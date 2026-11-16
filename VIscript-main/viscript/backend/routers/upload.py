from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from models.schemas import UploadResponse, JobStatus
from services.ingestion import extract_frames, analyze_video, redis_client
import shutil
import os
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    camera_id: str = Form(...) 
):
    # Validate extension
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Filename missing")
        
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".mp4", ".avi", ".mov"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only MP4, AVI, MOV allowed.")
    
    job_id = str(uuid.uuid4())
    logger.info(f"Starting upload job {job_id} for file {filename}")
    
    # Save file
    if os.name == 'nt':
        upload_dir = os.path.join(os.getcwd(), "tmp", "uploads")
    else:
        upload_dir = "/tmp/uploads"
        
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{job_id}{ext}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Update status
        redis_client.set(f"job:{job_id}", "extracting")
        
        # Extract frames (Synchronous blocking for count)
        frames = extract_frames(file_path, job_id)
        
        # Update status
        redis_client.set(f"job:{job_id}", "extracting") # Keeping extracting till task picks up or analyzing?
        # Task A3 says: "Set job status ... value = 'extracting'". The response says "status: 'processing'".
        # I'll update it to 'processing' just before returning or let task update it.
        # Task A4 says "extracting -> analyzing -> synthesizing".
        # If extraction is done here, next state is analyzing (queued).
        redis_client.set(f"job:{job_id}", "processing")
        
        # Enqueue task
        analyze_video.delay(job_id, frames, camera_id)
        
        return UploadResponse(job_id=job_id, status="processing", frame_count=len(frames))
        
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        redis_client.set(f"job:{job_id}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    status = redis_client.get(f"job:{job_id}")
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return JobStatus(job_id=job_id, status=str(status))
