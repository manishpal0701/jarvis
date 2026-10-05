"""
core/progress_reporter.py
Authoritative Progress & Execution Speech Reporter for Jarvis AI Assistant.
Dispatches progress events to structured telemetry logs, WebSocket broadcasting,
and the single authoritative TTS pipeline (EdgeTTSProvider, en-IN-NeerjaExpressiveNeural).
"""
import time
import uuid
import logging
import threading
from datetime import datetime
from typing import Optional

logger = logging.getLogger("ProgressReporter")

class ProgressReporter:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ProgressReporter, cls).__new__(cls)
                cls._instance._dispatched_events = {}
            return cls._instance

    @classmethod
    def get_instance(cls):
        return cls()

    def reset(self):
        with self._lock:
            self._dispatched_events.clear()

    def report(
        self,
        message: str,
        request_id: Optional[str] = None,
        stage: str = "EXECUTION",
        speak: bool = True
    ):
        """
        Reports progress event to:
        1. Structured telemetry logs ([PROGRESS_EVENT])
        2. WebSocket broadcasting to connected frontend ([PROGRESS_WS_TX])
        3. SpeechCoordinator TTS pipeline ([PROGRESS_TTS_DISPATCH]) when speak=True
        """
        if not message or not message.strip():
            return

        clean_text = message.strip()
        req_id = request_id or f"req_{uuid.uuid4().hex[:8]}"

        # Deduplication check for exact (req_id, clean_text) within 3 seconds
        now = time.time()
        event_key = f"{req_id}:{clean_text}"
        with self._lock:
            stale = [k for k, t in list(self._dispatched_events.items()) if now - t > 10.0]
            for k in stale:
                self._dispatched_events.pop(k, None)

            if event_key in self._dispatched_events and (now - self._dispatched_events[event_key]) < 3.0:
                print(f"[PROGRESS_DUPLICATE_BLOCKED] request_id={req_id} text=\"{clean_text[:30]}\"", flush=True)
                return
            self._dispatched_events[event_key] = now

        # 1. Structured Telemetry Log
        print(f"[PROGRESS_EVENT]\nrequest_id={req_id}\nstage={stage}\ntext={clean_text}\nspeak={speak}", flush=True)
        logger.info(f"[PROGRESS_EVENT] request_id={req_id} stage={stage} text=\"{clean_text}\" speak={speak}")

        timestamp = datetime.now().isoformat()

        # 2. Broadcast JSON event to WebSocket clients
        try:
            from api.websocket.jarvis import broadcast_sync
            print(f"[PROGRESS_WS_TX]\nrequest_id={req_id}\nstage={stage}\nevent=progress", flush=True)
            broadcast_sync({
                "type": "progress",
                "event": "progress",
                "request_id": req_id,
                "stage": stage,
                "text": clean_text,
                "speak": speak,
                "timestamp": timestamp
            })
        except Exception as ex:
            logger.warning(f"Failed to broadcast progress over WebSocket: {ex}")

        # 3. Dispatch to TTS Pipeline if speak=True (non-blocking wait=False)
        if speak:
            print(f"[APP_SPEECH]\nrequest_id={req_id}\nstage={stage}\ntext={clean_text}", flush=True)
            print(f"[APP_SPEECH_DISPATCH]\nrequest_id={req_id}", flush=True)
            print(f"[PROGRESS_TTS_DISPATCH]\nrequest_id={req_id}\nstage={stage}", flush=True)
            try:
                from conversation.conversation_engine import ConversationEngine
                engine = ConversationEngine()
                if engine and hasattr(engine, "speech_coordinator"):
                    engine.speech_coordinator.speak(clean_text, wait=False, request_id=req_id)
                else:
                    from speech.speech_coordinator import SpeechCoordinator
                    from core.state_machine import StateMachine
                    from core.timeout_manager import TimeoutManager
                    sc = SpeechCoordinator(StateMachine(), TimeoutManager())
                    sc.speak(clean_text, wait=False, request_id=req_id)
            except Exception as ex:
                logger.error(f"Progress speech dispatch error: {ex}")

