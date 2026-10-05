from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import os

class WebsiteSessionState(Enum):
    IDLE = "IDLE"
    WEBSITE_REQUESTED = "WEBSITE_REQUESTED"
    COLLECTING_CLIENT_BRIEF = "COLLECTING_CLIENT_BRIEF"
    ANALYZING_BRIEF = "ANALYZING_BRIEF"
    BRIEF_READY = "BRIEF_READY"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    EDITING_BRIEF = "EDITING_BRIEF"
    APPROVED = "APPROVED"
    WEBSITE_GENERATION = "WEBSITE_GENERATION"
    BUILD = "BUILD"
    BROWSER_QA = "BROWSER_QA"
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
        self.WEBSITE_GENERATION_STARTED = False

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
        self.WEBSITE_GENERATION_STARTED = False

    def is_active(self) -> bool:
        return self.state != WebsiteSessionState.IDLE

    def start_brief_collection(self, user_command: str = "") -> str:
        from tools.coding.local_client_brief import LocalClientBriefSession
        from tools.coding.workspace_manager import WorkspaceManager
        from tools.coding.client_brief_ingestion import ClientBriefParser

        self.state = WebsiteSessionState.WEBSITE_REQUESTED
        self.WEBSITE_GENERATION_STARTED = False
        self.original_command = user_command

        local_session = LocalClientBriefSession.get_instance()
        local_session.reset_session()

        if user_command and not any(trig in user_command.lower() for trig in ["ek website bana do", "website bana do"]):
            local_session.add_user_message(user_command)

        # Ensure Workspace UI opens for Client Brief interaction
        try:
            ws = WorkspaceManager.get_instance()
            ws.open_workspace(file_path="ClientBrief.json", language="json", open_browser=True)
            ws.set_status("Client Brief & Assets Collection Active", "thinking")
        except Exception as e:
            print(f"[WebsiteSessionManager]: Workspace UI launch notice: {e}")

        self.state = WebsiteSessionState.COLLECTING_CLIENT_BRIEF
        self.brief = ClientBriefParser.parse_local_client_session(local_session)

        msg = (
            "Okay Boss. Client Brief & Assets interface open ho gaya hai.\n\n"
            "Aap text, details, images, reference URLs/Videos/PDFs bhej sakte ho, ya chat mein details bata sakte ho.\n\n"
            "Jab saari details complete ho jayein to 'bas itni hi details hain' ya UI me 'Generate Website' approve kar dena."
        )
        return msg


    def start_session(self, user_command: str, owner_info: Dict[str, Any] = None) -> str:
        return self.start_brief_collection(user_command)

    def handle_input(self, user_input: str) -> str:
        from tools.coding.local_client_brief import LocalClientBriefSession
        from tools.coding.client_brief_ingestion import ClientBriefParser

        input_lower = user_input.lower().strip()
        local_session = LocalClientBriefSession.get_instance()

        if self.state in (WebsiteSessionState.COLLECTING_CLIENT_BRIEF, WebsiteSessionState.EDITING_BRIEF):
            local_session.add_user_message(user_input)

            if local_session.check_completion_signal(user_input):
                self.state = WebsiteSessionState.ANALYZING_BRIEF
                self.brief = ClientBriefParser.parse_local_client_session(local_session)
                self.state = WebsiteSessionState.BRIEF_READY
                self.state = WebsiteSessionState.WAITING_FOR_APPROVAL

                summary = local_session.get_pre_build_summary(self.brief)
                return (
                    f"{summary}\n\n"
                    "I understand the brief.\n\n"
                    "Ready to build?\n\n"
                    "[ BUILD WEBSITE ]\n"
                    "[ EDIT BRIEF ]\n"
                    "[ ADD MORE DETAILS ]\n\n"
                    "Boss, brief ready hai. Website bana du?"
                )
            else:
                return (
                    "Got it Boss. Multi-message details update ho gayi hain.\n"
                    "Aur details/images/references bhej sakte ho, ya jab complete ho jaye to 'bas itni hi details hain' keh dena."
                )

        elif self.state in (WebsiteSessionState.WAITING_FOR_APPROVAL, WebsiteSessionState.BRIEF_READY):
            affirmative_words = ["haan", "han", "yes", "bana do", "proceed", "build website", "start", "go ahead", "yes boss", "generate it", "banao", "ok", "sure"]
            negative_words = ["nahi", "nahin", "no", "not", "wrong", "galat", "wait", "stop", "edit"]
            is_affirmative = any(w in input_lower for w in affirmative_words) and not any(w in input_lower for w in negative_words)

            if is_affirmative:
                self.state = WebsiteSessionState.APPROVED
                self.WEBSITE_GENERATION_STARTED = True
                self.state = WebsiteSessionState.WEBSITE_GENERATION
                self.state = WebsiteSessionState.BUILD

                from tools.coding.code_assistant import CodeAssistant
                assistant = CodeAssistant()
                task_prompt = self.original_command or (self.brief.company_name if self.brief else "Website Build")
                target_dir = self.session_dir if self.session_dir else None
                code, path, status = assistant.generate_code(task_prompt, project_dir=target_dir, brief=self.brief)


                if status == "FAILED" or "Error" in str(code):
                    self.state = WebsiteSessionState.BUILD_FAILED
                    return f"Boss, website build process mein issue aa gaya hai: {code}\nKya main naye specifications se try karoon?"

                self.state = WebsiteSessionState.BROWSER_QA
                self.state = WebsiteSessionState.COMPLETED
                return f"Done Boss! Website successfully generate and preview build launch ho chuki hai."
            else:
                self.state = WebsiteSessionState.EDITING_BRIEF
                local_session.add_user_message(user_input)

                self.state = WebsiteSessionState.ANALYZING_BRIEF
                self.brief = ClientBriefParser.parse_local_client_session(local_session)
                self.state = WebsiteSessionState.BRIEF_READY
                self.state = WebsiteSessionState.WAITING_FOR_APPROVAL

                summary = local_session.get_pre_build_summary(self.brief)
                return (
                    "Got it Boss. Details updated.\n\n"
                    f"{summary}\n\n"
                    "Boss, updated brief ready hai. Website bana du?"
                )

        elif self.state == WebsiteSessionState.BUILD_FAILED:
            self.state = WebsiteSessionState.EDITING_BRIEF
            local_session.add_user_message(user_input)
            self.brief = ClientBriefParser.parse_local_client_session(local_session)
            self.state = WebsiteSessionState.WAITING_FOR_APPROVAL
            summary = local_session.get_pre_build_summary(self.brief)
            return f"Brief update kar diya hai:\n\n{summary}\n\nAb retry karke website bana du?"

        return self.start_brief_collection(user_input)

