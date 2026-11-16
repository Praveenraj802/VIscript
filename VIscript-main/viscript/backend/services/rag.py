import os
import logging
from typing import List, Dict
import google.generativeai as genai
from db.chromadb_client import search_transcripts
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-latest")
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

async def answer_query(question: str, camera_id: str | None = None) -> Dict:
    if MOCK_MODE:
        return {
            "answer": f"Mock answer to '{question}'. Based on transcripts, everything is normal.",
            "sources": ["10:00:00", "10:30:00"]
        }
        
    # Step 1: Search ChromaDB
    results = await search_transcripts(question, camera_id=camera_id, top_k=5)
    
    if not results:
        return {
            "answer": "No transcript data available yet matching your query.",
            "sources": []
        }
        
    # Step 2: Build context
    context_lines = []
    sources = []
    
    # Sort results by time? Or relevance? Chroma returns by relevance (distance).
    # Context usually better if chronological? But relevance is key for RAG.
    # We'll stick to relevance order but include timestamps in text.
    
    for r in results:
        ts = r['metadata'].get('timestamp', 'Unknown Time')
        txt = r['text']
        context_lines.append(f"[{ts}] {txt}")
        if ts not in sources:
            sources.append(ts)
            
    context_str = "\n\n".join(context_lines)
    
    # Step 3: Call Gemini
    model = genai.GenerativeModel(MODEL_NAME)
    
    prompt = f"""You are a helpful security assistant for an apartment complex.
Answer the question using ONLY the surveillance transcript excerpts below.
If the answer is not in the transcripts, say clearly: "This information is not in the available transcripts."
Always include specific times when referencing events.
Be factual. Answer in 2–4 sentences.

Question: {question}

Transcript excerpts:
{context_str}"""

    try:
        response = await model.generate_content_async(prompt)
        answer = response.text.strip()
    except Exception as e:
        logger.error(f"RAG generation failed: {e}")
        answer = "I'm sorry, I encountered an error generating the answer."
        
    return {
        "answer": answer,
        "sources": sources
    }
