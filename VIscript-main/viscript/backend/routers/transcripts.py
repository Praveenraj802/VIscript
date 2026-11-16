from fastapi import APIRouter, HTTPException
from models.schemas import Transcript, TranscriptDetail
from db.supabase_client import get_transcripts, get_transcript_with_events
from uuid import UUID
from typing import List

router = APIRouter()

@router.get("/transcripts", response_model=List[Transcript])
async def list_transcripts(limit: int = 50):
    return await get_transcripts(limit=limit)

@router.get("/transcripts/{id}", response_model=TranscriptDetail)
async def retrieve_transcript(id: UUID):
    result = await get_transcript_with_events(str(id))
    if not result:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return result
