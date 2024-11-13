import os
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
from azure.cosmos import CosmosClient
import numpy as np
import docx2txt
import io
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional
import uuid
from langchain_experimental.text_splitter import SemanticChunker

load_dotenv()

# Azure OpenAI settings for embeddings
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_EMBEDDING_ENDPOINT = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
AZURE_EMBEDDING_API_VERSION = os.getenv("AZURE_EMBEDDING_API_VERSION")

# Cosmos DB settings
COSMOS_ENDPOINT = os.getenv("COSMOS_DB_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_DB_KEY")

# Initialize Cosmos DB client
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.get_database_client("logbotai")
container = database.get_container_client("test")  # Use existing 'test' container

embedding_model = AzureOpenAIEmbeddings(
    azure_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_EMBEDDING_API_VERSION
)


async def ingest_single_document(file: io.BytesIO, session_id: str) -> dict:
    """
    Ingest a single DOCX document with session tracking and semantic chunking
    """
    try:
        # Process the BytesIO content with docx2txt
        text = docx2txt.process(file)
        
        # Initialize semantic chunker
        s_splitter = SemanticChunker(
            embeddings=embedding_model
        )
        
        # Split text into semantic chunks
        chunks = s_splitter.split_text(text)
        
        uploaded_chunks = []
        for chunk_index, chunk in enumerate(chunks):
            # Create a unique ID for each chunk
            content_hash = hashlib.md5(chunk.encode()).hexdigest()
            chunk_id = f"{session_id}_{content_hash}_{chunk_index}"
            
            # Generate embedding for the chunk
            embedding = embedding_model.embed_query(chunk)
            
            # Create document for Cosmos DB with enhanced metadata
            cosmos_doc = {
                "id": chunk_id,
                "content": chunk,
                "embedding": embedding,
                "session_id": session_id,
                "chunk_index": chunk_index,
                "total_chunks": len(chunks),
                "metadata": {
                    "source_file": file.filename,
                    "timestamp": datetime.now().isoformat(),
                    "hash": content_hash,
                    "creation_date": datetime.now().isoformat()
                }
            }
            
            # Upsert the chunk to Cosmos DB
            container.upsert_item(cosmos_doc)
            uploaded_chunks.append(chunk_id)
            
        print(f"Document chunked and upserted successfully with {len(chunks)} chunks")

        return {
            "status": "success",
            "filename": file.filename,
            "message": f"Document successfully split into {len(chunks)} chunks and upserted",
            "chunk_ids": uploaded_chunks
        }
        
    except Exception as e:
        print(f"Error during document processing: {str(e)}")
        return {
            "status": "error",
            "filename": getattr(file, 'filename', 'unknown'),
            "message": str(e)
        }

async def find_similar_documents(query: str, session_id: str, top_k: int = 10, similarity_threshold: float = 0.4):
    """
    Find similar documents using a multi-stage retrieval process:
    1. Initial similarity search
    2. MMR for diversity
    3. Reranking of top results
    """
    try:
        query_embedding = embedding_model.embed_query(query)
        
        # Initial retrieval
        items = list(container.query_items(
            query="SELECT c.content, c.metadata, c.embedding FROM c WHERE c.session_id = @session_id",
            parameters=[{"name": "@session_id", "value": session_id}],
            enable_cross_partition_query=True
        ))
        
        # Calculate initial similarities
        initial_results = []
        doc_embeddings = []
        doc_contents = []
        
        for item in items:
            doc_embedding = item['embedding']
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )
            
            if similarity >= similarity_threshold:
                formatted_content = f"""
<document source="{item['metadata']['source_file']}">
{item['content']}
</document>"""
                
                initial_results.append({
                    "content": formatted_content,
                    "source": item['metadata']['source_file'],
                    "similarity_score": similarity
                })
                doc_embeddings.append(doc_embedding)
                doc_contents.append(formatted_content)
        
        # Apply MMR for diversity
        if doc_embeddings:
            diverse_contents = mmr(
                query_embedding=query_embedding,
                doc_embeddings=doc_embeddings,
                doc_contents=doc_contents,
                lambda_param=0.7,  # Balance between relevance and diversity
                k=min(len(doc_contents), top_k)
            )
            
            # Create results list from diverse contents
            diverse_results = [
                {"content": content, "source": content.split('source="')[1].split('">')[0]}
                for content in diverse_contents
            ]
            
            # Rerank the diverse results
            final_results = await rerank_results(query, diverse_results, rerank_k=7)
            
            print(f"Found {len(final_results)} documents after reranking")
            return final_results
            
        return []
    
    except Exception as e:
        print(f"Error finding similar documents: {str(e)}")
        raise e

def generate_session_id() -> str:
    """
    Generate a unique session ID
    """
    return str(uuid.uuid4())

async def ingest_multiple_documents(files: List[io.BytesIO], session_id: str) -> List[dict]:
    """
    Ingest multiple DOCX documents for a specific session.
    """
    results = []
    for file in files:
        try:
            if not hasattr(file, 'filename') or not file.filename.endswith('.docx'):
                results.append({
                    "status": "error",
                    "filename": getattr(file, 'filename', 'unknown'),
                    "message": "Only DOCX files are supported"
                })
                continue
                
            result = await ingest_single_document(file, session_id)
            results.append(result)
            
        except Exception as e:
            results.append({
                "status": "error",
                "filename": getattr(file, 'filename', 'unknown'),
                "message": str(e)
            })
    
    return results

def mmr(query_embedding, doc_embeddings, doc_contents, lambda_param=0.5, k=5):
    """
    Maximal Marginal Relevance to get diverse but relevant results
    """
    selected_indices = []
    remaining_indices = list(range(len(doc_embeddings)))
    
    for _ in range(k):
        if not remaining_indices:
            break
            
        # Calculate relevance scores
        relevance_scores = [
            np.dot(query_embedding, doc_embeddings[idx]) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embeddings[idx])
            )
            for idx in remaining_indices
        ]
        
        if not selected_indices:
            # First selection based on relevance only
            selected_idx = remaining_indices[np.argmax(relevance_scores)]
        else:
            # Calculate diversity penalty
            diversity_scores = [
                max([
                    np.dot(doc_embeddings[idx], doc_embeddings[selected]) / (
                        np.linalg.norm(doc_embeddings[idx]) * np.linalg.norm(doc_embeddings[selected])
                    )
                    for selected in selected_indices
                ])
                for idx in remaining_indices
            ]
            
            # Combined score with MMR formula
            mmr_scores = [
                lambda_param * rel_score - (1 - lambda_param) * div_score
                for rel_score, div_score in zip(relevance_scores, diversity_scores)
            ]
            
            selected_idx = remaining_indices[np.argmax(mmr_scores)]
            
        selected_indices.append(selected_idx)
        remaining_indices.remove(selected_idx)
    
    return [doc_contents[idx] for idx in selected_indices]

async def rerank_results(query: str, initial_results: List[dict], rerank_k: int = 3):
    """
    Re-rank top results using more expensive but accurate semantic similarity
    """
    if len(initial_results) <= rerank_k:
        return initial_results
        
    # Get more detailed embeddings for reranking
    rerank_embeddings = embedding_model.embed_documents([r['content'] for r in initial_results[:rerank_k]])
    query_embedding = embedding_model.embed_query(query)
    
    # Calculate semantic similarity scores
    reranked_results = []
    for idx, result in enumerate(initial_results[:rerank_k]):
        semantic_score = np.dot(query_embedding, rerank_embeddings[idx])
        reranked_results.append((result, semantic_score))
    
    # Sort by new scores
    reranked_results.sort(key=lambda x: x[1], reverse=True)
    
    # Return reranked results plus any remaining results
    return [r[0] for r in reranked_results] + initial_results[rerank_k:]
