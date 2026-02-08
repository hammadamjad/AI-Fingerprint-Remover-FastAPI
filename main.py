import os
import shutil
import uuid
import logging
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the existing processing logic
# Assuming integrated_system.py is in the same directory or python path
from integrated_system import IntegratedWatermarkRemover

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Audio Fingerprint Remover API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
UPLOAD_DIR = Path("temp_uploads")
OUTPUT_DIR = Path("temp_outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Global progress store: {request_id: {"progress": float, "status": str, "output_path": str, "input_path": str}}
processing_progress: Dict[str, Dict[str, Any]] = {}

class ProcessingOptions(BaseModel):
    level: str = "balanced"
    enable_advanced_detection: bool = True
    enable_performance_optimization: bool = True
    generate_report: bool = False

def cleanup_files(file_paths: list[Path], request_id: Optional[str] = None):
    """Background task to remove temporary files and progress data."""
    # Note: We now keep output files until downloaded or timed out.
    # This function will be called AFTER download.
    for path in file_paths:
        try:
            if path.exists():
                if path.is_file():
                    os.remove(path)
                elif path.is_dir():
                    shutil.rmtree(path)
                logger.info(f"Cleaned up file: {path}")
        except Exception as e:
            logger.error(f"Error cleaning up {path}: {e}")
            
    # Clean up progress data
    if request_id and request_id in processing_progress:
        del processing_progress[request_id]
        logger.info(f"Cleaned up progress data for {request_id}")

def run_processing_task(request_id: str, input_path: Path, output_path: Path, level: str):
    """Background worker for audio processing."""
    try:
        processing_progress[request_id]["status"] = "Initializing processor..."
        system = IntegratedWatermarkRemover()
        
        # Define progress callback
        def progress_callback(progress: float, status: str):
            if request_id in processing_progress:
                processing_progress[request_id].update({
                    "progress": float(progress) * 100,
                    "status": status
                })
                # Log significant updates
                if int(progress * 100) % 10 == 0:
                    logger.info(f"Progress {request_id}: {progress:.0%} - {status}")
        
        # Process File
        stats = system.process_file(
            input_path=str(input_path),
            output_path=str(output_path),
            processing_level=level,
            enable_advanced_detection=True, 
            enable_performance_optimization=True,
            generate_report=False,
            progress_callback=progress_callback
        )
        
        logger.info(f"Processing complete for {request_id}. Stats: {stats}")
        
        if not output_path.exists():
            raise RuntimeError("Output file was not created by the processor")
            
        processing_progress[request_id].update({
            "progress": 100.0,
            "status": "Completed",
            "output_path": str(output_path)
        })

    except Exception as e:
        logger.error(f"Error in background task {request_id}: {e}")
        if request_id in processing_progress:
            processing_progress[request_id].update({
                "progress": 0.0,
                "status": f"Error: {str(e)}",
                "failed": True
            })
        # Clean up input if it failed early
        if input_path.exists():
            try: os.remove(input_path)
            except: pass

@app.get("/progress/{request_id}")
async def get_progress(request_id: str):
    """Get the current processing progress for a given request ID."""
    if request_id not in processing_progress:
        raise HTTPException(status_code=404, detail="Request ID not found or processing expired")
    
    # Return a copy to avoid mutation issues during serialization
    return dict(processing_progress[request_id])

@app.get("/download/{request_id}")
async def download_result(request_id: str, background_tasks: BackgroundTasks):
    """Download the processed file and schedule cleanup."""
    if request_id not in processing_progress:
        raise HTTPException(status_code=404, detail="Request ID not found")
        
    task_data = processing_progress[request_id]
    
    if task_data.get("failed"):
        raise HTTPException(status_code=500, detail=task_data.get("status"))
        
    if task_data.get("progress") < 100:
        raise HTTPException(status_code=400, detail="Processing not yet complete")
        
    output_path = Path(task_data["output_path"])
    input_path = Path(task_data["input_path"])
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Processed file missing from server")

    # Schedule cleanup AFTER the response is sent
    background_tasks.add_task(cleanup_files, [input_path, output_path], request_id)
    
    return FileResponse(
        path=output_path, 
        filename=f"processed_{request_id}{output_path.suffix}",
        media_type="application/octet-stream"
    )

@app.post("/process")
async def process_audio(
    file: UploadFile = File(...),
    level: str = Form("balanced"),
    aggressive_mode: bool = Form(False),
    request_id: str = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Initiate audio processing in the background and return a request ID immediately.
    """
    
    # 1. Validation
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".wav", ".mp3", ".flac", ".aiff", ".m4a"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {file_ext}")

    # Generate unique IDs for this request if not provided
    if not request_id:
        request_id = str(uuid.uuid4())
    
    logger.info(f"Received process request: {request_id}")
    
    # Initialize progress
    processing_progress[request_id] = {
        "progress": 0.0, 
        "status": "Uploading...",
        "input_path": "",
        "output_path": ""
    }

    input_filename = f"{request_id}_input{file_ext}"
    output_filename = f"{request_id}_output{file_ext}"
    
    input_path = UPLOAD_DIR / input_filename
    output_path = OUTPUT_DIR / output_filename
    
    try:
        # 2. Save Uploaded File
        processing_progress[request_id]["status"] = "Saving uploaded file..."
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        processing_progress[request_id].update({
            "input_path": str(input_path),
            "output_path": str(output_path),
            "status": "Queued for processing"
        })
            
        logger.info(f"File uploaded and queued: {input_path}")

        # 3. Start Background Task
        background_tasks.add_task(run_processing_task, request_id, input_path, output_path, level)
        
        return {"request_id": request_id, "status": "Processing started"}

    except Exception as e:
        logger.error(f"Error initiating process: {e}")
        if request_id in processing_progress:
            del processing_progress[request_id]
        if input_path.exists():
             os.remove(input_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "AI Audio Fingerprint Remover API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
