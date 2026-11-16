import logging
from datetime import datetime
from fastapi import APIRouter, Query
from db.supabase_client import supabase_client
from models.schemas import DigestResponse
from services.synthesizer import transcript_synthesizer

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Security Digest"])

@router.post("/digest", response_model=DigestResponse)
async def generate_daily_digest(
    date_str: str = Query(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
):
    """
    Generates an executive daily security summary paragraph from all surveillance transcripts.
    Highlighting events, anomaly counts, and community safety status.
    """
    transcripts = await supabase_client.get_transcripts(limit=20)
    alerts = await supabase_client.get_alerts(resolved=False)
    
    narratives = [t.get("narrative", "") for t in transcripts if t.get("narrative")]
    if not narratives:
        narratives = ["Standard monitoring conducted. No unusual breaches or perimeter alarms logged."]

    digest_text = await transcript_synthesizer.generate_daily_digest(narratives, date_str)
    total_events = sum(t.get("event_count", 0) for t in transcripts)
    
    safety_assessment = "Normal"
    if len(alerts) > 2:
        safety_assessment = "Elevated Alert"
    elif len(alerts) > 0:
        safety_assessment = "Caution Required"

    return DigestResponse(
        digest=digest_text,
        generated_at=datetime.utcnow().isoformat(),
        total_events=total_events,
        alerts_count=len(alerts),
        safety_assessment=safety_assessment
    )
