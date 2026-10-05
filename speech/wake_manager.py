from core.state_machine import State, StateMachine
from core.timeout_manager import TimeoutManager
from core.session_manager import SessionManager
from speech.listener_manager import ListenerManager, normalize_command

class WakeManager:
    def __init__(self, state_machine: StateMachine, timeout_manager: TimeoutManager, 
                 session_manager: SessionManager, listener_manager: ListenerManager, speech_coordinator):
        self.state_machine = state_machine
        self.timeout_manager = timeout_manager
        self.session_manager = session_manager
        self.listener_manager = listener_manager
        self.speech_coordinator = speech_coordinator

    def check_wake_word(self):
        """Listens for the wake word. Transitions to active session on success."""
        query = self.listener_manager.listen_and_recognize(State.WAKE_MODE)
        if not query or query == "None":
            return False

        if "jarvis" in query.lower():
            print("[WAKE_DETECTED] word=jarvis", flush=True)
            self.state_machine.transition_to(State.WAKE_DETECTED)
            self.session_manager.start_session()
            self.timeout_manager.reset()

            normalized = normalize_command(query)
            if normalized and normalized.lower() != "jarvis":
                print(f'[COMMAND_RECOGNIZED] text="{normalized}"', flush=True)
                return normalized
            else:
                self.speech_coordinator.speak("Yes Boss")
                return True
        return False
