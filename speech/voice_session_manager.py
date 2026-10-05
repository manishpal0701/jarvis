"""
speech/voice_session_manager.py
Central Voice Session Manager for JARVIS Phase 3.
Enforces single active primary voice session, manages session turn lifecycle,
and maintains stale request invalidation sets for real-time barge-in.
"""

import time
import threading
import logging
from typing import Dict, Optional, Set
from speech.voice_session import VoiceSession
from speech.voice_state_machine import VoiceStateMachine, VoiceState

logger = logging.getLogger("VoiceSessionManager")

class VoiceSessionManager:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = VoiceSessionManager()
            return cls._instance

    def __init__(self):
        self._current_session: Optional[VoiceSession] = None
        self.state_machine = VoiceStateMachine(VoiceState.IDLE)
        self._invalidated_request_ids: Set[str] = set()
        self._invalidated_session_ids: Set[str] = set()
        self._last_interruption_time: float = 0.0

    def start_session(self, user_request: str = "", source: str = "voice", request_id: Optional[str] = None) -> VoiceSession:
        with self._lock:
            if self._current_session and self._current_session.is_active:
                # Invalidate previous active session cleanly
                self._invalidated_request_ids.add(self._current_session.request_id)
                self._invalidated_session_ids.add(self._current_session.session_id)
                self._current_session.is_active = False

            session = VoiceSession(metadata={"source": source, "user_request": user_request})
            if request_id:
                session.request_id = request_id

            self._current_session = session
            self.state_machine.transition_to(VoiceState.LISTENING if source == "voice" else VoiceState.PROCESSING)
            print(f"[VOICE_SESSION_START] session_id={session.session_id} req_id={session.request_id} source={source}", flush=True)
            return session

    def get_active_session(self) -> Optional[VoiceSession]:
        with self._lock:
            return self._current_session

    def invalidate_request(self, request_id: str, reason: str = "interrupted") -> None:
        with self._lock:
            if not request_id:
                return
            self._invalidated_request_ids.add(request_id)
            if self._current_session and self._current_session.request_id == request_id:
                self._invalidated_session_ids.add(self._current_session.session_id)
                self._current_session.is_active = False
                self._current_session.interrupted_at = time.strftime("%Y-%m-%dT%H:%M:%S")
                self._current_session.interruption_count += 1
            self._last_interruption_time = time.time()
            print(f"[VOICE_SESSION_INVALIDATE] request_id={request_id} reason='{reason}'", flush=True)

    def is_request_invalidated(self, request_id: str) -> bool:
        with self._lock:
            return request_id in self._invalidated_request_ids

    def is_session_invalidated(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._invalidated_session_ids

    def mark_speaking_started(self, request_id: str, speech_id: str = None) -> None:
        with self._lock:
            if self._current_session and self._current_session.request_id == request_id:
                self._current_session.speaking_started_at = time.strftime("%Y-%m-%dT%H:%M:%S")
                self._current_session.current_audio_id = speech_id
                self.state_machine.transition_to(VoiceState.SPEAKING)

    def mark_completed(self, request_id: str) -> None:
        with self._lock:
            if self._current_session and self._current_session.request_id == request_id:
                self._current_session.completed_at = time.strftime("%Y-%m-%dT%H:%M:%S")
                self.state_machine.transition_to(VoiceState.COMPLETED)
                self.state_machine.transition_to(VoiceState.IDLE)

    def get_last_interruption_time(self) -> float:
        with self._lock:
            return self._last_interruption_time
