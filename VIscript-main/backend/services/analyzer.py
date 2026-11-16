import os
import json
import base64
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import settings
from models.schemas import FrameEvent

logger = logging.getLogger(__name__)

BASE_SYSTEM_PROMPT = """You are a security camera analyst for a residential apartment complex in India.
Analyze this surveillance camera frame.
Return ONLY a valid JSON object. No prose. No markdown. No explanation.

Use exactly this schema:
{
  "time": "HH:MM:SS",
  "camera_id": "cam_001",
  "people_count": 0,
  "activity": "Brief one-sentence description of what is happening",
  "objects": ["list", "of", "visible", "objects"],
  "anomaly_score": 0,
  "anomaly_reason": null,
  "location_zone": "gate",
  "faces_visible": false
}

RULES:
1. anomaly_score 0-10: 0=normal, 5=slightly unusual, 8+=urgent security threat.
2. Score > 6 only for: loitering >5min, aggression, forced entry, unattended bags, person in restricted area, vehicle blocking gate, unidentified stranger late night.
3. Never identify or describe specific faces (DPDP Act 2023 compliance).
4. faces_visible must always be false.
5. activity must be factual, concise, and non-speculative.
"""

def encode_image_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def clean_json_text(text: str) -> str:
    """Strip markdown code fence if present."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

class FrameAnalyzerService:
    def __init__(self):
        self.gemini_client = None
        self.groq_client = None
        self._init_clients()

    def _init_clients(self):
        # 1. Initialize Gemini
        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_client = genai
                logger.info(f"Gemini client initialized with primary model: {settings.GEMINI_PRIMARY_MODEL}")
            except Exception as e:
                logger.warning(f"Could not configure Gemini client: {e}")

        # 2. Initialize Groq
        if settings.GROQ_API_KEY:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
                logger.info(f"Groq client initialized with model: {settings.GROQ_VISION_MODEL}")
            except Exception as e:
                logger.warning(f"Could not configure Groq client: {e}")

    def _build_temporal_prompt(self, previous_events: List[FrameEvent]) -> str:
        """Improvement 2: Add temporal context to frame analysis for loitering & continuity."""
        prompt = BASE_SYSTEM_PROMPT
        if previous_events:
            recent = previous_events[-3:]
            context = "Recent activity in preceding frames:\n" + "\n".join([
                f"  - [{e.time}] {e.activity} (anomaly_score={e.anomaly_score})"
                for e in recent
            ])
            prompt += f"\n\nCONTEXT FROM PREVIOUS FRAMES:\n{context}\n"
            prompt += "Use this temporal context to detect loitering (>5 min), escalating suspicious behavior, or ongoing delivery operations."
        return prompt

    async def _call_gemini(self, frame_path: str, prompt: str, camera_id: str, timestamp: str) -> Optional[FrameEvent]:
        if not self.gemini_client:
            return None

        models_to_try = [
            settings.GEMINI_PRIMARY_MODEL,
            settings.GEMINI_FALLBACK_MODEL,
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]
        seen = set()
        unique_models = []
        for m in models_to_try:
            if m and m not in seen:
                seen.add(m)
                unique_models.append(m)

        logger.info(f"Attempting Gemini model chain: {unique_models}")

        from PIL import Image
        try:
            img = Image.open(frame_path)
        except Exception as e:
            logger.error(f"Cannot open frame image {frame_path}: {e}")
            return None

        loop = asyncio.get_running_loop()
        for model_name in unique_models:
            try:
                model = self.gemini_client.GenerativeModel(model_name)
                response = await loop.run_in_executor(
                    None, lambda: model.generate_content([prompt, img])
                )
                if response and response.text:
                    raw_text = clean_json_text(response.text)
                    data = json.loads(raw_text)
                    data["camera_id"] = camera_id
                    data["time"] = timestamp
                    data["faces_visible"] = False
                    return FrameEvent(**data)
            except Exception as e:
                logger.warning(f"Gemini model {model_name} error: {e}. Trying fallback model...")

        return None

    async def _call_groq(self, frame_path: str, prompt: str, camera_id: str, timestamp: str) -> Optional[FrameEvent]:
        if not self.groq_client:
            return None
        try:
            b64_image = encode_image_base64(frame_path)
            loop = asyncio.get_running_loop()
            
            def run_groq():
                completion = self.groq_client.chat.completions.create(
                    model=settings.GROQ_VISION_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{b64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2
                )
                return completion.choices[0].message.content

            res_content = await loop.run_in_executor(None, run_groq)
            data = json.loads(res_content)
            data["camera_id"] = camera_id
            data["time"] = timestamp
            data["faces_visible"] = False
            return FrameEvent(**data)
        except Exception as e:
            logger.warning(f"Groq frame analysis error: {e}")
            return None

    async def _call_cv_analysis(self, frame_path: str, camera_id: str, timestamp: str, index: int = 0) -> FrameEvent:
        """
        True Computer Vision Frame Inspection (Non-LLM / Offline fallback):
        Extracts real visual attributes from the actual video frame (brightness, contrast, resolution, lighting).
        Does NOT invent fake mock stories.
        """
        width, height = 640, 360
        brightness = 120.0
        contrast = 30.0

        try:
            from PIL import Image, ImageStat
            with Image.open(frame_path) as im:
                width, height = im.size
                stat = ImageStat.Stat(im)
                brightness = stat.mean[0]
                contrast = stat.stddev[0] if len(stat.stddev) > 0 else 25.0
        except Exception as e:
            logger.debug(f"PIL stat inspection failed: {e}")

        # Determine real lighting condition from pixels
        if brightness < 45:
            lighting = "Low-light / Night"
        elif brightness < 110:
            lighting = "Indoor / Shaded"
        else:
            lighting = "Bright Daylight"

        activity = (
            f"Frame #{index + 1} at {timestamp}: Monitored scene ({width}x{height}, {lighting}, Luminance: {brightness:.0f}/255, Contrast: {contrast:.0f}). "
            f"Notice: Set GEMINI_API_KEY in .env to activate full Gemini Vision object detection."
        )

        return FrameEvent(
            time=timestamp,
            camera_id=camera_id,
            people_count=0,
            activity=activity,
            objects=["surveillance_feed", f"{lighting.lower()}_scene"],
            anomaly_score=0,
            anomaly_reason=None,
            location_zone="monitored_area",
            faces_visible=False,
            frame_path=frame_path
        )

    async def analyze_frame(
        self,
        frame_path: str,
        camera_id: str,
        timestamp: str,
        previous_events: Optional[List[FrameEvent]] = None,
        index: int = 0
    ) -> FrameEvent:
        """
        Analyze a single frame with cascade:
        1. Gemini Vision (gemini-2.0-flash / gemini-1.5-flash)
        2. Groq Llama Vision
        3. Real CV Frame Metric Inspection (No fake mock events)
        """
        if previous_events is None:
            previous_events = []

        prompt = self._build_temporal_prompt(previous_events)

        # 1. Primary: Gemini Vision
        if self.gemini_client:
            res = await self._call_gemini(frame_path, prompt, camera_id, timestamp)
            if res:
                res.frame_path = frame_path
                return res

        # 2. Secondary: Groq Vision
        if self.groq_client:
            res = await self._call_groq(frame_path, prompt, camera_id, timestamp)
            if res:
                res.frame_path = frame_path
                return res

        # 3. Real Computer Vision frame metric inspection
        if not self.gemini_client and not self.groq_client and index == 0:
            logger.warning(
                "⚠️ GEMINI_API_KEY is not configured in .env! "
                "Running Computer Vision frame metric analysis. Add GEMINI_API_KEY to .env for AI object detection."
            )

        res = await self._call_cv_analysis(frame_path, camera_id, timestamp, index)
        return res

    async def analyze_batch(
        self, 
        frame_paths: List[str], 
        camera_id: str = "cam_gate_01"
    ) -> List[FrameEvent]:
        """Process frames in sequence maintaining temporal context."""
        events: List[FrameEvent] = []
        total = len(frame_paths)

        for idx, frame_path in enumerate(frame_paths):
            # Parse timestamp from filename if available (frame_00000_sample_10_15_00.jpg)
            filename = Path(frame_path).stem
            timestamp = "10:00:00"
            if "_" in filename:
                parts = filename.split("_")
                if len(parts) >= 3 and parts[-1].isdigit():
                    timestamp = f"{parts[-3]}:{parts[-2]}:{parts[-1]}"

            event = await self.analyze_frame(
                frame_path=frame_path,
                camera_id=camera_id,
                timestamp=timestamp,
                previous_events=events,
                index=idx
            )
            events.append(event)
            logger.info(f"Analyzed {idx + 1}/{total} frames (score={event.anomaly_score})")
            await asyncio.sleep(0.05)  # Slight delay to prevent rate limit spikes

        return events

frame_analyzer = FrameAnalyzerService()
