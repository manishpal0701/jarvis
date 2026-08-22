import threading
from conversation.conversation_manager import ConversationManager
from memory.memory_manager import MemoryManager

class ContextManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ContextManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._conv = ConversationManager()
        self._mem = MemoryManager()
        self._lock = threading.Lock()
        self._initialized = True

    def get_person(self):
        with self._lock:
            return self._conv.get_person()

    def is_owner(self):
        with self._lock:
            return self._conv.is_owner()

    def switch_to_guest(self, name, relation):
        with self._lock:
            self._conv.switch_to_guest(name, relation)

    def switch_to_owner(self):
        with self._lock:
            self._conv.switch_to_owner()

    def add_to_history(self, role, content):
        with self._lock:
            self._conv.add_to_history(role, content)

    def get_history_context(self):
        with self._lock:
            return self._conv.get_history_context()

    def clear_history(self):
        with self._lock:
            self._conv.clear_history()

    def save_log(self, question, answer):
        with self._lock:
            self._conv.save_log(question, answer)

    def get_logs(self, person_name):
        with self._lock:
            return self._conv.get_logs(person_name)

    def get_relevant_memories(self, query: str = None, limit: int = 5) -> list[dict]:
        """Retrieves relevant memories via MemoryManager for context building."""
        with self._lock:
            if query:
                return self._mem.retrieve_relevant(query, limit=limit)
            return self._mem.retrieve(limit=limit)
