from core.state_machine import State, StateMachine
from core.session_manager import SessionManager

class SleepManager:
    def __init__(self, state_machine: StateMachine, session_manager: SessionManager, speech_coordinator):
        self.state_machine = state_machine
        self.session_manager = session_manager
        self.speech_coordinator = speech_coordinator

    def go_to_sleep(self, reason: str = "timeout"):
        """Transitions Jarvis to sleep mode, plays the sleep notification, and enters wake mode."""
        self.state_machine.transition_to(State.SLEEPING, custom_reason=reason)
        self.session_manager.end_session()
        # Speak the sleep phrase (updates state to WAKE_MODE on complete)
        self.speech_coordinator.speak("I am going to sleep, boss")
