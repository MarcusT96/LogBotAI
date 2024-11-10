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


# Session TTL in hours
SESSION_TTL = 2

async def ingest_single_document(file: io.BytesIO, session_id: str) -> dict:
    """
    Ingest a single DOCX document with session tracking
    """
    try:
        # Process the BytesIO content with docx2txt
        text = docx2txt.process(file)
        
        # Create a unique ID based on session and content hash only
        content_hash = hashlib.md5(text.encode()).hexdigest()
        doc_id = f"{session_id}_{content_hash}"
        
        # Generate embedding for the text
        embedding = embedding_model.embed_query(text)
        
        # Create document for Cosmos DB with session info
        cosmos_doc = {
            "id": doc_id,
            "content": text,
            "embedding": embedding,
            "session_id": session_id,
            "filename": file.filename,
            "expires_at": (datetime.now() + timedelta(hours=SESSION_TTL)).isoformat(),
            "metadata": {
                "source": file.filename,
                "timestamp": datetime.now().isoformat(),
                "hash": content_hash
            }
        }
        
        # Upsert the document to Cosmos DB
        container.upsert_item(cosmos_doc)
        print(f"Document upserted successfully with ID: {doc_id}")

        return {
            "status": "success",
            "filename": file.filename,
            "message": "Document successfully upserted",
            "doc_id": doc_id
        }
        
    except Exception as e:
        print(f"Error during document processing: {str(e)}")
        return {
            "status": "error",
            "filename": getattr(file, 'filename', 'unknown'),
            "message": str(e)
        }

async def find_similar_documents(query: str, session_id: str, top_k: int = 3):
    """
    Find similar documents for specific session
    """
    try:
        query_embedding = embedding_model.embed_query(query)
        
        # Query documents for this session that haven't expired
        query = """
        SELECT * FROM c 
        WHERE c.session_id = @session_id 
        AND c.expires_at > @current_time
        """
        parameters = [
            {"name": "@session_id", "value": session_id},
            {"name": "@current_time", "value": datetime.now().isoformat()}
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
            similarities.append((item, similarity))
        
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

if __name__ == "__main__":
    import asyncio
    
    async def test_vector_store():
        print("\n=== Testing Vector Store Operations ===\n")
        
        # Generate a test session
        session_id = generate_session_id()
        print(f"Created test session ID: {session_id}")
        
        try:
            # Path to your document
            file_path = "backend/Motesprotokoll_Miljo_Samhallsbyggnad_2024-03-05.docx"
            
            # Read the actual document
            with open(file_path, 'rb') as doc_file:
                content = doc_file.read()
                
            # Create BytesIO object
            file_obj = io.BytesIO(content)
            file_obj.filename = "Motesprotokoll_Miljo_Samhallsbyggnad_2024-03-05.docx"
            
            # Test container creation and document ingestion
            print("\nTesting document ingestion...")
            result = await ingest_single_document(file_obj, session_id)
            print(f"Ingestion result: {result}")
            
            # Test similarity search
            test_query = "Vilka beslut togs under mötet den 5 mars 2024?"
            print(f"\nTesting similarity search with query: '{test_query}'")
            similar_docs = await find_similar_documents(test_query, session_id)
            print(f"Found {len(similar_docs)} similar documents")
            for i, doc in enumerate(similar_docs, 1):
                print(f"\nDocument {i}:")
                print(f"ID: {doc['id']}")
                print(f"Content preview: {doc['content'][:200]}...")
            
            print(f"\nTest complete. Container 'session_{session_id}' will be deleted after {SESSION_TTL} hours")
            
        except FileNotFoundError:
            print(f"Error: Could not find file {file_path}")
        except Exception as e:
            print(f"Error during test: {str(e)}")
        
        print("\n=== Test Completed ===")
    
    # Run the test
    asyncio.run(test_vector_store())