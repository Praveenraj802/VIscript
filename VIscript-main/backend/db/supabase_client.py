import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from config import settings
from models.schemas import FrameEvent

logger = logging.getLogger("visualiq.db.supabase")

class SupabaseClientService:
    def __init__(self):
        self.client = None
        self._is_connected = False
        
        # Local in-memory persistent store for development / offline resilience
        self._users: List[Dict[str, Any]] = []
        self._cameras: List[Dict[str, Any]] = []
        self._events: List[Dict[str, Any]] = []
        self._transcripts: List[Dict[str, Any]] = []
        self._alerts: List[Dict[str, Any]] = []

        self._init_client()

    def _init_client(self):
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY and not settings.SUPABASE_URL.startswith("https://your-"):
            try:
                from supabase import create_client, Client
                self.client: Client = create_client(
                    settings.SUPABASE_URL, 
                    settings.SUPABASE_SERVICE_ROLE_KEY
                )
                self._is_connected = True
                logger.info("Connected successfully to Supabase PostgreSQL database.")
            except Exception as e:
                logger.warning(f"Could not connect to Supabase: {e}. Falling back to in-memory store.")
                self._is_connected = False
                if settings.is_production:
                    logger.critical("PRODUCTION ERROR: Supabase connection failed in production mode!")
        else:
            if settings.is_production:
                logger.critical("PRODUCTION CONFIG ERROR: Supabase credentials not configured in production mode!")
            else:
                logger.info("Supabase credentials not configured. Running with in-memory development store.")
            self._is_connected = False

    # -------------------------------------------------------------
    # User Management (Auth)
    # -------------------------------------------------------------
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        norm_email = email.strip().lower()
        if self._is_connected and self.client:
            try:
                res = self.client.table("users").select("*").eq("email", norm_email).limit(1).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase get_user_by_email query failed: {e}. Checking local store.")

        for u in self._users:
            if u.get("email") == norm_email:
                return u
        return None

    async def insert_user(
        self,
        user_id: str,
        email: str,
        password_hash: str,
        name: str,
        role: str
    ) -> Dict[str, Any]:
        user_data = {
            "id": user_id,
            "email": email.strip().lower(),
            "password_hash": password_hash,
            "name": name,
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self._users = [u for u in self._users if u.get("email") != user_data["email"]]
        self._users.append(user_data)

        if self._is_connected and self.client:
            try:
                self.client.table("users").insert(user_data).execute()
                logger.info(f"User {email} persisted to Supabase database.")
            except Exception as e:
                logger.warning(f"Supabase insert_user error: {e}. User saved to in-memory store.")

        return user_data

    # -------------------------------------------------------------
    # Camera Management
    # -------------------------------------------------------------
    async def get_cameras(self) -> List[Dict[str, Any]]:
        if self._is_connected and self.client:
            try:
                res = self.client.table("cameras").select("*").execute()
                if res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_cameras failed: {e}. Using local store.")
        return self._cameras

    async def insert_camera(
        self, 
        name: str, 
        location: str = "Main Area", 
        rtsp_url: Optional[str] = None, 
        camera_id: Optional[str] = None
    ) -> Dict[str, Any]:
        cid = camera_id or f"cam_{uuid.uuid4().hex[:6]}"
        cam_data = {
            "id": cid,
            "name": name,
            "location": location,
            "status": "active",
            "stream_url": rtsp_url,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self._cameras = [c for c in self._cameras if c.get("id") != cid]
        self._cameras.append(cam_data)
        if self._is_connected and self.client:
            try:
                self.client.table("cameras").insert(cam_data).execute()
            except Exception as e:
                logger.warning(f"Supabase insert_camera error: {e}")
        return cam_data

    async def delete_camera(self, camera_id: str) -> bool:
        self._cameras = [c for c in self._cameras if c.get("id") != camera_id]
        if self._is_connected and self.client:
            try:
                self.client.table("cameras").delete().eq("id", camera_id).execute()
            except Exception as e:
                logger.warning(f"Supabase delete_camera error: {e}")
        return True

    # -------------------------------------------------------------
    # Event Management
    # -------------------------------------------------------------
    async def insert_event(self, event: FrameEvent, camera_id: str) -> str:
        event_id = str(uuid.uuid4())
        event_data = {
            "id": event_id,
            "camera_id": camera_id,
            "event_time": event.time,
            "activity": event.activity,
            "people_count": event.people_count,
            "anomaly_score": event.anomaly_score,
            "anomaly_reason": event.anomaly_reason,
            "objects": event.objects,
            "location_zone": event.location_zone,
            "raw_json": event.model_dump(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        # Save to local store
        self._events.append(event_data)

        if self._is_connected and self.client:
            try:
                self.client.table("events").insert(event_data).execute()
            except Exception as e:
                logger.warning(f"Supabase event insert failed ({e}). Saved to local store.")

        # Auto-alert trigger when anomaly_score > threshold
        if event.anomaly_score > settings.ANOMALY_ALERT_THRESHOLD:
            await self.insert_alert(
                camera_id=camera_id,
                event_id=event_id,
                anomaly_score=event.anomaly_score,
                anomaly_reason=event.anomaly_reason,
                time=event.time,
                activity=event.activity
            )

        return event_id

    async def get_all_events(self, camera_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        if self._is_connected and self.client:
            try:
                query = self.client.table("events").select("*").order("created_at", desc=True).limit(limit)
                if camera_id:
                    query = query.eq("camera_id", camera_id)
                res = query.execute()
                if res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_all_events error ({e}). Using local store.")

        events = self._events
        if camera_id:
            events = [e for e in events if e.get("camera_id") == camera_id]
        return events[:limit]

    # -------------------------------------------------------------
    # Alert Management
    # -------------------------------------------------------------
    async def insert_alert(
        self,
        camera_id: str,
        event_id: str,
        anomaly_score: int,
        anomaly_reason: Optional[str] = None,
        time: Optional[str] = None,
        activity: Optional[str] = None
    ) -> str:
        alert_id = str(uuid.uuid4())
        camera_name = next((c["name"] for c in self._cameras if c["id"] == camera_id), camera_id)
        alert_data = {
            "id": alert_id,
            "camera_id": camera_id,
            "camera_name": camera_name,
            "event_id": event_id,
            "anomaly_score": anomaly_score,
            "anomaly_reason": anomaly_reason or "Suspicious anomaly detected",
            "time": time or datetime.now().strftime("%H:%M:%S"),
            "activity": activity or "Anomalous event flagged by AI",
            "resolved": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        self._alerts.insert(0, alert_data)

        if self._is_connected and self.client:
            try:
                self.client.table("alerts").insert(alert_data).execute()
            except Exception as e:
                logger.warning(f"Supabase alert insert failed ({e}). Saved to local store.")

        return alert_id

    async def get_alerts(
        self, 
        camera_id: Optional[str] = None, 
        resolved: Optional[bool] = False
    ) -> List[Dict[str, Any]]:
        if self._is_connected and self.client:
            try:
                query = self.client.table("alerts").select("*").order("created_at", desc=True)
                if resolved is not None:
                    query = query.eq("resolved", resolved)
                if camera_id:
                    query = query.eq("camera_id", camera_id)
                res = query.execute()
                if res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_alerts error ({e}). Using local store.")

        alerts = self._alerts
        if resolved is not None:
            alerts = [a for a in alerts if a.get("resolved") == resolved]
        if camera_id:
            alerts = [a for a in alerts if a.get("camera_id") == camera_id]
        return alerts

    async def resolve_alert(self, alert_id: str) -> bool:
        if self._is_connected and self.client:
            try:
                self.client.table("alerts").update({"resolved": True}).eq("id", alert_id).execute()
            except Exception as e:
                logger.warning(f"Supabase resolve_alert error: {e}")

        for a in self._alerts:
            if a.get("id") == alert_id:
                a["resolved"] = True
                return True
        return False

    # -------------------------------------------------------------
    # Transcript Management
    # -------------------------------------------------------------
    async def insert_transcript(
        self,
        camera_id: str,
        period_start: str,
        period_end: str,
        narrative: str,
        event_count: int = 0,
        events: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        transcript_id = str(uuid.uuid4())
        camera_name = next((c["name"] for c in self._cameras if c["id"] == camera_id), camera_id)
        transcript_data = {
            "id": transcript_id,
            "camera_id": camera_id,
            "camera_name": camera_name,
            "period_start": period_start,
            "period_end": period_end,
            "narrative": narrative,
            "event_count": event_count,
            "events": events or [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        self._transcripts.insert(0, transcript_data)

        if self._is_connected and self.client:
            try:
                self.client.table("transcripts").insert(transcript_data).execute()
            except Exception as e:
                logger.warning(f"Supabase transcript insert failed ({e}). Saved to local store.")

        return transcript_id

    async def get_transcripts(
        self, 
        camera_id: Optional[str] = None, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Fetch transcripts, filtering by camera_id when provided."""
        if self._is_connected and self.client:
            try:
                query = self.client.table("transcripts").select("*").order("created_at", desc=True).limit(limit)
                if camera_id:
                    query = query.eq("camera_id", camera_id)
                res = query.execute()
                if res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_transcripts error ({e}). Using local store.")

        results = self._transcripts
        if camera_id:
            results = [t for t in results if t.get("camera_id") == camera_id]
        return results[:limit]

    async def get_transcript_by_id(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        if self._is_connected and self.client:
            try:
                res = self.client.table("transcripts").select("*").eq("id", transcript_id).single().execute()
                if res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_transcript_by_id error: {e}")

        for t in self._transcripts:
            if t.get("id") == transcript_id:
                return t
        return None

supabase_client = SupabaseClientService()
