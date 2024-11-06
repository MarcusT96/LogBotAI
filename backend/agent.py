import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_astradb import AstraDBVectorStore
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
import docx2txt

from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
import glob
import re

from langchain_core.documents import Document
from datetime import datetime

from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter

from fastapi import UploadFile

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_EMBEDDING_ENDPOINT = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
AZURE_EMBEDDING_API_VERSION = os.getenv("AZURE_EMBEDDING_API_VERSION")

ASTRA_DB_ENDPOINT = os.getenv("ASTRA_DB_ENDPOINT")
ASTRA_DB_TOKEN = os.getenv("ASTRA_DB_TOKEN")

model = AzureChatOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    deployment_name="MecklyGPT4oMini",
    temperature=0.5,
    streaming=True
)

embedding_model = AzureOpenAIEmbeddings(
    azure_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_EMBEDDING_API_VERSION
)

vectorstore = AstraDBVectorStore(
    token=ASTRA_DB_TOKEN, 
    api_endpoint=ASTRA_DB_ENDPOINT, 
    collection_name="LogBotAI", 
    embedding=embedding_model,
    namespace="default_keyspace"
)

retriever = vectorstore.as_retriever()

async def ingest_single_document(file: UploadFile) -> dict:
    """
    Ingest a single DOCX document from an uploaded file into the vector store.
    
    Args:
        file (UploadFile): The uploaded file object from FastAPI
    
    Returns:
        dict: Status of the ingestion
    """
    try:
        # Read the content of the uploaded file
        content = await file.read()
        
        # Convert bytes to text using docx2txt
        text = docx2txt.process(content)
        
        # Create a single document with metadata
        document = Document(
            page_content=text,
            metadata={
                "source": file.filename
            }
        )
        
        # Store in vector database
        vectorstore.add_documents(documents=[document])

        return {
            "status": "success",
            "filename": file.filename,
            "message": "Document successfully ingested"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "filename": file.filename,
            "message": str(e)
        }

async def ingest_multiple_documents(files: List[UploadFile]) -> List[dict]:
    """
    Ingest multiple DOCX documents from uploaded files.
    
    Args:
        files (List[UploadFile]): List of uploaded file objects
    
    Returns:
        List[dict]: Status of each file's ingestion
    """
    results = []
    
    for file in files:
        if not file.filename.endswith('.docx'):
            results.append({
                "status": "error",
                "filename": file.filename,
                "message": "Only DOCX files are supported"
            })
            continue
            
        result = await ingest_single_document(file)
        results.append(result)
    
    return results

prompt = PromptTemplate.from_template("""
You are LogBot, an AI assistant that answers questions based on the provided context from meeting protocols and documents.

Context from relevant documents:
{context}

Question: {input}

Please provide a clear and concise answer based on the context provided. If the context doesn't contain relevant information to answer the question, please say so.
Speak Swedish.
Answer:""")

# Create the retrieval chain
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Build the RAG chain
rag_chain = (
    {
        "context": retriever | format_docs,
        "input": RunnablePassthrough()
    }
    | prompt 
    | model 
    | StrOutputParser()
)

# Example usage function
def ask_question(question: str) -> str:
    """
    Ask a question and get a response based on the retrieved documents.
    
    Args:
        question (str): The question to ask
    
    Returns:
        str: The response from the model
    """
    response = rag_chain.invoke(question)
    return response

# Example usage:
if __name__ == "__main__":
    # For ingesting documents:
    # ingest_multiple_documents("./documents")
    
    # For asking questions:
    question = "Vilka beslut togs i mötet den 5 mars 2024?"
    answer = ask_question(question)
    print("\nQuestion:", question)
    print("\nAnswer:", answer)

