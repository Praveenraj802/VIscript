import os
import time
import json
import logging
import asyncio
from typing import List
from models.schemas import FrameEvent
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not set")

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-latest")
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

SYSTEM_PROMPT = """You are a security camera analyst for a residential
apartment complex in India. Analyze this surveillance camera frame.

Return ONLY a valid JSON object. No prose. No markdown. No explanation.

Use exactly this schema:
{
  "time":           "HH:MM:SS",
  "camera_id":      "cam_001",
  "people_count":   0,
  "activity":       "Brief one-sentence description of what is happening",
  "objects":        ["list", "of", "visible", "objects"],
  "anomaly_score":  0,
  "anomaly_reason": null,
  "location_zone":  "gate",
  "faces_visible":  false
}

RULES:
1. anomaly_score range is 0–10. 0 = completely normal. 5 = slightly unusual. 8+ = urgent.
2. Score > 6 ONLY for: loitering more than 5 minutes, aggression, forced entry,
   unattended bags, person in restricted area, vehicle blocking gate.
3. Never identify or describe specific faces.
4. faces_visible must ALWAYS be false — never change this.
5. activity must be factual and observable, never speculative.
"""

async def analyze_frame(frame_path: str, camera_id: str, timestamp: str = "00:00:00") -> FrameEvent:
    if MOCK_MODE:
        await asyncio.sleep(0.1) # Simulate latency
        return FrameEvent(
            time=timestamp,
            camera_id=camera_id,
            people_count=1,
            activity=f"Mock analysis of {os.path.basename(frame_path)}",
            objects=["person", "bag"],
            anomaly_score=0,
            anomaly_reason=None,
            location_zone="gate",
            faces_visible=False
        )

    if not GEMINI_API_KEY:
        logger.error("Gemini API Key missing")
        return FrameEvent(time=timestamp, camera_id=camera_id, activity="Analysis skipped: No Key", anomaly_score=0)

    model = genai.GenerativeModel(MODEL_NAME)
    
    try:
        img = Image.open(frame_path)
    except Exception as e:
        logger.error(f"Frame read error {frame_path}: {e}")
        return FrameEvent(time=timestamp, camera_id=camera_id, activity="Frame error", anomaly_score=0)

    user_prompt = f"Analyze this frame. The timestamp is {timestamp}. Camera ID is {camera_id}."
    
    retries = 2
    for attempt in range(retries):
        try:
            # Generate content
            response = await model.generate_content_async(
                [SYSTEM_PROMPT, user_prompt, img],
                generation_config={"response_mime_type": "application/json", "temperature": 0.2}
            )
            
            text = response.text
            # Cleanup markdown
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            data = json.loads(text)
            
            # Enforce validation
            data["time"] = timestamp
            data["camera_id"] = camera_id
            
            return FrameEvent(**data)
            
        except Exception as e:
            logger.warning(f"Frame analysis attempt {attempt+1} failed: {e}")
            if attempt == retries - 1:
                logger.error(f"All attempts failed for {frame_path}")
                return FrameEvent(
                    time=timestamp,
                    camera_id=camera_id,
                    activity="frame_analysis_failed",
                    anomaly_score=0
                )
            await asyncio.sleep(1) # Backoff
            
    return FrameEvent(time=timestamp, camera_id=camera_id, activity="Unknown error", anomaly_score=0)

async def analyze_batch(frame_paths: list[str], camera_id: str) -> List[FrameEvent]:
    logger.info(f"Analyzing batch of {len(frame_paths)} frames for {camera_id}")
    results = []
    
    # Process 5 frames at a time to avoid rate limits on free tier
    batch_size = 5
    for i in range(0, len(frame_paths), batch_size):
        batch = frame_paths[i : i + batch_size]
        tasks = []
        for j, path in enumerate(batch):
            global_idx = i + j
            # timestamp calculation: assumes 1 frame per 5 seconds
            seconds = global_idx * 5
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            ts = f"{h:02d}:{m:02d}:{s:02d}"
            
            tasks.append(analyze_frame(path, camera_id, ts))
            
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
        logger.info(f"Analyzed {min(i + batch_size, len(frame_paths))}/{len(frame_paths)} frames")
        
        if i + batch_size < len(frame_paths):
            await asyncio.sleep(2) # Generous sleep for API limits
            
    return results
