from fastapi import APIRouter
from models.schemas import Alert
from db.supabase_client import get_alerts
from typing import List

router = APIRouter()

@router.get("/alerts", response_model=List[Alert])
async def list_alerts():
    return await get_alerts(resolved=False)
