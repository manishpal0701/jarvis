"""
AI Package — Ollama communication, response management, and prompt templates.
"""
from ai.ask_ollama import ask_ollama
from ai.ai_response_manager import AIResponseManager
from ai.prompt import GENERATE_CODE_PROMPT, REVIEW_CODE_PROMPT, EXPLAIN_CODE_PROMPT

__all__ = [
    "ask_ollama",
    "AIResponseManager",
    "GENERATE_CODE_PROMPT",
    "REVIEW_CODE_PROMPT",
    "EXPLAIN_CODE_PROMPT",
]
