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
        self._listeners = set()
        self.logger = logging.getLogger("StateMachine")

    def add_listener(self, callback):
        """Register a callback for state transition notifications."""
        with self._lock:
            self._listeners.add(callback)

    def remove_listener(self, callback):
        """Unregister a listener callback."""
        with self._lock:
            self._listeners.discard(callback)

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
                valid = new_state in (State.WAKE_DETECTED, State.WAKE_MODE, State.SPEAKING, State.LISTENING, State.PROCESSING, State.THINKING, State.WAITING_FOR_NEXT_COMMAND, State.ACTIVE_SESSION)
            elif old_state == State.WAKE_DETECTED:
                valid = new_state in (State.ACTIVE_SESSION, State.SPEAKING, State.PROCESSING, State.THINKING, State.WAKE_MODE, State.LISTENING)
            elif old_state == State.ACTIVE_SESSION:
                valid = new_state in (State.LISTENING, State.PROCESSING, State.THINKING, State.SPEAKING, State.SLEEPING, State.WAKE_MODE)
            elif old_state == State.LISTENING:
                valid = new_state in (State.PROCESSING, State.THINKING, State.SPEAKING, State.WAITING_FOR_NEXT_COMMAND, State.WAKE_MODE, State.SLEEPING)
            elif old_state == State.PROCESSING:
                valid = new_state in (State.THINKING, State.SPEAKING, State.WAITING_FOR_NEXT_COMMAND, State.WAKE_MODE, State.SLEEPING, State.LISTENING)
            elif old_state == State.THINKING:
                valid = new_state in (State.SPEAKING, State.WAITING_FOR_NEXT_COMMAND, State.WAKE_MODE, State.SLEEPING, State.LISTENING)
            elif old_state == State.SPEAKING:
                valid = new_state in (State.WAITING_FOR_NEXT_COMMAND, State.LISTENING, State.WAKE_MODE, State.SLEEPING, State.PROCESSING, State.THINKING, State.ACTIVE_SESSION)
            elif old_state == State.WAITING_FOR_NEXT_COMMAND:
                valid = new_state in (State.LISTENING, State.SPEAKING, State.PROCESSING, State.THINKING, State.SLEEPING, State.WAKE_MODE)
            elif old_state == State.SLEEPING:
                valid = new_state in (State.WAKE_MODE, State.SPEAKING, State.LISTENING)

            # Safety net: WAKE_MODE can be transitioned to at any time to recover
            if new_state == State.WAKE_MODE:
                valid = True

            if not valid:
                self.logger.warning(f"Invalid transition attempted: {old_state.name} -> {new_state.name}")
                return False

            self._state = new_state
            self._print_state_transition(old_state, new_state, custom_reason)
            self._state_changed.notify_all()

            # Notify registered state listeners
            listeners = list(self._listeners)
            for listener in listeners:
                try:
                    listener(old_state, new_state)
                except Exception as exc:
                    self.logger.warning(f"Error in StateMachine listener: {exc}")

            # Broadcast state changes to connected WebSocket clients (Frontend Live2D app)
            try:
                from api.websocket.jarvis import broadcast_sync
                state_name = new_state.name if hasattr(new_state, 'name') else str(new_state)
                if new_state == State.WAKE_DETECTED:
                    broadcast_sync({"type": "wake_detected"})
                broadcast_sync({"type": "state", "state": state_name})
            except Exception:
                pass

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
