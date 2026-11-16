import os
import json
import uuid
import time
import shutil
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import settings
from models.schemas import JobStatus, FrameEvent
from db.supabase_client import supabase_client
from db.chromadb_client import chromadb_client
from services.analyzer import frame_analyzer
from services.synthesizer import transcript_synthesizer

logger = logging.getLogger(__name__)

# Real Redis Connection with In-Memory Defensive Fallback (Gap 2 Fix)
redis_client = None
_in_memory_jobs: Dict[str, Dict[str, Any]] = {}

if settings.REDIS_URL:
    try:
        import redis
        client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.ping()
        redis_client = client
        logger.info(f"Connected to Redis at {settings.REDIS_URL}")
    except Exception as e:
        logger.warning(f"Redis unavailable ({e}). Using in-memory job status store.")
        redis_client = None
else:
    logger.info("REDIS_URL not configured. Using in-memory job status store.")

def update_job_status(
    job_id: str, 
    status: str, 
    message: Optional[str] = None, 
    frame_count: int = 0, 
    analyzed_count: int = 0,
    error: Optional[str] = None
):
    """Store job status in Redis (with 1h TTL) or in-memory fallback."""
    job_data = {
        "job_id": job_id,
        "status": status,
        "message": message,
        "frame_count": frame_count,
        "analyzed_count": analyzed_count,
        "error": error,
        "updated_at": time.time()
    }
    
    # Always keep in memory store as fallback
    _in_memory_jobs[job_id] = job_data

    if redis_client:
        try:
            redis_client.set(f"job:{job_id}", json.dumps(job_data), ex=3600)
        except Exception as e:
            logger.warning(f"Failed to write job status to Redis: {e}")

def get_job_status(job_id: str) -> Dict[str, Any]:
    """Retrieve job status from Redis or in-memory fallback."""
    if redis_client:
        try:
            val = redis_client.get(f"job:{job_id}")
            if val:
                return json.loads(val)
        except Exception as e:
            logger.warning(f"Failed to read job status from Redis: {e}")
            
    # Check in-memory store
    if job_id in _in_memory_jobs:
        return _in_memory_jobs[job_id]
        
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Job queued for processing",
        "frame_count": 0,
        "analyzed_count": 0
    }


class IngestionService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.frames_dir = settings.FRAMES_DIR

    def extract_motion_burst_frames(self, video_path: str, output_dir: Path) -> List[str]:
        """
        Improvement 3: Motion-Burst Frame Extraction.
        Extracts uniform sample frames (1 per 5 sec) AND detects moments of high pixel change
        to inject burst frames where rapid activity occurs.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        frame_paths: List[str] = []

        try:
            import cv2
            import numpy as np

            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            sample_interval = max(1, int(fps / settings.FRAME_SAMPLE_FPS))  # Default 1 frame per 5 seconds

            current_frame_idx = 0
            prev_gray = None
            burst_count = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # 1. Uniform interval sampling
                is_uniform_sample = (current_frame_idx % sample_interval == 0)
                is_motion_burst = False

                # 2. Motion burst check
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if prev_gray is not None and burst_count < settings.MAX_BURST_FRAMES:
                    # Compute mean absolute pixel difference
                    diff = np.mean(np.abs(gray.astype(float) - prev_gray)) / 255.0
                    if diff > settings.MOTION_THRESHOLD:
                        is_motion_burst = True
                        burst_count += 1
                        logger.info(f"Motion burst detected at frame {current_frame_idx} (diff={diff:.3f})")

                if is_uniform_sample or is_motion_burst:
                    sec = int(current_frame_idx / fps)
                    hrs, mins, secs = sec // 3600, (sec % 3600) // 60, sec % 60
                    time_tag = f"{hrs:02d}_{mins:02d}_{secs:02d}"
                    tag = "burst" if is_motion_burst else "sample"
                    
                    frame_filename = f"frame_{current_frame_idx:05d}_{tag}_{time_tag}.jpg"
                    frame_path = str(output_dir / frame_filename)
                    cv2.imwrite(frame_path, frame)
                    frame_paths.append(frame_path)

                prev_gray = gray
                current_frame_idx += 1

            cap.release()
            logger.info(f"Extracted {len(frame_paths)} total frames ({burst_count} motion burst frames).")

        except Exception as e:
            logger.error(f"OpenCV frame extraction failed for {video_path}: {e}")
            raise RuntimeError(
                f"Video decoding failed: {e}. Please ensure OpenCV is installed and the uploaded file is a valid video (MP4/AVI/MKV)."
            )

        return frame_paths

    async def run_pipeline(self, job_id: str, video_path: str, camera_id: str = "cam_gate_01"):
        """Full end-to-end ingestion pipeline."""
        output_dir = self.frames_dir / job_id
        try:
            logger.info(f"Starting ingestion pipeline for job {job_id}")
            update_job_status(job_id, "extracting", "Extracting frames and motion-burst events...")

            # 1. Extraction (Uniform + Motion Burst)
            loop = asyncio.get_running_loop()
            frames = await loop.run_in_executor(
                None, self.extract_motion_burst_frames, video_path, output_dir
            )

            if not frames:
                raise ValueError("No frames could be extracted from video.")

            total_frames = len(frames)
            update_job_status(
                job_id, "analyzing", 
                f"Analyzing {total_frames} frames with Vision AI...", 
                frame_count=total_frames
            )

            # 2. Vision AI Analysis (with Temporal Context)
            events: List[FrameEvent] = await frame_analyzer.analyze_batch(frames, camera_id=camera_id)
            
            update_job_status(
                job_id, "synthesizing", 
                "Synthesizing timestamped surveillance transcript...", 
                frame_count=total_frames, 
                analyzed_count=len(events)
            )

            # 3. Transcript Synthesis
            period_start = events[0].time if events else "10:00:00"
            period_end = events[-1].time if events else "10:30:00"
            
            # Dynamically determine or register camera
            existing_cams = await supabase_client.get_cameras()
            cam_obj = next((c for c in existing_cams if c.get("id") == camera_id), None)
            if not cam_obj:
                cam_name = camera_id.replace("_", " ").title()
                cam_obj = await supabase_client.insert_camera(name=cam_name, location="Monitored Area", camera_id=camera_id)
            camera_name = cam_obj.get("name", camera_id)
            
            narrative = await transcript_synthesizer.synthesize_transcript(
                events=events,
                period=f"{period_start} - {period_end}",
                camera_name=camera_name
            )

            # 4. Storage & Defensive Persistence
            update_job_status(
                job_id, "storing", 
                "Persisting events and indexing vector chunks...", 
                frame_count=total_frames, 
                analyzed_count=len(events)
            )

            # Save events to database
            for event in events:
                await supabase_client.insert_event(event, camera_id=camera_id)

            # Save transcript
            transcript_id = await supabase_client.insert_transcript(
                camera_id=camera_id,
                period_start=period_start,
                period_end=period_end,
                narrative=narrative,
                event_count=len(events),
                events=[e.model_dump() for e in events]
            )

            # Index in ChromaDB
            metadata = {
                "transcript_id": transcript_id,
                "camera_id": camera_id,
                "period": f"{period_start} - {period_end}",
                "job_id": job_id
            }
            await chromadb_client.store_transcript_chunk(
                text=narrative,
                metadata=metadata,
                chunk_id=f"chunk_{transcript_id}"
            )

            # 5. Done
            update_job_status(
                job_id, "done", 
                "Processing complete. Transcript generated successfully.", 
                frame_count=total_frames, 
                analyzed_count=len(events)
            )
            logger.info(f"Pipeline completed successfully for job {job_id}")

        except Exception as e:
            logger.exception(f"Pipeline error on job {job_id}: {e}")
            update_job_status(job_id, "failed", f"Pipeline failed: {str(e)}", error=str(e))
        finally:
            # Clean up raw frames (Privacy DPDP compliance)
            try:
                if output_dir.exists():
                    shutil.rmtree(output_dir, ignore_errors=True)
            except Exception as ce:
                logger.warning(f"Could not remove frame dir: {ce}")
            # Clean up original uploaded video file to prevent disk exhaustion
            try:
                video_file = Path(video_path)
                if video_file.exists():
                    video_file.unlink()
                    logger.info(f"Cleaned up uploaded video: {video_path}")
            except Exception as ve:
                logger.warning(f"Could not remove uploaded video: {ve}")

ingestion_service = IngestionService()
