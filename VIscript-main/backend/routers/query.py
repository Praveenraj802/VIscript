import logging
from fastapi import APIRouter, HTTPException
from models.schemas import QueryRequest, QueryResponse
from services.rag import rag_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["RAG Intelligence Query"])

@router.post("/query", response_model=QueryResponse)
async def query_transcripts(req: QueryRequest):
    """
    Natural Language RAG Query endpoint.
    Searches ChromaDB / vector embeddings and generates a synthesized answer with citations
    using Gemini 2.5 Flash -> Groq Llama 4 Scout -> Heuristic Direct Synthesis cascade.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Query question cannot be empty.")

    try:
        response = await rag_service.answer_query(
            question=req.question.strip(), 
            camera_id=req.camera_id
        )
        return response
    except Exception as e:
        logger.exception(f"Error executing RAG query: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
