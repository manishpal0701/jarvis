from core.state_machine import State, StateMachine
from core.timeout_manager import TimeoutManager
from core.session_manager import SessionManager
from speech.listener_manager import ListenerManager

class WakeManager:
    def __init__(self, state_machine: StateMachine, timeout_manager: TimeoutManager, 
                 session_manager: SessionManager, listener_manager: ListenerManager, speech_coordinator):
        self.state_machine = state_machine
        self.timeout_manager = timeout_manager
        self.session_manager = session_manager
        self.listener_manager = listener_manager
        self.speech_coordinator = speech_coordinator

    def check_wake_word(self) -> bool:
        """Listens for the wake word. Transitions to active session on success."""
        query = self.listener_manager.listen_and_recognize(State.WAKE_MODE)
        if "jarvis" in query.lower():
            # Transition to WAKE_DETECTED (prints Wake word detected)
            self.state_machine.transition_to(State.WAKE_DETECTED)
            
            # Start session and reset inactivity timeout
            self.session_manager.start_session()
            self.timeout_manager.reset()
            
            # Speak "Yes Boss" (updates state to ACTIVE_SESSION upon completion)
            self.speech_coordinator.speak("Yes Boss")
            return True
        return False
