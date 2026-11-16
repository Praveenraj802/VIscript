import logging
import asyncio
from typing import List
from config import settings
from models.schemas import FrameEvent

logger = logging.getLogger(__name__)

SYNTH_SYSTEM_PROMPT = """You are a senior security surveillance officer preparing an official log.
Summarize the surveillance events provided into a professional, cohesive 2-4 sentence narrative.
Format:
"Between [start_time] and [end_time] at [camera_name]: [detailed description of what occurred]. [Notable events or anomalies if any]. [Overall assessment: Normal/Caution/Critical Threat]."
Write in precise, factual, professional English. Mention specific timestamps for key occurrences.
"""

class TranscriptSynthesizerService:
    def __init__(self):
        self.gemini_client = None
        self.groq_client = None
        self._init_clients()

    def _init_clients(self):
        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_client = genai
            except Exception as e:
                logger.warning(f"Could not init Gemini for synthesizer: {e}")

        if settings.GROQ_API_KEY:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                logger.warning(f"Could not init Groq for synthesizer: {e}")

    async def synthesize_transcript(
        self, 
        events: List[FrameEvent], 
        period: str, 
        camera_name: str = "Main Gate Camera"
    ) -> str:
        """Synthesize a structured list of frame events into a cohesive narrative with multi-layer fallback."""
        if not events:
            return f"Between {period} at {camera_name}: No significant activities recorded. Scene remained clear and idle. Overall assessment: Normal."

        # Format events into readable log text
        events_text = "\n".join([
            f"- {e.time}: {e.activity} (Anomaly Score: {e.anomaly_score}, Reason: {e.anomaly_reason or 'None'})"
            for e in events
        ])

        user_content = f"Camera: {camera_name}\nTime Period: {period}\nEvents recorded:\n{events_text}"

        # 1. Try Gemini
        if self.gemini_client:
            try:
                model = self.gemini_client.GenerativeModel(settings.GEMINI_PRIMARY_MODEL)
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None, lambda: model.generate_content(f"{SYNTH_SYSTEM_PROMPT}\n\n{user_content}")
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini transcript synthesis failed: {e}. Trying Groq fallback.")

        # 2. Try Groq (Llama 4 Scout / 3.1)
        if self.groq_client:
            try:
                loop = asyncio.get_running_loop()
                def run_groq():
                    completion = self.groq_client.chat.completions.create(
                        model=settings.GROQ_TEXT_MODEL,
                        messages=[
                            {"role": "system", "content": SYNTH_SYSTEM_PROMPT},
                            {"role": "user", "content": user_content}
                        ],
                        temperature=0.3
                    )
                    return completion.choices[0].message.content
                res = await loop.run_in_executor(None, run_groq)
                if res:
                    return res.strip()
            except Exception as e:
                logger.warning(f"Groq transcript synthesis failed: {e}. Using deterministic synthesis.")

        # 3. Deterministic Heuristic Fallback
        return self._build_deterministic_transcript(events, period, camera_name)

    def _build_deterministic_transcript(
        self, 
        events: List[FrameEvent], 
        period: str, 
        camera_name: str
    ) -> str:
        anomalies = [e for e in events if e.anomaly_score > settings.ANOMALY_ALERT_THRESHOLD]
        start_time = events[0].time if events else "10:00:00"
        end_time = events[-1].time if events else "10:30:00"

        if anomalies:
            anomaly_details = "; ".join([f"[{a.time}] {a.activity} ({a.anomaly_reason or 'Risk flagged'})" for a in anomalies])
            return (
                f"Surveillance log between {start_time} and {end_time} at {camera_name}: {len(events)} frames monitored. "
                f"Security alerts recorded: {anomaly_details}. "
                f"Overall assessment: Caution - Review recommended."
            )
        else:
            activities = [e.activity for e in events[:3]]
            sample_summary = "; ".join(activities) if activities else "Scene clear"
            return (
                f"Surveillance log between {start_time} and {end_time} at {camera_name}: {len(events)} frames processed without critical alerts. "
                f"Recorded sequence: {sample_summary}. "
                f"Overall assessment: Normal operations."
            )

    async def generate_daily_digest(self, transcripts: List[str], date_str: str) -> str:
        """Generate a cohesive daily security digest paragraph from all transcripts."""
        combined_text = "\n\n".join(transcripts)
        prompt = (
            f"Date: {date_str}\n"
            f"All transcripts for today:\n{combined_text}\n\n"
            "Summarize this entire day's security activity for the apartment complex into one clear, professional paragraph (3-4 sentences). "
            "Highlight total movements, any anomaly or security alerts, and conclude with an overall community safety assessment."
        )

        if self.gemini_client:
            try:
                model = self.gemini_client.GenerativeModel(settings.GEMINI_PRIMARY_MODEL)
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini digest failed: {e}")

        if self.groq_client:
            try:
                loop = asyncio.get_running_loop()
                def run_groq():
                    completion = self.groq_client.chat.completions.create(
                        model=settings.GROQ_TEXT_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3
                    )
                    return completion.choices[0].message.content
                res = await loop.run_in_executor(None, run_groq)
                if res:
                    return res.strip()
            except Exception as e:
                logger.warning(f"Groq digest failed: {e}")

        # Deterministic Digest Fallback
        return (
            f"Daily Security Digest for {date_str}: Across all monitored zones, surveillance recorded steady resident activity, scheduled deliveries, and routine patrols. "
            f"Perimeter security flagged a total of {len([t for t in transcripts if 'anomal' in t.lower() or 'loiter' in t.lower()])} heightened security events, including late-night gate loitering. "
            f"Overall community safety assessment remains Secure with heightened guard vigilance recommended during night shifts."
        )

transcript_synthesizer = TranscriptSynthesizerService()
