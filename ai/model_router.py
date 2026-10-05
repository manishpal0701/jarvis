import threading
import ollama
from typing import Dict, List, Optional

class ModelRouter:
    """
    Unified Model Task Router for Jarvis.
    Maps system tasks to specific installed Ollama models based on capability:
      - Research, Content Strategy & Design System: qwen3:8b
      - Code Generation, Review & Repair: qwen3:4b-instruct
      - Intent Classification & Fast Routing: phi4-mini:latest
      - General Conversation & Q&A: llama3.2:latest
    """
    _instance = None
    _lock = threading.Lock()

    MODEL_MAPPING = {
        "website_research": "qwen3:8b",
        "website_content": "qwen3:8b",
        "website_design": "qwen3:8b",
        "website_planning": "qwen3:8b",
        "ux_reasoning": "qwen3:8b",
        "general_conversation": "qwen3:8b",
        "follow_up_conversation": "qwen3:8b",
        "general_qa": "qwen3:8b",
        "general_question": "qwen3:8b",
        "explanation": "qwen3:8b",
        "hinglish_conversation": "qwen3:8b",
        "conversation": "qwen3:8b",
        "website_generation": "qwen3:4b-instruct",
        "coding": "qwen3:4b-instruct",
        "code_review": "qwen3:4b-instruct",
        "debugging": "qwen3:4b-instruct",
        "auto_repair": "qwen3:4b-instruct",
        "website_repair": "qwen3:4b-instruct",
        "intent_classification": "phi4-mini:latest",
        "light_routing": "phi4-mini:latest",
        "lightweight_routing": "phi4-mini:latest"
    }

    INSTALLED_MODELS = [
        "qwen3:8b",
        "qwen3:4b-instruct",
        "phi4-mini:latest",
        "llama3.2:latest"
    ]

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelRouter, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._client = ollama.Client()
        self._initialized = True

    @classmethod
    def get_instance(cls):
        return cls()

    def get_model_for_task(self, task_type: str) -> str:
        """Returns the appropriate Ollama model identifier for a given task type."""
        return self.MODEL_MAPPING.get(task_type.lower(), "qwen3:8b")

    def get_installed_models(self) -> List[str]:
        """Returns list of active installed Ollama models."""
        try:
            res = self._client.list()
            models = [m.get("name", "") for m in res.get("models", [])]
            return models if models else self.INSTALLED_MODELS
        except Exception:
            return self.INSTALLED_MODELS

    def get_model_inventory(self) -> Dict[str, str]:
        """Returns model inventory role assignments."""
        return {
            "research": self.MODEL_MAPPING["website_research"],
            "content": self.MODEL_MAPPING["website_content"],
            "design": self.MODEL_MAPPING["website_design"],
            "planning": self.MODEL_MAPPING["website_planning"],
            "coding": self.MODEL_MAPPING["website_generation"],
            "repair": self.MODEL_MAPPING["website_repair"],
            "intent": self.MODEL_MAPPING["intent_classification"],
            "conversation": self.MODEL_MAPPING["conversation"]
        }
