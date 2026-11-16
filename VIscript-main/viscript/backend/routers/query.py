from fastapi import APIRouter, HTTPException
from models.schemas import QueryRequest, QueryResponse
from services.rag import answer_query

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_transcripts(req: QueryRequest):
    try:
        result = await answer_query(req.question, req.camera_id)
        return QueryResponse(answer=result["answer"], sources=result["sources"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
