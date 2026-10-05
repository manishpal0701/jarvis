import json
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
LOG_FILE = os.path.join(DATA_DIR, "conversation_logs.json")


class ConversationManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ConversationManager()
        return cls._instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConversationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.owner = {
            "name": "Manish",
            "relation": "owner"
        }

        self.current_person = self.owner.copy()
        self.history = []  # In-memory history for Ollama context
        self.MAX_HISTORY = 6  # Keep last 6 turns (12 messages) to limit context length

        self.active_entity = None
        self.active_task = None
        self.active_project = None
        self.current_topic = None

        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w") as f:
                json.dump([], f)
        
        self._initialized = True

    def add_to_history(self, role, content):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.MAX_HISTORY * 2:  # roles (user + assistant)
            self.history = self.history[-self.MAX_HISTORY * 2:]

    def process_and_resolve_input(self, user_input: str) -> dict:
        """
        Processes user input, updates active entity/topic context,
        and resolves follow-up pronoun references ('isko', 'isme', etc.).
        """
        from conversation.intelligence.context_tracker import ContextTracker
        tracker = ContextTracker()

        # Check for explicit new target entity in user input
        extracted_entity = tracker.extract_target_entity(user_input)
        if extracted_entity and not tracker.resolve_followup_references(user_input, self.active_entity).get("has_followup"):
            self.active_entity = extracted_entity
            print(f"[CONTEXT_LIFECYCLE] active_entity updated to '{self.active_entity}'")

        # Resolve follow-up references
        resolved = tracker.resolve_followup_references(user_input, self.active_entity)
        if resolved.get("has_followup"):
            print(f"[CONTEXT_RESOLVED] pronoun='{resolved.get('pronoun')}' target='{self.active_entity}'")

        return resolved

    def set_active_context(self, entity: str = None, task: str = None, project: str = None):
        if entity is not None:
            self.active_entity = entity
        if task is not None:
            self.active_task = task
        if project is not None:
            self.active_project = project

    def get_history_context(self, current_query: str = None):
        """
        Returns history context.
        If current_query is provided, filters out stale/unrelated single-turn queries (e.g., date/time queries).
        """
        if not current_query or not self.history:
            return self.history

        # If current query is unrelated to date/time or weather, exclude transient single-turn questions from history
        query_lower = current_query.lower()
        is_date_query = any(w in query_lower for w in ["time", "date", "day", "baje"])
        is_weather_query = any(w in query_lower for w in ["weather", "mausam", "temperature", "rain", "forecast"])

        filtered = []
        for i in range(0, len(self.history), 2):
            pair = self.history[i:i+2]
            if not pair:
                continue
            user_msg = pair[0].get("content", "").lower() if len(pair) > 0 else ""
            
            # Skip historical date/time queries if current query is not date/time
            if not is_date_query and any(kw in user_msg for kw in ["what time is it", "today's date", "current time", "kitne baje", "current date", "what is the date"]):
                continue

            # Skip historical weather queries if current query is not weather
            if not is_weather_query and any(kw in user_msg for kw in ["weather in", "weather kya hai", "aaj ka weather", "what is the weather"]):
                continue

            filtered.extend(pair)

        return filtered


    def clear_history(self):
        self.history = []

    def reset_context(self):
        """
        Resets short-term conversation context, working memory, and active entities
        without deleting long-term user memories.
        """
        self.history = []
        self.active_entity = None
        self.active_task = None
        self.active_project = None
        self.current_topic = None

        try:
            from memory.memory_manager import MemoryManager
            MemoryManager().clear_session_conversation()
        except Exception:
            pass

        print("[CONTEXT_RESET] Conversation intelligence context reset complete.")


    def _patch_speak(self):
        """Monkey patch main.speak to be target-aware if it exists."""
        try:
            if 'main' in sys.modules:
                m = sys.modules['main']
                if hasattr(m, 'speak') and not hasattr(m.speak, '_patched'):
                    original_speak = m.speak
                    def personalized_speak(text):
                        person = self.get_person()
                        name = person["name"]
                        relation = person["relation"]
                        
                        if relation != "owner":
                            import re
                            text = re.sub(r'\bboss\b', name, text, flags=re.IGNORECASE)
                            text = re.sub(r'\bsir\b', name, text, flags=re.IGNORECASE)
                            
                        original_speak(text)
                    
                    personalized_speak._patched = True
                    m.speak = personalized_speak
        except Exception:
            pass  # Fail silently as this is a hack

    def switch_to_guest(self, name, relation):
        # Normalize name for Boss/Sir mode
        if relation == "boss":
            name = "Boss"
        elif relation == "sir":
            name = "Sir"
            
        self.current_person = {
            "name": name,
            "relation": relation
        }
        self._patch_speak()

    def switch_to_owner(self):
        self.current_person = self.owner.copy()
        self._patch_speak()

    def get_person(self):
        return self.current_person

    def is_owner(self):
        return self.current_person["relation"] == "owner"

    def save_log(self, question, answer):
        data = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = []

        data.append({
            "speaker": self.current_person["name"],
            "relation": self.current_person["relation"],
            "question": question,
            "answer": answer
        })

        with open(LOG_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def get_logs(self, person_name):
        if not os.path.exists(LOG_FILE):
            return []
        with open(LOG_FILE, "r") as f:
            try:
                data = json.load(f)
            except Exception:
                return []

        return [
            x for x in data
            if x.get("speaker", "").lower() == person_name.lower()
        ]
