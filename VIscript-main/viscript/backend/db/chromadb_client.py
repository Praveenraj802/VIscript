import os
import logging
from db.supabase_client import supabase
from services.synthesizer import generate_embedding

logger = logging.getLogger(__name__)

# RPC function name expected in Supabase for vector search
# E.g., match_transcripts(query_embedding vector(768), match_threshold float, match_count int)
RPC_FUNCTION_NAME = "match_transcripts" 

async def search_transcripts(query: str, camera_id: str | None = None, top_k: int = 5) -> list:
    """
    Searches for relevant transcripts using Supabase pgvector RPC.
    Returns a list of dicts with 'text' and 'metadata' to emulate the previous ChromaDB format.
    """
    if not supabase:
        logger.warning("Supabase client not initialized. Cannot perform vector search.")
        return []
        
    try:
        # Generate embedding for the search query
        query_embedding = await generate_embedding(query)
        
        if not query_embedding:
            logger.error("Got empty embedding for query.")
            return []
            
        # Call the Supabase RPC function for vector similarity search
        rpc_params = {
            "query_embedding": query_embedding,
            "match_threshold": 0.0, # Adjust based on needed similarity
            "match_count": top_k
        }
        
        if camera_id:
            rpc_params["filter_camera_id"] = camera_id
            
        response = supabase.rpc(RPC_FUNCTION_NAME, rpc_params).execute()
        
        results = []
        if response.data:
            for row in response.data:
                # Map Supabase row back to the format expected by RAG
                results.append({
                    "text": row.get('narrative', ''),
                    "metadata": {
                        "id": row.get('id', ''),
                        "camera_id": row.get('camera_id', ''),
                        "timestamp": row.get('period_start', ''),
                        "similarity": row.get('similarity', 0)
                    }
                })
        
        return results
        
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []
