"""
tools/computer/confirmation_manager.py
Confirmation Manager for JARVIS Phase 5 Safety System.
Tracks pending high-risk action confirmations bound to request_id and action_id.
"""

import time
import re
import logging
from typing import Any, Dict, Optional
from tools.computer.action_model import Action, ActionPlan

logger = logging.getLogger("ConfirmationManager")

AFFIRMATIVE_TERMS = [
    "yes", "haan", "ha", "confirm", "proceed", "do it", "approve", "ok", "okay",
    "sure", "haan kar do", "haan karo", "delete kar do", "kar do"
]

NEGATIVE_TERMS = [
    "no", "nahi", "nhi", "nahin", "na", "naa", "cancel", "stop", "mat karo", "abort", "don't"
]


class PendingConfirmation:
    def __init__(self, request_id: str, plan: Optional[ActionPlan], action: Optional[Action], prompt: str):
        self.request_id = request_id
        self.plan = plan
        self.action = action
        self.prompt = prompt
        self.created_at = time.time()


class ConfirmationManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ConfirmationManager()
        return cls._instance

    def __init__(self):
        self._pending: Optional[PendingConfirmation] = None

    def register_pending_confirmation(
        self,
        request_id: str,
        plan: Optional[ActionPlan],
        action: Optional[Action],
        prompt: str
    ) -> PendingConfirmation:
        """Registers a pending safety confirmation request."""
        pending = PendingConfirmation(request_id, plan, action, prompt)
        self._pending = pending
        print(f"[CONFIRMATION_REGISTERED] req_id={request_id} prompt='{prompt[:60]}...'", flush=True)
        return pending

    def has_pending_confirmation(self) -> bool:
        if self._pending is None:
            return False
        # Expire after 120 seconds
        if time.time() - self._pending.created_at > 120.0:
            self.clear()
            return False
        return True

    def get_pending_confirmation(self) -> Optional[PendingConfirmation]:
        if self.has_pending_confirmation():
            return self._pending
        return None

    def is_affirmative_response(self, user_input: str) -> bool:
        cmd_lower = re.sub(r"[^\w\s]", "", user_input.lower().strip())
        return any(term in cmd_lower.split() or cmd_lower.startswith(f"{term} ") or cmd_lower.endswith(f" {term}") for term in AFFIRMATIVE_TERMS)

    def is_negative_response(self, user_input: str) -> bool:
        cmd_lower = re.sub(r"[^\w\s]", "", user_input.lower().strip())
        return any(term in cmd_lower.split() or cmd_lower.startswith(f"{term} ") or cmd_lower.endswith(f" {term}") for term in NEGATIVE_TERMS)

    def clear(self):
        self._pending = None
