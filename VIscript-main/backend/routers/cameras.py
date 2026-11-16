import logging
import time
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from db.supabase_client import supabase_client
from models.schemas import Camera
from services.stream_manager import stream_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Cameras & Streams"])

@router.get("/cameras", response_model=List[Camera])
async def list_cameras():
    """Lists all configured surveillance cameras."""
    cameras = await supabase_client.get_cameras()
    return cameras

@router.post("/cameras", response_model=Camera)
async def create_camera(camera_data: dict):
    """Registers a new surveillance camera and starts its live ingestion stream."""
    name = camera_data.get("name", "Camera 01")
    location = camera_data.get("location", "Main Entrance")
    rtsp_url = camera_data.get("stream_url") or camera_data.get("rtsp_url")
    camera_id = camera_data.get("id")
    cam = await supabase_client.insert_camera(name=name, location=location, rtsp_url=rtsp_url, camera_id=camera_id)
    if rtsp_url:
        await stream_manager.start_stream(cam["id"], rtsp_url, camera_name=name)
    return cam

@router.delete("/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    """Deletes a surveillance camera and terminates its stream session."""
    await stream_manager.stop_stream(camera_id)
    await supabase_client.delete_camera(camera_id)
    return {"status": "ok", "message": f"Camera {camera_id} removed successfully"}

@router.get("/cameras/{camera_id}/live")
async def live_camera_feed(camera_id: str):
    """Streams live MJPEG frames directly to the browser for RTSP/webcam feeds."""
    cameras = await supabase_client.get_cameras()
    cam = next((c for c in cameras if c.get("id") == camera_id), None)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    stream_url = cam.get("stream_url")
    if not stream_url:
        raise HTTPException(status_code=400, detail="This camera does not have an RTSP or live stream URL configured.")

    # Ensure stream session is started
    session = stream_manager.get_session(camera_id)
    if not session or not session.is_running:
        session = await stream_manager.start_stream(camera_id, stream_url, cam.get("name"))

    return StreamingResponse(
        session.generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.post("/cameras/{camera_id}/transcribe")
async def trigger_live_transcription(camera_id: str):
    """
    On-demand Vision AI analysis of the current live frame.
    Analyzes the active webcam/RTSP frame, logs the event, and triggers transcript synthesis.
    """
    cameras = await supabase_client.get_cameras()
    cam = next((c for c in cameras if c.get("id") == camera_id), None)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    stream_url = cam.get("stream_url")
    if not stream_url:
        raise HTTPException(status_code=400, detail="No stream URL configured for this camera.")

    session = stream_manager.get_session(camera_id)
    if not session or not session.is_running:
        session = await stream_manager.start_stream(camera_id, stream_url, cam.get("name"))
        # Brief warmup for first frame capture
        await stream_manager.start_stream(camera_id, stream_url, cam.get("name"))

    event = await session.capture_and_transcribe_sample()
    if not event:
        raise HTTPException(status_code=500, detail="Could not capture live frame for analysis. Please ensure camera is connected.")

    return {
        "status": "ok",
        "message": "Live frame captured and transcribed successfully.",
        "event": event.model_dump()
    }

@router.post("/cameras/{camera_id}/toggle-transcription")
async def toggle_continuous_transcription(camera_id: str, enabled: bool):
    """Toggles background continuous Vision AI transcription for a camera feed."""
    session = stream_manager.get_session(camera_id)
    if not session:
        raise HTTPException(status_code=404, detail="Stream session not found for this camera.")
    session.transcription_enabled = enabled
    return {
        "status": "ok",
        "camera_id": camera_id,
        "transcription_enabled": session.transcription_enabled
    }

@router.get("/cameras/health")
async def get_stream_health():
    """Returns RTSP live stream health metrics (reconnect counts, active status)."""
    return stream_manager.get_stream_health()

@router.post("/cameras/{camera_id}/stream")
async def start_camera_stream(camera_id: str, rtsp_url: str):
    """Initiates an active RTSP live stream worker for a camera."""
    await stream_manager.start_stream(camera_id, rtsp_url)
    return {"status": "ok", "message": f"RTSP stream session registered for {camera_id}"}
