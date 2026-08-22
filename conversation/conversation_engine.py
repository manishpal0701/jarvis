"""
conversation/conversation_engine.py
Main conversation engine loop. Manages session active state, background command execution,
and state machine transitions (WAKE_MODE -> ACTIVE_SESSION -> LISTENING -> PROCESSING -> THINKING -> SPEAKING -> WAITING_FOR_NEXT_COMMAND -> LISTENING).
"""
import time
import threading
from core.state_machine import State, StateMachine
from core.session_manager import SessionManager
from core.timeout_manager import TimeoutManager
from ai.ai_response_manager import AIResponseManager
from speech.speech_coordinator import SpeechCoordinator
from speech.listener_manager import ListenerManager
from speech.wake_manager import WakeManager
from speech.sleep_manager import SleepManager
from core.thread_manager import ThreadManager

class ConversationEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConversationEngine, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, process_command_callback=None):
        if self._initialized:
            return
        
        self.state_machine = StateMachine()
        self.session_manager = SessionManager(self.state_machine)
        self.timeout_manager = TimeoutManager(timeout_seconds=10.0)
        self.speech_coordinator = SpeechCoordinator(self.state_machine, self.timeout_manager)
        self.listener_manager = ListenerManager(self.state_machine, self.timeout_manager, self.speech_coordinator)
        
        self.wake_manager = WakeManager(
            self.state_machine,
            self.timeout_manager,
            self.session_manager,
            self.listener_manager,
            self.speech_coordinator
        )
        
        self.sleep_manager = SleepManager(
            self.state_machine,
            self.session_manager,
            self.speech_coordinator
        )
        
        self.ai_manager = AIResponseManager()
        self.thread_manager = ThreadManager()
        
        if process_command_callback is None:
            from conversation.command_router import CommandRouter
            router = CommandRouter(self.speech_coordinator)
            self.process_command_callback = router.route_command
        else:
            self.process_command_callback = process_command_callback
            
        self.running = False

        from tools.coding.website_session_manager import WebsiteSessionManager
        self.website_session_manager = WebsiteSessionManager.get_instance()
        
        # Start prewarming Ollama
        self.ai_manager.prewarm()
        self._initialized = True

    def has_active_website_session(self) -> bool:
        return self.website_session_manager.is_active()

    def handle_website_input(self, user_input: str) -> str:
        return self.website_session_manager.handle_input(user_input)

    def start_website_session(self, task: str) -> str:
        owner_info = {"name": "Manish"}
        return self.website_session_manager.start_session(task, owner_info=owner_info)


    def run(self):
        """Starts the main conversation engine loop."""
        self.running = True
        print("Jarvis Conversation Engine is active and running.")
        
        while self.running:
            try:
                state = self.state_machine.state
                
                if state == State.WAKE_MODE:
                    # Clear session activity flag
                    self.session_manager.end_session()
                    # Blocks until wake word is detected
                    self.wake_manager.check_wake_word()
                    
                elif self.session_manager.is_active:
                    # Strictly block listening if processing, thinking, speaking, or if speech coordinator is active
                    if state in (State.PROCESSING, State.THINKING, State.SPEAKING) or self.speech_coordinator.is_speaking():
                        time.sleep(0.1)
                        continue
                    
                    # Check timeout before listening
                    remaining = self.timeout_manager.time_remaining()
                    if remaining <= 0:
                        self.sleep_manager.go_to_sleep(reason="timeout")
                        continue
                    
                    # Dynamically set listen timeout based on remaining session time
                    listen_timeout = min(5.0, remaining)
                    if listen_timeout < 0.5:
                        self.sleep_manager.go_to_sleep(reason="timeout")
                        continue
                    
                    # Listen for user input
                    query = self.listener_manager.listen_and_recognize(State.LISTENING)
                    
                    if query.lower() in ["exit", "stop", "shutdown", "bye"]:
                        self.speech_coordinator.speak("goodbye boss")
                        self.running = False
                        break
                        
                    if query != "None":
                        # Valid user interaction: Reset timer
                        self.timeout_manager.reset()
                        
                        # Transition to PROCESSING
                        self.state_machine.transition_to(State.PROCESSING)
                        
                        # Run command in background thread
                        def execute_and_update():
                            try:
                                if self.process_command_callback:
                                    self.process_command_callback(query)
                            except Exception as e:
                                print(f"Error running command: {e}")
                            finally:
                                # Wait until speech coordinator and audio playback are completely finished
                                while self.speech_coordinator.is_speaking():
                                    time.sleep(0.1)
                                self.state_machine.transition_to(State.WAITING_FOR_NEXT_COMMAND)
                                self.timeout_manager.reset()
                                    
                        self.thread_manager.run_in_background(execute_and_update)
                    else:
                        # No valid command heard
                        if self.state_machine.state in (State.LISTENING, State.PROCESSING) and not self.speech_coordinator.is_speaking():
                            self.state_machine.transition_to(State.WAITING_FOR_NEXT_COMMAND)
                            
                else:
                    # Safety recovery state
                    self.state_machine.transition_to(State.WAKE_MODE)
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"Error in Conversation Loop: {e}")
                time.sleep(0.5)
