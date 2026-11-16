from pydantic import BaseModel, Field
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime

# SECTION 10: FrameEvent
class FrameEvent(BaseModel):
    time:           str
    camera_id:      str
    people_count:   int        = 0
    activity:       str
    objects:        list[str]  = []
    anomaly_score:  int        = Field(ge=0, le=10)
    anomaly_reason: str | None = None
    location_zone:  str        = "unknown"
    faces_visible:  bool       = False

# Schemas for API responses based on SECTION 7 DB Tables
class Camera(BaseModel):
    id: UUID
    name: str
    location: Optional[str] = None
    rtsp_url: Optional[str] = None
    status: str
    created_at: datetime

class Event(BaseModel):
    id: UUID
    camera_id: UUID
    event_time: datetime
    activity:       str
    people_count:   int
    anomaly_score:  int
    anomaly_reason: Optional[str] = None
    objects:        list[str]
    location_zone:  str
    raw_json: Optional[dict] = None
    created_at: datetime

class Transcript(BaseModel):
    id: UUID
    camera_id: UUID
    period_start: datetime
    period_end: datetime
    narrative: str
    event_count: int
    created_at: datetime

class TranscriptDetail(Transcript):
    events: List[Event] = []

class Alert(BaseModel):
    id: UUID
    camera_id: UUID
    event_id: UUID
    anomaly_score: int
    anomaly_reason: Optional[str] = None
    resolved: bool
    created_at: datetime

# API Request/Response Models
class UploadResponse(BaseModel):
    job_id: str
    status: str
    frame_count: int

class JobStatus(BaseModel):
    job_id: str
    status: str

class QueryRequest(BaseModel):
    question: str
    camera_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]

class HealthCheck(BaseModel):
    status: str
    version: str
