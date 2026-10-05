"""
speech/voice_session.py
Structured VoiceSession data model for JARVIS Phase 3 Voice Intelligence.
Tracks identity, timings, interruption count, and state lifecycle across single voice turns.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class VoiceSession:
    session_id: str = field(default_factory=lambda: f"vses_{uuid.uuid4().hex[:8]}")
    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    message_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    state: str = "IDLE"  # IDLE, LISTENING, PROCESSING, SPEAKING, INTERRUPTED, CANCELLING, WAITING_FOR_INPUT, COMPLETED, ERROR
    started_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    listening_started_at: Optional[str] = None
    processing_started_at: Optional[str] = None
    speaking_started_at: Optional[str] = None
    interrupted_at: Optional[str] = None
    completed_at: Optional[str] = None
    current_audio_id: Optional[str] = None
    interruption_count: int = 0
    user_speech_detected: bool = False
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "request_id": self.request_id,
            "message_id": self.message_id,
            "state": self.state,
            "started_at": self.started_at,
            "listening_started_at": self.listening_started_at,
            "processing_started_at": self.processing_started_at,
            "speaking_started_at": self.speaking_started_at,
            "interrupted_at": self.interrupted_at,
            "completed_at": self.completed_at,
            "current_audio_id": self.current_audio_id,
            "interruption_count": self.interruption_count,
            "user_speech_detected": self.user_speech_detected,
            "is_active": self.is_active,
            "metadata": self.metadata
        }
