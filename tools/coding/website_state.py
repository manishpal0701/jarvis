import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class ActiveWebsiteState:
    project_name: str = ""
    output_directory: str = ""
    local_url: str = ""
    port: int = 0
    temporary_public_url: str = ""
    permanent_public_url: str = ""
    hosting_provider: str = "vercel"
    hosting_status: str = "not_deployed"  # 'not_deployed', 'auth_required', 'deployed', 'failed'
    build_status: str = "running"
    validation_status: str = "running"
    preview_status: str = "not_started"
    visual_qa_status: str = "not_started"
    dependency_validation_passed: bool = False
    build_passed: bool = False
    preview_running: bool = False
    http_status_ok: bool = False
    visual_qa_passed: bool = False
    responsive_passed: bool = False
    visual_qa_score: str = "0/20"
    console_errors: int = 0
    broken_images: int = 0
    repair_attempts: int = 0
    last_error: str = ""

    def is_authoritative_ready(self) -> bool:
        """
        Calculates authoritative website readiness.
        WEBSITE READY is mathematically impossible if ANY single gate fails.
        """
        return (
            self.dependency_validation_passed is True and
            self.build_passed is True and
            self.preview_running is True and
            self.http_status_ok is True and
            self.visual_qa_status == "passed" and
            self.visual_qa_passed is True and
            self.responsive_passed is True and
            self.console_errors == 0 and
            self.broken_images == 0
        )

    @property
    def website_ready(self) -> bool:
        return self.is_authoritative_ready()

    @website_ready.setter
    def website_ready(self, val: bool):
        # Setting website_ready to True is only allowed if authoritative check passes
        if val and not self.is_authoritative_ready():
            pass # Suppress setting True when upstream gates fail

    def invalidate_downstream(self, failed_gate: str):
        """
        Invalidates all downstream pipeline gates whenever an upstream gate fails.
        """
        if failed_gate in ["dependency", "build", "preview", "http", "visual_qa", "syntax", "timeout", "reset"]:
            self.visual_qa_passed = False
            self.visual_qa_status = "failed"
            self.responsive_passed = False
            self.visual_qa_score = "0/20"
        if failed_gate in ["dependency", "build", "preview", "http", "syntax", "timeout", "reset"]:
            self.http_status_ok = False
            self.preview_running = False
            self.preview_status = "failed"
        if failed_gate in ["dependency", "build", "syntax", "timeout", "reset"]:
            self.build_passed = False
            self.build_status = "failed"
        if failed_gate in ["dependency", "syntax", "timeout", "reset"]:
            self.dependency_validation_passed = False
            self.validation_status = "failed"

class WebsiteStateManager:
    """
    Website State Manager Singleton.
    Tracks currently active website session across generation, local preview,
    temporary public share links, and permanent hosting deployment.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WebsiteStateManager, cls).__new__(cls)
                cls._instance._active_state: Optional[ActiveWebsiteState] = None
            return cls._instance

    @classmethod
    def get_instance(cls):
        return cls()

    def set_active_website(self, state: ActiveWebsiteState):
        with self._lock:
            self._active_state = state

    def reset_active_website(self, project_name: str = "", output_directory: str = ""):
        with self._lock:
            self._active_state = ActiveWebsiteState(
                project_name=project_name,
                output_directory=output_directory,
                local_url="",
                port=0,
                temporary_public_url="",
                permanent_public_url="",
                hosting_provider="vercel",
                hosting_status="not_deployed",
                build_status="running",
                validation_status="running",
                preview_status="not_started",
                visual_qa_status="not_started",
                dependency_validation_passed=False,
                build_passed=False,
                preview_running=False,
                http_status_ok=False,
                visual_qa_passed=False,
                responsive_passed=False,
                visual_qa_score="0/20",
                console_errors=0,
                broken_images=0,
                repair_attempts=0,
                last_error=""
            )

    def get_active_website(self) -> Optional[ActiveWebsiteState]:
        with self._lock:
            return self._active_state

    def update_temporary_url(self, public_url: str):
        with self._lock:
            if self._active_state:
                self._active_state.temporary_public_url = public_url

    def update_permanent_url(self, public_url: str, status: str = "deployed"):
        with self._lock:
            if self._active_state:
                self._active_state.permanent_public_url = public_url
                self._active_state.hosting_status = status

    def clear(self):
        with self._lock:
            self._active_state = None

