import os
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
from azure.cosmos import CosmosClient
import numpy as np
import docx2txt
import io
import hashlib
from datetime import datetime
from typing import List
import uuid
import re

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
container = database.get_container_client("test")

embedding_model = AzureOpenAIEmbeddings(
    azure_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_EMBEDDING_API_VERSION
)

class ProtocolSplitter:
    def __init__(self):
        self.header_pattern = "MÖTESPROTOKOLL"
        self.section_patterns = [
            r"^\d+\.\s+[A-ZÅÄÖ]",  # Main numbered sections
            r"^[a-z]\)\s+",        # Sub-items
            r"^Närvarande:",       # Attendee section
            r"^Datum:",            # Date section
            r"^Plats:"            # Location section
        ]
    
    def split_text(self, text: str) -> List[dict]:
        chunks = []
        current_header = ""
        current_content = ""
        lines = text.split('\n')
        
        for line in lines:
            # Check if this line starts a new section
            is_new_section = any(re.match(pattern, line) for pattern in self.section_patterns)
            
            if is_new_section:
                # Save previous chunk if it exists and has content
                if current_header and current_content.strip():
                    chunks.append({
                        "content": f"{current_header}\n{current_content.strip()}",
                        "metadata": {
                            "section": current_header.split('.')[0] if '.' in current_header else current_header,
                            "type": "content"
                        }
                    })
                current_header = line
                current_content = ""
            else:
                # Add line to current content if we have a header
                if current_header:
                    current_content += "\n" + line
                else:
                    # If no header yet, this might be initial content (like meeting info)
                    current_content += line
        
        # Add the last chunk if it exists and has content
        if current_header and current_content.strip():
            chunks.append({
                "content": f"{current_header}\n{current_content.strip()}",
                "metadata": {
                    "section": current_header.split('.')[0] if '.' in current_header else current_header,
                    "type": "content"
                }
            })
        
        # Handle any initial content without a header (like meeting info)
        if not current_header and current_content.strip():
            chunks.append({
                "content": current_content.strip(),
                "metadata": {
                    "section": "Mötesinfo",
                    "type": "header"
                }
            })
        
        return chunks

async def ingest_single_document(file: io.BytesIO, session_id: str) -> dict:
    """
    Ingest a single DOCX document with protocol-specific chunking
    """
    try:
        # Process the BytesIO content with docx2txt
        text = docx2txt.process(file)
        
        # Use custom protocol splitter
        protocol_splitter = ProtocolSplitter()
        chunks = protocol_splitter.split_text(text)
        
        uploaded_chunks = []
        for chunk_index, chunk_data in enumerate(chunks):
            content = chunk_data["content"]
            content_hash = hashlib.md5(content.encode()).hexdigest()
            chunk_id = f"{session_id}_{content_hash}_{chunk_index}"
            
            # Generate embedding for the chunk
            embedding = embedding_model.embed_query(content)
            
            # Create document for Cosmos DB with enhanced metadata
            cosmos_doc = {
                "id": chunk_id,
                "content": content,
                "embedding": embedding,
                "session_id": session_id,
                "chunk_index": chunk_index,
                "total_chunks": len(chunks),
                "metadata": {
                    "source_file": file.filename,
                    "timestamp": datetime.now().isoformat(),
                    "hash": content_hash,
                    "creation_date": datetime.now().isoformat(),
                    "section": chunk_data["metadata"]["section"],
                    "type": chunk_data["metadata"]["type"]
                }
            }
            
            container.upsert_item(cosmos_doc)
            uploaded_chunks.append(chunk_id)


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

async def find_similar_documents(query: str, session_id: str, top_k: int = 20):
    """
    Find similar documents using cosine similarity
    """
    try:
        query_embedding = embedding_model.embed_query(query)
        
        # Retrieve documents for this session
        items = list(container.query_items(
            query="SELECT c.content, c.metadata, c.embedding FROM c WHERE c.session_id = @session_id",
            parameters=[{"name": "@session_id", "value": session_id}],
            enable_cross_partition_query=True
        ))
        
        # Calculate similarities and format results
        similarities = []
        for item in items:
            doc_embedding = item['embedding']
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )
            
            formatted_content = f"""
<document source="{item['metadata']['source_file']}">
{item['content']}
</document>"""
            
            similarities.append({
                "content": formatted_content,
                "source": item['metadata']['source_file'],
                "similarity_score": similarity
            })
        
        # Sort by similarity score and get top k results
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_results = similarities[:top_k]
        

        return [{"content": r["content"], "source": r["source"]} for r in top_results]
            
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
