import asyncio
import logging
import time
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import cv2
import numpy as np

from config import settings
from models.schemas import FrameEvent
from db.supabase_client import supabase_client
from db.chromadb_client import chromadb_client
from services.analyzer import frame_analyzer
from services.synthesizer import transcript_synthesizer

def normalize_stream_url(raw_url: str):
    url_str = str(raw_url).strip()
    if url_str.isdigit():
        return int(url_str)

    # Auto-normalize mobile phone IP camera streams (Android IP Webcam, DroidCam, iOS IP Camera)
    if url_str.startswith("http://") or url_str.startswith("https://"):
        from urllib.parse import urlparse
        parsed = urlparse(url_str)
        # IP Webcam (Android) default port 8080
        if parsed.port == 8080 and (not parsed.path or parsed.path == "/"):
            return f"{parsed.scheme}://{parsed.netloc}/video"
        # DroidCam default port 4747
        if parsed.port == 4747 and (not parsed.path or parsed.path == "/"):
            return f"{parsed.scheme}://{parsed.netloc}/video"
        # IP Camera Lite (iOS) default port 8081
        if parsed.port == 8081 and (not parsed.path or parsed.path == "/"):
            return f"{parsed.scheme}://{parsed.netloc}/video"

    return url_str

class RTSPStreamSession:
    def __init__(self, camera_id: str, rtsp_url: str, camera_name: Optional[str] = None):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.camera_name = camera_name or camera_id.replace("_", " ").title()
        self.is_running = False
        self.reconnect_count = 0
        self.last_frame_time = 0.0
        
        # Frame storage
        self.latest_frame_mat: Optional[np.ndarray] = None
        self.latest_frame_bytes: Optional[bytes] = None
        self._frame_lock = threading.Lock()
        
        # Event & Transcription state
        self.event_buffer: deque = deque(maxlen=100) # Circular buffer of analyzed events
        self.uncommitted_events: List[FrameEvent] = [] # Events waiting for next transcript batch
        self.frame_seq: int = 0
        self.transcription_enabled: bool = True
        self.transcription_interval: int = 12 # Analyze 1 live frame every 12 seconds
        self._is_analyzing: bool = False
        
        # Background workers
        self._capture_thread: Optional[threading.Thread] = None
        self._transcribe_task: Optional[asyncio.Task] = None

    def _render_standby_frame(self, message: str = "CONNECTING TO FEED...") -> bytes:
        """Generates an animated CCTV standby card if feed drops or camera reconnecting."""
        placeholder = np.zeros((360, 640, 3), dtype=np.uint8)
        # Subtle grid background
        placeholder[::40, :, :] = [25, 35, 50]
        placeholder[:, ::40, :] = [25, 35, 50]
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(placeholder, f"FEED: {self.camera_name.upper()}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 200), 2)
        cv2.putText(placeholder, message, (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.putText(placeholder, f"SOURCE: {str(self.rtsp_url)[:45]}", (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (140, 140, 140), 1)
        cv2.putText(placeholder, f"LIVE CLOCK: {now_str}", (30, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        _, buf = cv2.imencode(".jpg", placeholder, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        return buf.tobytes()

    def _capture_loop(self):
        """Dedicated background thread reading frames from OpenCV device/RTSP/Mobile IP Camera."""
        source = normalize_stream_url(self.rtsp_url)
        logger.info(f"Capture worker started for camera {self.camera_id} from source: {source}")
        
        cap = cv2.VideoCapture(source)
        if hasattr(cv2, 'CAP_PROP_BUFFERSIZE'):
            try:
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass

        fail_count = 0
        while self.is_running:
            try:
                ret, frame = cap.read() if cap.isOpened() else (False, None)
                if not ret or frame is None:
                    fail_count += 1
                    status_msg = "CONNECTING TO CCTV STREAM..." if fail_count < 4 else f"STREAM STANDBY / RETRY #{self.reconnect_count}"
                    standby_bytes = self._render_standby_frame(status_msg)
                    
                    with self._frame_lock:
                        self.latest_frame_mat = None
                        self.latest_frame_bytes = standby_bytes

                    time.sleep(1.0)
                    if fail_count % 5 == 0:
                        self.reconnect_count += 1
                        cap.release()
                        cap = cv2.VideoCapture(source)
                    continue

                fail_count = 0
                self.last_frame_time = time.time()
                
                # Resize if high resolution to keep latency sub-second
                h, w = frame.shape[:2]
                if w > 1280:
                    frame = cv2.resize(frame, (1280, int(h * 1280 / w)))

                # Add real-time timestamp HUD overlay
                display_frame = frame.copy()
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(display_frame, f"{self.camera_name.upper()} • {now_str}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 180), 2)

                _, buf = cv2.imencode(".jpg", display_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                frame_bytes = buf.tobytes()

                with self._frame_lock:
                    self.latest_frame_mat = frame
                    self.latest_frame_bytes = frame_bytes

                # Throttle capture loop slightly (~25 FPS)
                time.sleep(0.04)

            except Exception as e:
                logger.warning(f"Error in capture loop for {self.camera_id}: {e}")
                time.sleep(1.0)

        cap.release()
        logger.info(f"Capture worker terminated for camera {self.camera_id}")

    async def _transcribe_loop(self):
        """Asynchronous continuous AI frame analyzer & transcript synthesizer."""
        logger.info(f"AI live transcription worker active for camera {self.camera_id}")
        # Brief initial warmup
        await asyncio.sleep(4)

        while self.is_running:
            try:
                await asyncio.sleep(self.transcription_interval)
                if not self.transcription_enabled:
                    continue

                await self.capture_and_transcribe_sample()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in live transcription loop for {self.camera_id}: {e}")
                await asyncio.sleep(5)

    async def capture_and_transcribe_sample(self) -> Optional[FrameEvent]:
        """Samples the latest frame, analyzes via Vision AI, saves event and synthesizes transcript."""
        if self._is_analyzing:
            return None

        # Grab clean frame snapshot
        with self._frame_lock:
            if self.latest_frame_mat is None:
                return None
            frame_snapshot = self.latest_frame_mat.copy()

        self._is_analyzing = True
        temp_path = None
        try:
            self.frame_seq += 1
            now_dt = datetime.now()
            time_str = now_dt.strftime("%H:%M:%S")
            
            # Save temporary image file in system temp dir (outside workspace so watchfiles won't reload)
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "visualiq_live"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_path = str(temp_dir / f"sample_{self.camera_id}_{int(time.time()*1000)}.jpg")
            cv2.imwrite(temp_path, frame_snapshot)

            # 1. Analyze single frame with Vision AI (Gemini 2.5 Flash -> Groq -> Heuristics)
            recent_context = list(self.event_buffer)[-3:]
            event: FrameEvent = await frame_analyzer.analyze_frame(
                frame_path=temp_path,
                camera_id=self.camera_id,
                timestamp=time_str,
                previous_events=recent_context,
                index=self.frame_seq
            )

            # 2. Persist event to database & trigger anomaly alert if score > threshold
            await supabase_client.insert_event(event, camera_id=self.camera_id)
            self.event_buffer.append(event)
            self.uncommitted_events.append(event)
            logger.info(f"[Live AI] Event logged for {self.camera_id} at {time_str}: {event.activity} (Anomaly: {event.anomaly_score})")

            # 3. Batch synthesis: Synthesize narrative transcript every 3 sampled events (~36-45s)
            if len(self.uncommitted_events) >= 3:
                await self._synthesize_batch()

            return event

        except Exception as e:
            logger.error(f"Failed to transcribe live frame for {self.camera_id}: {e}")
            return None
        finally:
            self._is_analyzing = False
            # DPDP Act privacy compliance: Clean up transient raw frame
            if temp_path and Path(temp_path).exists():
                try:
                    Path(temp_path).unlink()
                except Exception:
                    pass

    async def _synthesize_batch(self):
        """Synthesizes uncommitted events into a timestamped official narrative transcript."""
        if not self.uncommitted_events:
            return

        batch = list(self.uncommitted_events)
        self.uncommitted_events.clear()

        period_start = batch[0].time
        period_end = batch[-1].time
        period = f"{period_start} - {period_end}"

        try:
            # Generate cohesive narrative
            narrative = await transcript_synthesizer.synthesize_transcript(
                events=batch,
                period=period,
                camera_name=self.camera_name
            )

            # Persist transcript in DB
            transcript_id = await supabase_client.insert_transcript(
                camera_id=self.camera_id,
                period_start=period_start,
                period_end=period_end,
                narrative=narrative,
                event_count=len(batch),
                events=[e.model_dump() for e in batch]
            )

            # Embed and index chunk in ChromaDB for Intelligence Q&A RAG
            metadata = {
                "transcript_id": transcript_id,
                "camera_id": self.camera_id,
                "period": period,
                "source": "live_stream"
            }
            await chromadb_client.store_transcript_chunk(
                text=narrative,
                metadata=metadata,
                chunk_id=f"chunk_{transcript_id}"
            )
            logger.info(f"[Live AI] Synthesized transcript {transcript_id} for {self.camera_id} ({period}): {narrative[:60]}...")

        except Exception as e:
            logger.error(f"Batch transcript synthesis failed for {self.camera_id}: {e}")

    async def start(self):
        """Starts both the frame capture worker thread and the AI transcription loop."""
        if self.is_running:
            return

        self.is_running = True
        
        # 1. Start frame grabber thread
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name=f"cctv-capture-{self.camera_id}"
        )
        self._capture_thread.start()

        # 2. Start asyncio live transcription task
        self._transcribe_task = asyncio.create_task(self._transcribe_loop())
        logger.info(f"Live CCTV Stream & AI Ingestion Pipeline active for camera: {self.camera_id}")

    async def stop(self):
        """Stops stream workers and flushes any pending events."""
        self.is_running = False
        if self._transcribe_task:
            self._transcribe_task.cancel()
        
        # Flush remaining events if any
        if self.uncommitted_events:
            try:
                await self._synthesize_batch()
            except Exception:
                pass

        logger.info(f"Stopped live stream session for camera: {self.camera_id}")

    async def generate_mjpeg_stream(self):
        """Yields MJPEG stream directly for browser HTTP streaming."""
        while self.is_running:
            with self._frame_lock:
                frame_bytes = self.latest_frame_bytes

            if frame_bytes:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
            
            await asyncio.sleep(0.04) # ~25 fps

    def get_recent_events(self, limit: int = 20) -> List[FrameEvent]:
        return list(self.event_buffer)[-limit:]


class StreamManager:
    def __init__(self):
        self.streams: Dict[str, RTSPStreamSession] = {}

    def get_session(self, camera_id: str) -> Optional[RTSPStreamSession]:
        return self.streams.get(camera_id)

    def register_stream(self, camera_id: str, rtsp_url: str, camera_name: Optional[str] = None) -> RTSPStreamSession:
        if camera_id in self.streams:
            session = self.streams[camera_id]
            session.rtsp_url = rtsp_url
            if camera_name:
                session.camera_name = camera_name
            return session

        session = RTSPStreamSession(camera_id, rtsp_url, camera_name=camera_name)
        self.streams[camera_id] = session
        return session

    async def start_stream(self, camera_id: str, rtsp_url: str, camera_name: Optional[str] = None) -> RTSPStreamSession:
        session = self.register_stream(camera_id, rtsp_url, camera_name=camera_name)
        if not session.is_running:
            await session.start()
        return session

    async def stop_stream(self, camera_id: str):
        if camera_id in self.streams:
            session = self.streams.pop(camera_id)
            await session.stop()

    def get_stream_health(self) -> Dict[str, Any]:
        return {
            cam_id: {
                "running": s.is_running,
                "reconnect_count": s.reconnect_count,
                "buffered_events": len(s.event_buffer),
                "uncommitted_events": len(s.uncommitted_events),
                "transcription_enabled": s.transcription_enabled,
                "last_active": s.last_frame_time
            }
            for cam_id, s in self.streams.items()
        }

stream_manager = StreamManager()
