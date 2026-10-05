"""
tools/whatsapp/whatsapp_confirmation.py
Safety & Confirmation Integration for JARVIS WhatsApp Agent.
Integrates HIGH-risk message dispatches and multi-recipient broadcasts
with the central ConfirmationManager.
"""

import time
import logging
from typing import Any, Dict, List, Optional, Tuple

from tools.computer.confirmation_manager import ConfirmationManager
from tools.whatsapp.whatsapp_models import WhatsAppContact

logger = logging.getLogger("WhatsAppConfirmation")

class PendingWhatsAppAction:
    def __init__(
        self,
        request_id: str,
        recipients: List[WhatsAppContact],
        body: str,
        is_broadcast: bool = False
    ):
        self.request_id = request_id
        self.recipients = recipients
        self.body = body
        self.is_broadcast = is_broadcast
        self.created_at = time.time()


class WhatsAppConfirmationManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = WhatsAppConfirmationManager()
        return cls._instance

    def __init__(self):
        self._pending: Optional[PendingWhatsAppAction] = None

    def register_pending_message(
        self,
        request_id: str,
        recipients: List[WhatsAppContact],
        body: str
    ) -> Tuple[str, PendingWhatsAppAction]:
        is_broadcast = len(recipients) > 1
        pending = PendingWhatsAppAction(
            request_id=request_id,
            recipients=recipients,
            body=body,
            is_broadcast=is_broadcast
        )
        self._pending = pending

        if is_broadcast:
            prompt = f"Boss, ye message {len(recipients)} contacts ko send hoga:\n\"{body}\"\nConfirm karu?"
        else:
            c = recipients[0]
            prompt = f"Boss, {c.display_name} ({c.phone_number_masked}) ko ye WhatsApp message send karu?\n\"{body}\""

        conf_mgr = ConfirmationManager.get_instance()
        conf_mgr.register_pending_confirmation(request_id, None, None, prompt)

        print(f"[WHATSAPP_CONFIRMATION_REGISTERED] req_id={request_id} count={len(recipients)} prompt='{prompt[:60]}'", flush=True)
        return prompt, pending

    def has_pending_confirmation(self) -> bool:
        if self._pending is None:
            return False
        if time.time() - self._pending.created_at > 120.0:
            self.clear()
            return False
        return True

    def get_pending_action(self) -> Optional[PendingWhatsAppAction]:
        if self.has_pending_confirmation():
            return self._pending
        return None

    def clear(self):
        self._pending = None
        ConfirmationManager.get_instance().clear()
