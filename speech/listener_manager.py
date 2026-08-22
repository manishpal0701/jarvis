import speech_recognition as sr
import threading
import time
from core.state_machine import State, StateMachine
from core.timeout_manager import TimeoutManager

class ListenerManager:
    def __init__(self, state_machine: StateMachine, timeout_manager: TimeoutManager, speech_coordinator):
        self.state_machine = state_machine
        self.timeout_manager = timeout_manager
        self.speech_coordinator = speech_coordinator
        self.recognizer = sr.Recognizer()
        self._lock = threading.Lock()
        self._calibrated = False

    def recalibrate(self, duration: float = 0.5):
        """Forces recalibration of ambient noise levels."""
        self._calibrated = False

    def listen_and_recognize(self, mode_state: State) -> str:
        """Listens to microphone input and recognizes it. Enforces single listener."""
        # Non-blocking acquire to ensure only one listener thread is active
        acquired = self._lock.acquire(blocking=False)
        if not acquired:
            return "None"

        try:
            # Wait if the speech engine is currently speaking
            while self.speech_coordinator.is_speaking():
                time.sleep(0.1)

            # Transition to appropriate state (e.g. LISTENING or WAKE_MODE)
            self.state_machine.transition_to(mode_state)

            with sr.Microphone() as source:
                # Wait if speech starts just before entering microphone capture
                while self.speech_coordinator.is_speaking():
                    time.sleep(0.1)

                # Calibrate ambient noise ONCE to avoid per-command latency overhead
                if not self._calibrated:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    self._calibrated = True

                if self.speech_coordinator.is_speaking():
                    return "None"

                try:
                    # Timeout of 5 seconds, phrase limit of 7 seconds
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=7)
                except sr.WaitTimeoutError:
                    return "None"

            # If speech is active now, discard what was recorded to prevent self-recognition
            if self.speech_coordinator.is_speaking():
                return "None"

            # Transition to PROCESSING (which prints Recognizing...)
            self.state_machine.transition_to(State.PROCESSING)

            query = self.recognizer.recognize_google(audio, language="en-IN")
            return query.strip()

        except sr.UnknownValueError:
            if self.state_machine.state == State.PROCESSING:
                self.state_machine.transition_to(State.WAITING_FOR_NEXT_COMMAND)
            return "None"
        except Exception:
            if self.state_machine.state == State.PROCESSING:
                self.state_machine.transition_to(State.WAITING_FOR_NEXT_COMMAND)
            return "None"
        finally:
            self._lock.release()
