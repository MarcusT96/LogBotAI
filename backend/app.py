#FastAPI app

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from agent import ask_question
from knowledge import ingest_multiple_documents, generate_session_id
import io
from fastapi.responses import StreamingResponse

# Add this class for responses that include session_id
class UploadResponse(BaseModel):
    files: List[dict]
    session_id: str

class QuestionRequest(BaseModel):
    message: str
    session_id: str

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload-documents", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)) -> UploadResponse:
    """
    Endpoint to upload and ingest multiple documents
    """
    try:
        # Generate new session ID for this upload
        session_id = generate_session_id()
        
        # Process each file
        file_objects = []
        
        for file in files:
            try:
                contents = await file.read()
                if len(contents) > MAX_FILE_SIZE:
                    raise HTTPException(status_code=413, detail="File too large")
                
                if not file.filename.endswith('.docx'):
                    raise HTTPException(status_code=415, detail="Only .docx files are allowed")
                
                file_obj = io.BytesIO(contents)
                file_obj.filename = file.filename
                file_obj.content_type = file.content_type
                file_objects.append(file_obj)
                
            except Exception as e:
                return UploadResponse(
                    files=[{
                        "status": "error",
                        "filename": file.filename,
                        "message": str(e)
                    }],
                    session_id=session_id
                )
        
        if file_objects:
            # Process all valid files with the session ID
            results = await ingest_multiple_documents(file_objects, session_id)
            return UploadResponse(files=results, session_id=session_id)
            
        return UploadResponse(files=[], session_id=session_id)
        
    except Exception as e:
        return UploadResponse(
            files=[{"status": "error", "message": str(e)}],
            session_id=session_id
        )

@app.post("/ask")
async def ask(question: QuestionRequest):
    """
    Endpoint to ask questions about the ingested documents
    """
    try:
        return StreamingResponse(
            ask_question(question.message, question.session_id),
            media_type="text/event-stream"
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import os
    from gunicorn.app.base import BaseApplication

    class StandaloneApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            config = {key: value for key, value in self.options.items()
                      if key in self.cfg.settings and value is not None}
            for key, value in config.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    options = {
        'bind': f"0.0.0.0:{os.environ.get('PORT', '8000')}",
        'workers': 4,
        'worker_class': 'uvicorn.workers.UvicornWorker',
    }
    StandaloneApplication(app, options).run()