import os
import glob
import subprocess
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis Connection Stub
redis_client = type('MockRedis', (object,), {
    'set': lambda self, k, v: logger.info(f"MockRedis SET {k}={v}"),
    'get': lambda self, k: None
})()

# Celery App Stub
class MockCelery:
    def task(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def conf(self): pass
    update = lambda self, *args, **kwargs: None

celery_app = MockCelery()

def extract_frames(video_path: str, job_id: str) -> list[str]:
    """
    Runs FFmpeg to extract 1 frame every 5 seconds.
    Returns list of absolute file paths to extracted images.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # backend/
    frames_dir = os.path.join(base_dir, "frames", job_id)
    os.makedirs(frames_dir, exist_ok=True)
    
    output_pattern = os.path.join(frames_dir, "frame_%04d.jpg")
    
    cmd = [
        "ffmpeg", "-y", 
        "-i", video_path,
        "-vf", "fps=0.2",
        "-q:v", "2", 
        output_pattern
    ]
    
    logger.info(f"Extracting frames for job {job_id} from {video_path}")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed: {e.stderr}")
        raise RuntimeError("Frame extraction failed")
        
    frames = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))
    logger.info(f"Extracted {len(frames)} frames for job {job_id}")
    return frames

@celery_app.task(name="analyze_video")
def analyze_video(job_id: str, frame_paths: list[str], camera_id: str):
    """
    Celery task stubbed to run the AI pipeline synchronously or just log.
    """
    import asyncio
    from datetime import datetime, timedelta

    async def run_pipeline():
        try:
            logger.info(f"STUB: Starting analysis for job {job_id} with {len(frame_paths)} frames")
            redis_client.set(f"job:{job_id}", "done")
            logger.info(f"Job {job_id} completed (STUBBED)")
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            redis_client.set(f"job:{job_id}", "error")

    try:
        asyncio.run(run_pipeline())
    except Exception as e:
        logger.error(f"Asyncio run failed: {e}")
        redis_client.set(f"job:{job_id}", "error")
