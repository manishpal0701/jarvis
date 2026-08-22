import json
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
LOG_FILE = os.path.join(DATA_DIR, "conversation_logs.json")


class ConversationManager:
    _instance = None

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

        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w") as f:
                json.dump([], f)
        
        self._initialized = True

    def add_to_history(self, role, content):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.MAX_HISTORY * 2:  # roles (user + assistant)
            self.history = self.history[-self.MAX_HISTORY * 2:]

    def get_history_context(self):
        return self.history

    def clear_history(self):
        self.history = []

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
