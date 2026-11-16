import uuid
import shutil
import logging
import asyncio
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from config import settings
from models.schemas import JobStatus
from services.ingestion import ingestion_service, get_job_status, update_job_status

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Upload & Ingestion"])

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
MAX_UPLOAD_SIZE_MB = 500
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

@router.post("/upload", response_model=JobStatus)
async def upload_video(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    camera_id: str = Form("cam_gate_01")
):
    """
    Accepts video file (MP4/AVI/MOV), validates format, and starts the asynchronous
    extraction, temporal vision analysis, transcript synthesis, and vector persistence pipeline.
    """
    file_ext = Path(file.filename or "video.mp4").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validate file size by reading content length header or streaming check
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_UPLOAD_SIZE_MB}MB."
        )

    job_id = str(uuid.uuid4())
    save_path = settings.UPLOAD_DIR / f"{job_id}{file_ext}"

    try:
        # Stream file to disk with size enforcement
        total_written = 0
        with open(save_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)  # Read 1MB at a time
                if not chunk:
                    break
                total_written += len(chunk)
                if total_written > MAX_UPLOAD_SIZE_BYTES:
                    buffer.close()
                    save_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum allowed size is {MAX_UPLOAD_SIZE_MB}MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to save video upload to disk.")

    # Initialize job status in Redis / fallback store
    update_job_status(
        job_id=job_id,
        status="pending",
        message="Video received, scheduling pipeline..."
    )

    # Launch ingestion pipeline in background task
    background_tasks.add_task(
        ingestion_service.run_pipeline,
        job_id=job_id,
        video_path=str(save_path),
        camera_id=camera_id
    )

    return JobStatus(
        job_id=job_id,
        status="pending",
        message="Video upload complete. Pipeline started.",
        camera_id=camera_id
    )

@router.get("/job/{job_id}", response_model=JobStatus)
async def get_job_progress(job_id: str):
    """
    Returns real-time job processing progress (Gap 2 Fix).
    Transitions through: pending -> extracting -> analyzing -> synthesizing -> storing -> done (or failed).
    """
    data = get_job_status(job_id)
    return JobStatus(
        job_id=job_id,
        status=data.get("status", "pending"),
        message=data.get("message"),
        frame_count=data.get("frame_count", 0),
        analyzed_count=data.get("analyzed_count", 0),
        error=data.get("error")
    )
