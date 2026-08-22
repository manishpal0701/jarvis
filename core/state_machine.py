from enum import Enum, auto
import threading
import logging

class State(Enum):
    WAKE_MODE = auto()
    WAKE_DETECTED = auto()
    ACTIVE_SESSION = auto()
    LISTENING = auto()
    PROCESSING = auto()
    THINKING = auto()
    SPEAKING = auto()
    WAITING_FOR_NEXT_COMMAND = auto()
    SLEEPING = auto()

class StateMachine:
    def __init__(self, initial_state=State.WAKE_MODE):
        self._state = initial_state
        self._lock = threading.Lock()
        self._state_changed = threading.Condition(self._lock)
        self.logger = logging.getLogger("StateMachine")

    @property
    def state(self):
        with self._lock:
            return self._state

    def transition_to(self, new_state: State, custom_reason: str = None) -> bool:
        with self._lock:
            old_state = self._state
            if old_state == new_state:
                return True
            
            # Verify transitions
            valid = False
            if old_state == State.WAKE_MODE:
                valid = new_state in (State.WAKE_DETECTED, State.WAKE_MODE)
            elif old_state == State.WAKE_DETECTED:
                valid = new_state in (State.ACTIVE_SESSION, State.WAKE_MODE)
            elif old_state == State.ACTIVE_SESSION:
                valid = new_state in (State.LISTENING, State.SLEEPING, State.WAKE_MODE)
            elif old_state == State.LISTENING:
                valid = new_state in (State.PROCESSING, State.SPEAKING, State.WAITING_FOR_NEXT_COMMAND, State.WAKE_MODE, State.SLEEPING)
            elif old_state == State.PROCESSING:
                valid = new_state in (State.THINKING, State.SPEAKING, State.WAITING_FOR_NEXT_COMMAND, State.WAKE_MODE, State.SLEEPING)
            elif old_state == State.THINKING:
                valid = new_state in (State.SPEAKING, State.WAITING_FOR_NEXT_COMMAND, State.WAKE_MODE, State.SLEEPING)
            elif old_state == State.SPEAKING:
                valid = new_state in (State.WAITING_FOR_NEXT_COMMAND, State.LISTENING, State.WAKE_MODE, State.SLEEPING)
            elif old_state == State.WAITING_FOR_NEXT_COMMAND:
                valid = new_state in (State.LISTENING, State.SLEEPING, State.WAKE_MODE)
            elif old_state == State.SLEEPING:
                valid = new_state in (State.WAKE_MODE,)

            # Safety net: WAKE_MODE can be transitioned to at any time to recover
            if new_state == State.WAKE_MODE:
                valid = True

            if not valid:
                self.logger.warning(f"Invalid transition attempted: {old_state.name} -> {new_state.name}")
                return False

            self._state = new_state
            self._print_state_transition(old_state, new_state, custom_reason)
            self._state_changed.notify_all()
            return True

    def _print_state_transition(self, old_state: State, new_state: State, reason: str):
        if new_state == State.LISTENING:
            print("Listening...")
        elif new_state == State.PROCESSING:
            print("Recognizing...")
        elif new_state == State.WAKE_DETECTED:
            print("\nWake word detected.\n")
        elif new_state == State.THINKING:
            print("Thinking...")
        elif new_state == State.SPEAKING:
            print("Speaking...")
        elif new_state == State.WAITING_FOR_NEXT_COMMAND:
            print("Waiting for next command...")
        elif new_state == State.SLEEPING:
            if reason == "timeout":
                print("Session timeout.\nGoing to sleep.")
            else:
                print("Going to sleep.")

    def wait_for_state(self, state: State, timeout: float = None) -> bool:
        with self._lock:
            return self._state_changed.wait_for(lambda: self._state == state, timeout=timeout)
