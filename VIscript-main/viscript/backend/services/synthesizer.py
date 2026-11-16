import os
import logging
from typing import List
from models.schemas import FrameEvent
from dotenv import load_dotenv
import google.generativeai as genai
import asyncio
from datetime import datetime, timedelta
from typing import Tuple

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-latest")
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
EMBEDDING_MODEL_NAME = "models/text-embedding-004"

async def generate_embedding(text: str) -> list[float]:
    """Generates a vector embedding for the given text using Gemini."""
    if MOCK_MODE:
        return [0.0] * 768  # Return dummy vector in mock mode
        
    try:
        # the title isn't critical but good practice for retrieval_document capability
        result = await asyncio.to_thread(
            genai.embed_content,
            model=EMBEDDING_MODEL_NAME,
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return []

async def synthesize_transcript(events: List[FrameEvent], camera_name: str) -> Tuple[str, list[float]]:
    """Synthesizes a transcript narrative and generates its vector embedding."""
    if not events:
        return "No events recorded.", []
        
    if MOCK_MODE:
        narrative = f"Mock transcript for {len(events)} events from {camera_name}. Normal activity observed."
        return narrative, [0.0] * 768

    # Sort events by time
    # FrameEvent time is "HH:MM:SS" string.
    # We assume all events are from the same day for this prototype.
    sorted_events = sorted(events, key=lambda e: e.time)
    
    # Group into 30-minute windows
    # Since time is string, we'll just parse to minutes for grouping
    windows = {}
    
    for event in sorted_events:
        try:
            t = datetime.strptime(event.time, "%H:%M:%S")
            # Window key: integer index of 30-min chunk
            window_idx = (t.hour * 60 + t.minute) // 30
            if window_idx not in windows:
                windows[window_idx] = []
            windows[window_idx].append(event)
        except ValueError:
            continue
            
    sorted_window_indices = sorted(windows.keys())
    
    narrative_parts = []
    
    model = genai.GenerativeModel(MODEL_NAME)
    
    for idx in sorted_window_indices:
        window_events = windows[idx]
        
        # Determine time range string
        start_min = idx * 30
        end_min = (idx + 1) * 30
        
        start_h, start_m = divmod(start_min, 60)
        end_h, end_m = divmod(end_min, 60)
        # Handle day wrap? 24:00 -> 00:00
        if end_h >= 24: end_h = 23; end_m = 59
        
        window_start_str = f"{start_h:02d}:{start_m:02d}"
        window_end_str = f"{end_h:02d}:{end_m:02d}"
        
        # Format events text for prompt
        # "14:05:30: [Score 0] Person walking. Objects: person, bag."
        formatted_events_text = "\n".join([
            f"{e.time}: [Score {e.anomaly_score}] {e.activity}. Objects: {', '.join(e.objects)}."
            for e in window_events
        ])
        
        prompt = f"""You are writing a security log for {camera_name}.
Time period: {window_start_str} to {window_end_str}.
Events observed:
{formatted_events_text}

Write a clear 2–3 sentence narrative summary.
Format: "Between [time] and [time]: [what happened]. [Notable events if any]. [Overall assessment: normal/unusual]."
Write in professional English. Be specific with times."""

        try:
            response = await model.generate_content_async(prompt)
            narrative_parts.append(response.text.strip())
            await asyncio.sleep(1) # Rate limit
        except Exception as e:
            logger.error(f"Failed to synthesize window {window_start_str}: {e}")
            narrative_parts.append(f"Could not generate summary for {window_start_str}-{window_end_str}.")
    
    final_narrative = "\n\n".join(narrative_parts)
    
    # Generate embedding for the full 5-minute transcript narrative
    embedding = await generate_embedding(final_narrative)
    
    return final_narrative, embedding
