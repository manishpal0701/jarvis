"""
speech/speech_coordinator.py
Thread-safe speech coordinator. Manages audio playback locks and state machine
transitions for both single-shot and streaming multi-chunk response sessions.
"""
import speech
import time
from core.state_machine import State, StateMachine
from core.timeout_manager import TimeoutManager
import threading

class SpeechCoordinator:
    def __init__(self, state_machine: StateMachine, timeout_manager: TimeoutManager):
        self.state_machine = state_machine
        self.timeout_manager = timeout_manager
        self._lock = threading.Lock()
        self._session_active = False

    def begin_speech_session(self):
        """Signals the start of a streaming or multi-sentence response session."""
        with self._lock:
            self._session_active = True
            self.state_machine.transition_to(State.THINKING)
            self.timeout_manager.reset()

    def speak_chunk(self, text: str, wait: bool = True):
        """
        Speaks a single sentence/chunk during an active session without advancing
        the state machine to WAITING_FOR_NEXT_COMMAND prematurely.
        """
        if not text or not text.strip():
            return

        with self._lock:
            self._session_active = True
            self.state_machine.transition_to(State.SPEAKING)
            self.timeout_manager.reset()

            print(f"Jarvis: {text.strip()}")
            speech.speak(text.strip(), wait=wait)
            self.timeout_manager.reset()

    def end_speech_session(self):
        """
        Signals the end of a streaming response session. Advances state machine
        to WAITING_FOR_NEXT_COMMAND only after all speech and audio playback has completely finished.
        """
        # Wait outside lock until audio queue and playback are 100% finished
        while speech.is_speaking():
            time.sleep(0.05)

        with self._lock:
            self.timeout_manager.reset()
            self._session_active = False
            self.state_machine.transition_to(State.WAITING_FOR_NEXT_COMMAND)

    def speak(self, text: str, wait: bool = True):
        """Convenience method for single-shot speech calls."""
        if not text:
            return

        with self._lock:
            prev_state = self.state_machine.state
            self.state_machine.transition_to(State.SPEAKING)
            self.timeout_manager.reset()

            print(f"Jarvis: {text.strip()}")
            speech.speak(text.strip(), wait=wait)
            self.timeout_manager.reset()

            if self._session_active:
                # Keep session active during streaming; end_speech_session handles final transition
                pass
            elif prev_state == State.WAKE_DETECTED:
                self.state_machine.transition_to(State.ACTIVE_SESSION)
            elif prev_state == State.SLEEPING:
                self.state_machine.transition_to(State.WAKE_MODE)
            else:
                self.state_machine.transition_to(State.WAITING_FOR_NEXT_COMMAND)

    def is_speaking(self) -> bool:
        """
        Returns True if TTS audio is playing, queue is non-empty, state is SPEAKING,
        or a multi-chunk speech session is currently active.
        """
        with self._lock:
            return (
                self._session_active or
                speech.is_speaking() or
                self.state_machine.state in (State.SPEAKING, State.THINKING, State.PROCESSING)
            )

