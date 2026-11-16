import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from db.supabase_client import supabase_client
from models.schemas import Transcript, FrameEvent

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Transcripts & Events"])

@router.get("/transcripts", response_model=List[Transcript])
async def get_transcripts(
    camera_id: Optional[str] = Query(None, description="Optional camera ID filter (Gap 3 Fix)"),
    limit: int = Query(50, ge=1, le=200, description="Max number of transcripts to return")
):
    """
    Returns transcripts ordered by timestamp.
    Accepts optional camera_id filter (Gap 3 Fix: frontend camera dropdown filtering works seamlessly).
    """
    transcripts = await supabase_client.get_transcripts(camera_id=camera_id, limit=limit)
    return transcripts

@router.get("/transcripts/{transcript_id}", response_model=Transcript)
async def get_transcript_details(transcript_id: str):
    """Returns a single transcript by ID with all associated frame events."""
    transcript = await supabase_client.get_transcript_by_id(transcript_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return transcript

@router.get("/events", response_model=List[Dict[str, Any]])
async def get_all_events(
    camera_id: Optional[str] = Query(None, description="Optional camera ID filter"),
    limit: int = Query(100, ge=1, le=500)
):
    """Returns raw structured frame analysis events for timeline visualization."""
    return await supabase_client.get_all_events(camera_id=camera_id, limit=limit)
