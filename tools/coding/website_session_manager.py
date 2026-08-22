from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import os

class WebsiteSessionState(Enum):
    IDLE = "IDLE"
    REQUIREMENTS_COLLECTION = "REQUIREMENTS_COLLECTION"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    BUILDING = "BUILDING"
    COMPLETED = "COMPLETED"
    BUILD_FAILED = "BUILD_FAILED"

class WebsiteSessionManager:
    _instance = None

    def __init__(self):
        self.state = WebsiteSessionState.IDLE
        self.brief = None
        self.original_command = ""
        self.owner_info = {}
        self.session_dir = ""

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = WebsiteSessionManager()
        return cls._instance

    def reset_session(self):
        self.state = WebsiteSessionState.IDLE
        self.brief = None
        self.original_command = ""
        self.owner_info = {}
        self.session_dir = ""

    def is_active(self) -> bool:
        return self.state != WebsiteSessionState.IDLE

    def start_session(self, user_command: str, owner_info: Dict[str, Any] = None) -> str:
        from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer, WebsiteCategory, WebsiteSubject
        self.owner_info = owner_info or {}
        self.original_command = user_command
        cat = WebsiteRequirementsAnalyzer.detect_category(user_command)
        subj = WebsiteRequirementsAnalyzer.detect_subject(user_command)
        if not subj.name and self.owner_info.get("name"):
            subj.name = self.owner_info["name"]

        self.brief = WebsiteRequirementsAnalyzer.extract_information(user_command, cat, subj)
        self.state = WebsiteSessionState.AWAITING_CONFIRMATION

        summary = WebsiteRequirementsAnalyzer.format_brief_summary(self.brief)
        return f"{summary}\n\nYe brief correct hai? Agar haan, main website build karta hoon."

    def handle_input(self, user_input: str) -> str:
        input_lower = user_input.lower().strip()

        if self.state == WebsiteSessionState.AWAITING_CONFIRMATION:
            affirmative_words = ["haan", "han", "yes", "correct", "sahi", "build", "bana", "sure", "ok", "yep", "ha"]
            is_affirmative = any(w in input_lower for w in affirmative_words) and not any(w in input_lower for w in ["nahi", "nahin", "no", "not", "wrong", "galat"])

            if is_affirmative:
                self.state = WebsiteSessionState.BUILDING
                self.brief.confirmed = True

                from tools.coding.code_assistant import CodeAssistant
                assistant = CodeAssistant()
                task_prompt = self.original_command or self.brief.title
                code, path = assistant.generate_code(task_prompt, brief=self.brief)

                if "Error" in code or not code:
                    self.state = WebsiteSessionState.BUILD_FAILED
                    return f"Boss, website build process mein issue aa gaya hai: {code}\nKya main naye specifications se try karoon?"

                self.state = WebsiteSessionState.COMPLETED
                return f"Done Boss! Website successfully generate and preview build launch ho chuki hai."
            else:
                from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer
                self.brief.design_preference += f" | {user_input}"
                summary = WebsiteRequirementsAnalyzer.format_brief_summary(self.brief)
                return f"Brief update kar diya hai:\n{summary}\n\nAb ye correct hai?"

        elif self.state == WebsiteSessionState.BUILD_FAILED:
            self.state = WebsiteSessionState.AWAITING_CONFIRMATION
            from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer
            self.brief.design_preference += f" | {user_input}"
            summary = WebsiteRequirementsAnalyzer.format_brief_summary(self.brief)
            return f"Brief update kar diya hai:\n{summary}\n\nYe brief correct hai? Agar haan, retry karte hain."

        return "Session complete ho chuka hai."
