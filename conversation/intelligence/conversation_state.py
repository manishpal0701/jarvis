import threading

class ConversationState:
    """
    Thread-safe session-level active conversation state manager.
    Tracks short-term topic flow, user state, turn count, and response strategies
    for the active conversation session without mutating persistent long-term memory.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConversationState, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        with self._lock:
            self._state = {
                "current_topic": None,
                "previous_topic": None,
                "current_intent": None,
                "current_emotion": "neutral",
                "last_user_message": None,
                "pending_question": None,
                "conversation_goal": None,
                "last_response_type": None,
                "turn_count": 0
            }
            self._initialized = True

    def update(self, **kwargs):
        """Updates specific attributes of the active conversation state."""
        with self._lock:
            for key, val in kwargs.items():
                if key in self._state:
                    if key == "current_topic" and val != self._state["current_topic"]:
                        self._state["previous_topic"] = self._state["current_topic"]
                    self._state[key] = val

    def set_pending_question(self, question_type: str | None):
        """Sets or clears pending follow-up/clarification question state."""
        with self._lock:
            self._state["pending_question"] = question_type

    def increment_turn(self):
        """Increments turn counter."""
        with self._lock:
            self._state["turn_count"] += 1

    def get_snapshot(self) -> dict:
        """Returns a snapshot copy of the current conversation state."""
        with self._lock:
            return self._state.copy()

    def reset(self):
        """Resets active session conversation state."""
        with self._lock:
            self._state = {
                "current_topic": None,
                "previous_topic": None,
                "current_intent": None,
                "current_emotion": "neutral",
                "last_user_message": None,
                "pending_question": None,
                "conversation_goal": None,
                "last_response_type": None,
                "turn_count": 0
            }

