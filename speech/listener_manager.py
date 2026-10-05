import speech_recognition as sr
import threading
import time
from core.state_machine import State, StateMachine
from core.timeout_manager import TimeoutManager

def normalize_command(raw_text: str) -> str:
    """
    Normalizes recognized transcript by removing ONLY the leading wake word ('jarvis' or 'jarvis,').
    Preserves all rest of the command string intact.
    """
    if not raw_text or raw_text == "None":
        return ""
    text = raw_text.strip()
    words = text.split()
    if words and words[0].lower().rstrip(",.-") == "jarvis":
        rem = " ".join(words[1:]).lstrip(",.- ").strip()
        return rem if rem else text
    return text

class ListenerManager:
    def __init__(self, state_machine: StateMachine, timeout_manager: TimeoutManager, speech_coordinator):
        self.state_machine = state_machine
        self.timeout_manager = timeout_manager
        self.speech_coordinator = speech_coordinator
        self.recognizer = sr.Recognizer()
        # Tuning parameters for human speech, natural pauses, and end-of-speech VAD
        self.recognizer.pause_threshold = 0.8            # Tolerates 0.4s-0.6s natural human pauses inside sentences
        self.recognizer.non_speaking_duration = 0.5
        self.recognizer.dynamic_energy_threshold = True
        self._lock = threading.Lock()
        self._calibrated = False

    def recalibrate(self, duration: float = 0.5):
        """Forces recalibration of ambient noise levels."""
        self._calibrated = False

    def listen_and_recognize(self, mode_state: State) -> str:
        """Listens to microphone input and recognizes it. Enforces single listener."""
        acquired = self._lock.acquire(blocking=False)
        if not acquired:
            return "None"

        from core.task_orchestrator import TaskOrchestrator
        if TaskOrchestrator.get_instance().is_task_active():
            print("[VOICE_LISTEN_SUPPRESSED] reason=ACTIVE_TASK", flush=True)
            time.sleep(0.5)
            self._lock.release()
            return "None"

        mode_name = mode_state.name if hasattr(mode_state, 'name') else str(mode_state)
        print(f"[VOICE_LISTEN_START] mode={mode_name}", flush=True)

        try:
            # Check if speech is currently active for barge-in monitoring
            is_speaking_active = self.speech_coordinator.is_speaking()
            
            if not is_speaking_active:
                # Post-Speech Echo Guard: Wait 300ms after TTS completes so room reverb/echo clears
                if hasattr(self.speech_coordinator, "get_last_speech_end_time"):
                    last_end = self.speech_coordinator.get_last_speech_end_time()
                    if last_end > 0:
                        elapsed_since_speech = time.time() - last_end
                        if elapsed_since_speech < 0.3:
                            time.sleep(0.3 - elapsed_since_speech)

            # Transition to target state
            self.state_machine.transition_to(mode_state)

            with sr.Microphone() as source:
                # Calibrate ambient noise ONCE to avoid per-command latency overhead
                if not self._calibrated:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    if hasattr(self.recognizer, 'energy_threshold'):
                        self.recognizer.energy_threshold = max(300, self.recognizer.energy_threshold)
                    self._calibrated = True

                listen_timeout = 3.0 if self.speech_coordinator.is_speaking() else (8.0 if mode_state == State.LISTENING else 5.0)
                phrase_limit = 5.0 if self.speech_coordinator.is_speaking() else 15.0

                try:
                    capture_start = time.time()
                    audio = self.recognizer.listen(source, timeout=listen_timeout, phrase_time_limit=phrase_limit)
                    duration = round(time.time() - capture_start, 2)
                    print(f"[VOICE_LISTEN_END] duration={duration}s", flush=True)
                except sr.WaitTimeoutError:
                    duration = round(time.time() - capture_start, 2)
                    print(f"[VOICE_LISTEN_END] duration={duration}s", flush=True)
                    if not self.speech_coordinator.is_speaking():
                        print("[ASR_EMPTY] reason=microphone listen timeout", flush=True)
                    return "None"

            # Check if user spoke while speech was active (Barge-In Event)
            was_speaking_during_capture = self.speech_coordinator.is_speaking()

            # Recognize user command
            raw_query = self.recognizer.recognize_google(audio, language="en-IN").strip()
            if raw_query and raw_query != "None":
                if was_speaking_during_capture:
                    print(f"[BARGE_IN_DETECTED] raw='{raw_query}'", flush=True)
                    self.speech_coordinator.interrupt_speech(reason="user_barge_in")

                # Transition to PROCESSING
                if self.state_machine.state != State.WAKE_MODE:
                    self.state_machine.transition_to(State.PROCESSING)

                print(f'[ASR_SUCCESS] raw="{raw_query}"', flush=True)
                normalized = normalize_command(raw_query)
                print(f'[COMMAND_NORMALIZED] command="{normalized}"', flush=True)
                return normalized
            else:
                print("[ASR_EMPTY] reason=empty Google ASR result", flush=True)
                return "None"

        except sr.UnknownValueError:
            print("[ASR_UNKNOWN] reason=SpeechRecognition.UnknownValueError", flush=True)
            if self.state_machine.state == State.PROCESSING:
                self.state_machine.transition_to(State.WAITING_FOR_NEXT_COMMAND)
            return "None"
        except sr.RequestError as re:
            print(f"[ASR_ERROR] reason=SpeechRecognition.RequestError: {re}", flush=True)
            if self.state_machine.state == State.PROCESSING:
                self.state_machine.transition_to(State.WAITING_FOR_NEXT_COMMAND)
            return "None"
        except Exception as e:
            print(f"[ASR_ERROR] reason={e}", flush=True)
            if self.state_machine.state == State.PROCESSING:
                self.state_machine.transition_to(State.WAITING_FOR_NEXT_COMMAND)
            return "None"
        finally:
            self._lock.release()
