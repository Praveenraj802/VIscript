import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from models.schemas import FrameEvent

load_dotenv()
logger = logging.getLogger(__name__)

url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

if not url or not key:
    logger.warning("Supabase URL or SERVICE_ROLE_KEY not set")
    # In production, raise error. For scaffold, allow it but client will fail on calls.

try:
    supabase: Client = create_client(url, key)
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None

async def insert_event(event: FrameEvent, camera_id: str) -> str:
    if not supabase: raise RuntimeError("Supabase client not initialized")
    
    data = event.model_dump()
    data["camera_id"] = camera_id
    
    # Convert 'HH:MM:SS' string time to timestamp (using today's date)
    # This is an assumption as video upload date is not provided, 
    # but for prototype "live" feel, today is appropriate.
    current_date = datetime.now().date()
    try:
        t = datetime.strptime(event.time, "%H:%M:%S").time()
        dt = datetime.combine(current_date, t)
        data["event_time"] = dt.isoformat()
    except ValueError:
        logger.warning(f"Invalid time format {event.time}, using now()")
        data["event_time"] = datetime.now().isoformat()
        
    # Remove fields not in DB or map them
    # DB: activity, people_count, anomaly_score, anomaly_reason, objects, location_zone, raw_json
    # FrameEvent: definitions match DB columns mostly.
    # event.time is removed.
    if "time" in data:
        del data["time"]
    if "faces_visible" in data:
        del data["faces_visible"] # Not stored in DB events table per schema
        
    # Raw JSON storage? "raw_json" column.
    # Maybe store the original FrameEvent dump there?
    data["raw_json"] = event.model_dump()
    
    try:
        response = supabase.table("events").insert(data).execute()
        if not response.data:
            raise RuntimeError("Insert returned no data")
            
        inserted_id = response.data[0]['id']
        
        # Task D5: Auto-alert
        if event.anomaly_score > 6:
            await insert_alert(camera_id, inserted_id, event.anomaly_score, event.anomaly_reason)
            
        return inserted_id
    except Exception as e:
        logger.error(f"Error inserting event: {e}")
        raise

async def insert_alert(camera_id: str, event_id: str, anomaly_score: int, anomaly_reason: str | None) -> None:
    if not supabase: raise RuntimeError("Supabase client not initialized")
    
    data = {
        "camera_id": camera_id,
        "event_id": event_id,
        "anomaly_score": anomaly_score,
        "anomaly_reason": anomaly_reason,
        "resolved": False
    }
    supabase.table("alerts").insert(data).execute()

async def insert_transcript(
    camera_id: str, 
    period_start: datetime, 
    period_end: datetime, 
    narrative: str, 
    event_count: int,
    embedding: list[float] | None = None
) -> str:
    if not supabase: raise RuntimeError("Supabase client not initialized")

    data = {
        "camera_id": camera_id,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "narrative": narrative,
        "event_count": event_count
    }
    
    if embedding:
        data["embedding"] = embedding
        
    response = supabase.table("transcripts").insert(data).execute()
    return response.data[0]['id']

async def get_transcripts(camera_id: str | None = None, limit: int = 50) -> list:
    if not supabase: raise RuntimeError("Supabase client not initialized")

    query = supabase.table("transcripts").select("*").order("created_at", desc=True).limit(limit)
    if camera_id:
        query = query.eq("camera_id", camera_id)
    response = query.execute()
    return response.data

async def get_transcript_with_events(transcript_id: str) -> dict:
    if not supabase: raise RuntimeError("Supabase client not initialized")

    t_response = supabase.table("transcripts").select("*").eq("id", transcript_id).single().execute()
    if not t_response.data:
        # Handle not found?
        return None
        
    transcript = t_response.data
    
    start = transcript["period_start"]
    end = transcript["period_end"]
    cam_id = transcript["camera_id"]
    
    e_response = supabase.table("events").select("*")\
        .eq("camera_id", cam_id)\
        .gte("event_time", start)\
        .lte("event_time", end)\
        .order("event_time", desc=False)\
        .execute()
        
    transcript["events"] = e_response.data
    return transcript

async def get_alerts(resolved: bool = False) -> list:
    if not supabase: raise RuntimeError("Supabase client not initialized")

    # Fetch alerts and join camera name
    response = supabase.table("alerts").select("*, cameras(name)").eq("resolved", resolved).order("created_at", desc=True).execute()
    return response.data

async def get_cameras() -> list:
    if not supabase: raise RuntimeError("Supabase client not initialized")

    response = supabase.table("cameras").select("*").eq("status", "active").execute()
    return response.data

async def create_camera(name: str, location: str | None = None, rtsp_url: str | None = None) -> dict:
    if not supabase: raise RuntimeError("Supabase client not initialized")
    
    data = {"name": name, "status": "active"}
    if location: data["location"] = location
    if rtsp_url: data["rtsp_url"] = rtsp_url
        
    response = supabase.table("cameras").insert(data).execute()
    if not response.data:
        raise RuntimeError("Failed to create camera")
    return response.data[0]
