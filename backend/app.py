#FastAPI app

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from agent import ask_question
from knowledge import ingest_multiple_documents
import io
from fastapi.responses import StreamingResponse
import asyncio

# Add this class for the request body
class QuestionRequest(BaseModel):
    message: str

# Add at the top
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React's default port
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/upload-documents")
async def upload_documents(files: List[UploadFile] = File(...)) -> List[dict[str, str]]:
    """
    Endpoint to upload and ingest multiple documents
    """
    try:
        # Process each file
        results = []
        file_objects = []  # List to store file objects with metadata
        
        for file in files:
            try:
                # Check file size
                contents = await file.read()
                if len(contents) > MAX_FILE_SIZE:
                    raise HTTPException(status_code=413, detail="File too large")
                
                # Check file type
                if not file.filename.endswith('.docx'):
                    raise HTTPException(status_code=415, detail="Only .docx files are allowed")
                
                # Create a BytesIO object with additional attributes
                file_obj = io.BytesIO(contents)
                file_obj.filename = file.filename  # Add filename attribute
                file_obj.content_type = file.content_type  # Add content_type attribute
                file_objects.append(file_obj)
                
            except Exception as e:
                results.append({
                    "status": "error",
                    "filename": file.filename,
                    "message": str(e)
                })
                continue
        
        if file_objects:
            # Process all valid files
            await ingest_multiple_documents(file_objects)
            for file_obj in file_objects:
                results.append({
                    "status": "success",
                    "filename": file_obj.filename,
                    "message": "File processed successfully"
                })
                
        return results
    except Exception as e:
        return [{"status": "error", "message": str(e)}]

@app.post("/ask")
async def ask(question: QuestionRequest):
    """
    Endpoint to ask questions about the ingested documents with streaming response
    """
    try:
        return StreamingResponse(
            ask_question(question.message),
            media_type="text/event-stream"
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}