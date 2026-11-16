import logging
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from db.supabase_client import supabase_client
from models.schemas import Alert

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Security Alerts"])

@router.get("/alerts", response_model=List[Alert])
async def get_security_alerts(
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status (None for all)")
):
    """
    Returns anomaly-flagged alerts (anomaly_score > 6).
    Supports camera and resolution status filtering.
    """
    alerts = await supabase_client.get_alerts(camera_id=camera_id, resolved=resolved)
    return alerts

@router.post("/alerts/{alert_id}/resolve")
async def resolve_security_alert(alert_id: str):
    """Marks a security anomaly alert as resolved by a guard or administrator."""
    success = await supabase_client.resolve_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found or already resolved.")
    return {"status": "ok", "message": f"Alert {alert_id} marked as resolved."}
