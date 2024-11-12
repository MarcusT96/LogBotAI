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

async def find_similar_documents(query: str, session_id: str, top_k: int = 5) -> List[dict]:
    """
    Find similar documents for specific session, returning content with source metadata
    """
    try:
        query_embedding = embedding_model.embed_query(query)
        
        # Query documents for this session
        query = """
        SELECT c.content, c.metadata, c.embedding
        FROM c 
        WHERE c.session_id = @session_id
        """
        parameters = [
            {"name": "@session_id", "value": session_id}
        ]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        # Calculate cosine similarity
        similarities = []
        for item in items:
            doc_embedding = item['embedding']
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )
            
            # Format the content with source metadata
            formatted_content = f"""
<document source="{item['metadata']['source_file']}">
{item['content']}
</document>"""
            
            # Create a result object with formatted content
            result = {
                "content": formatted_content,
                "source": item['metadata']['source_file']
            }
            similarities.append((result, similarity))
        
        # Sort by similarity and get top_k results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in similarities[:top_k]]
    
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
