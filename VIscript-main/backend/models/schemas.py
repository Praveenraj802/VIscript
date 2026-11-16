from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

class FrameEvent(BaseModel):
    time: str = Field(..., description="Timestamp HH:MM:SS or ISO string")
    camera_id: str = Field(..., description="ID or identifier of camera")
    people_count: int = Field(default=0, ge=0, description="Number of visible persons")
    activity: str = Field(..., description="Factual description of scene activity")
    objects: List[str] = Field(default_factory=list, description="List of recognized objects")
    anomaly_score: int = Field(default=0, ge=0, le=10, description="Anomaly score 0 (normal) to 10 (critical)")
    anomaly_reason: Optional[str] = Field(default=None, description="Reason if anomaly_score > 0")
    location_zone: str = Field(default="unknown", description="Zone e.g. gate, lobby, parking")
    faces_visible: bool = Field(default=False, description="Privacy constraint: always false")
    frame_path: Optional[str] = Field(default=None, description="Local or temp path to frame image")

class JobStatus(BaseModel):
    job_id: str
    status: str = Field(..., description="pending | extracting | analyzing | synthesizing | storing | done | failed")
    message: Optional[str] = None
    frame_count: int = 0
    analyzed_count: int = 0
    camera_id: Optional[str] = "cam_gate_01"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    role: Optional[str] = "Surveillance Operator"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    user: Dict[str, Any]

class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    role: str

class Camera(BaseModel):
    id: str
    name: str
    location: Optional[str] = "Main Area"
    status: str = "active"
    stream_url: Optional[str] = None
    created_at: Optional[str] = None

class Transcript(BaseModel):
    id: str
    camera_id: str
    camera_name: Optional[str] = None
    period_start: str
    period_end: str
    narrative: str
    event_count: int = 0
    events: Optional[List[FrameEvent]] = None
    created_at: Optional[str] = None

class Alert(BaseModel):
    id: str
    camera_id: str
    camera_name: Optional[str] = None
    event_id: Optional[str] = None
    time: Optional[str] = None
    activity: Optional[str] = None
    anomaly_score: int
    anomaly_reason: Optional[str] = None
    resolved: bool = False
    created_at: Optional[str] = None

class QueryRequest(BaseModel):
    question: str
    camera_id: Optional[str] = None

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[str] = Field(default_factory=list)
    provider: Optional[str] = None
    latency_ms: Optional[float] = None

class DigestResponse(BaseModel):
    digest: str
    generated_at: str
    total_events: int = 0
    alerts_count: int = 0
    safety_assessment: str = "Normal"
