#FastAPI app

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from agent import ingest_multiple_documents, ask_question

# Add this class for the request body
class QuestionRequest(BaseModel):
    message: str

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
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Endpoint to upload and ingest multiple documents
    """
    results = await ingest_multiple_documents(files)
    return results

@app.post("/ask")
async def ask(question: QuestionRequest):
    """
    Endpoint to ask questions about the ingested documents
    """
    try:
        answer = ask_question(question.message)  # Use question.message instead of question
        return {"status": "success", "answer": answer}
    except Exception as e:
        return {"status": "error", "message": str(e)}