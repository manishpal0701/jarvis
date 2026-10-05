"""
tools/email/email_confirmation.py
Safety & Confirmation Integration for JARVIS Email Agent.
Integrates HIGH-risk external side effects (SEND, REPLY, FORWARD, DELETE)
with the central ConfirmationManager.
"""

import time
import logging
from typing import Any, Dict, Optional, Tuple

from tools.computer.confirmation_manager import ConfirmationManager, PendingConfirmation
from tools.email.email_models import EmailRiskLevel

logger = logging.getLogger("EmailConfirmation")

class PendingEmailAction:
    def __init__(
        self,
        request_id: str,
        action_type: str,
        recipient: str,
        subject: str,
        body: str,
        target_msg_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ):
        self.request_id = request_id
        self.action_type = action_type
        self.recipient = recipient
        self.subject = subject
        self.body = body
        self.target_msg_id = target_msg_id
        self.thread_id = thread_id
        self.created_at = time.time()


class EmailConfirmationManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = EmailConfirmationManager()
        return cls._instance

    def __init__(self):
        self._pending_email: Optional[PendingEmailAction] = None

    def register_pending_email(
        self,
        request_id: str,
        action_type: str,
        recipient: str,
        subject: str,
        body: str,
        target_msg_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> Tuple[str, PendingEmailAction]:
        pending = PendingEmailAction(
            request_id=request_id,
            action_type=action_type,
            recipient=recipient,
            subject=subject,
            body=body,
            target_msg_id=target_msg_id,
            thread_id=thread_id
        )
        self._pending_email = pending

        if action_type == "DELETE":
            prompt = f"Boss, email '{target_msg_id or subject}' ko Trash me move karu?"
        elif action_type == "REPLY":
            prompt = f"Boss, {recipient} ko subject '{subject}' ke reply me ye message send karu?\nBody: '{body[:100]}'"
        elif action_type == "FORWARD":
            prompt = f"Boss, ye email {recipient} ko forward karu?"
        else:
            prompt = f"Boss, {recipient} ko subject '{subject}' ke saath ye email send karu?\nBody: '{body[:100]}'"

        conf_mgr = ConfirmationManager.get_instance()
        conf_mgr.register_pending_confirmation(request_id, None, None, prompt)

        print(f"[EMAIL_CONFIRMATION_REGISTERED] req_id={request_id} type={action_type} prompt='{prompt[:60]}'", flush=True)
        return prompt, pending

    def has_pending_confirmation(self) -> bool:
        if self._pending_email is None:
            return False
        if time.time() - self._pending_email.created_at > 120.0:
            self.clear()
            return False
        return True

    def get_pending_email(self) -> Optional[PendingEmailAction]:
        if self.has_pending_confirmation():
            return self._pending_email
        return None

    def clear(self):
        self._pending_email = None
        ConfirmationManager.get_instance().clear()
