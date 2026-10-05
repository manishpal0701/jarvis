"""
speech/voice_state_machine.py
Deterministic Voice State Machine for JARVIS Phase 3 Voice Intelligence.
Manages strict voice states and validates legal transitions.
"""

import logging
import threading
from enum import Enum
from typing import Dict, Set

logger = logging.getLogger("VoiceStateMachine")

class VoiceState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    INTERRUPTED = "INTERRUPTED"
    CANCELLING = "CANCELLING"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"

VALID_VOICE_TRANSITIONS: Dict[VoiceState, Set[VoiceState]] = {
    VoiceState.IDLE: {
        VoiceState.LISTENING, VoiceState.PROCESSING, VoiceState.SPEAKING, VoiceState.ERROR
    },
    VoiceState.LISTENING: {
        VoiceState.PROCESSING, VoiceState.SPEAKING, VoiceState.IDLE, VoiceState.INTERRUPTED, VoiceState.CANCELLING, VoiceState.ERROR
    },
    VoiceState.PROCESSING: {
        VoiceState.SPEAKING, VoiceState.WAITING_FOR_INPUT, VoiceState.COMPLETED, VoiceState.IDLE, VoiceState.CANCELLING, VoiceState.ERROR
    },
    VoiceState.SPEAKING: {
        VoiceState.INTERRUPTED, VoiceState.CANCELLING, VoiceState.COMPLETED, VoiceState.WAITING_FOR_INPUT, VoiceState.IDLE, VoiceState.ERROR
    },
    VoiceState.INTERRUPTED: {
        VoiceState.CANCELLING, VoiceState.LISTENING, VoiceState.PROCESSING, VoiceState.IDLE, VoiceState.ERROR
    },
    VoiceState.CANCELLING: {
        VoiceState.LISTENING, VoiceState.IDLE, VoiceState.WAITING_FOR_INPUT, VoiceState.ERROR
    },
    VoiceState.WAITING_FOR_INPUT: {
        VoiceState.LISTENING, VoiceState.PROCESSING, VoiceState.IDLE, VoiceState.CANCELLING, VoiceState.ERROR
    },
    VoiceState.COMPLETED: {
        VoiceState.IDLE, VoiceState.LISTENING, VoiceState.PROCESSING, VoiceState.ERROR
    },
    VoiceState.ERROR: {
        VoiceState.IDLE, VoiceState.LISTENING
    }
}

class VoiceStateMachine:
    def __init__(self, initial_state: VoiceState = VoiceState.IDLE):
        self._state = initial_state
        self._lock = threading.Lock()

    @property
    def state(self) -> VoiceState:
        with self._lock:
            return self._state

    def transition_to(self, new_state: VoiceState, reason: str = "normal") -> bool:
        with self._lock:
            if new_state == self._state:
                return True

            allowed = VALID_VOICE_TRANSITIONS.get(self._state, set())
            if new_state not in allowed:
                print(f"[VOICE_STATE_REJECT] from={self._state.value} to={new_state.value} reason='{reason}'", flush=True)
                logger.warning(f"[VOICE_STATE_REJECT] from={self._state.value} to={new_state.value} reason='{reason}'")
                return False

            old = self._state
            self._state = new_state
            print(f"[VOICE_STATE_TRANSITION] from={old.value} to={new_state.value} reason='{reason}'", flush=True)
            logger.info(f"[VOICE_STATE_TRANSITION] from={old.value} to={new_state.value} reason='{reason}'")
            return True
