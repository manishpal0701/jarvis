"""
tools/whatsapp/whatsapp_service.py
High-level WhatsApp Service for JARVIS WhatsApp Agent.
Manages provider strategy selection and active WhatsApp context state.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from tools.whatsapp.whatsapp_models import WhatsAppContact, WhatsAppMessage, WhatsAppStatus
from tools.whatsapp.whatsapp_provider import WhatsAppProvider, MockWhatsAppProvider, WhatsAppCloudAPIProvider, WhatsAppWebComputerControlProvider
from tools.whatsapp.contact_resolver import ContactResolver, ContactResolutionResult, ContactResolutionStatus
from tools.whatsapp.message_composer import WhatsAppMessageComposer
from tools.whatsapp.whatsapp_confirmation import WhatsAppConfirmationManager
from conversation.conversation_manager import ConversationManager

logger = logging.getLogger("WhatsAppService")

class WhatsAppService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = WhatsAppService()
        return cls._instance

    def __init__(self):
        self.provider: WhatsAppProvider = MockWhatsAppProvider()
        self.resolver = ContactResolver.get_instance()
        self.conf_mgr = WhatsAppConfirmationManager.get_instance()
        self.active_contact: Optional[WhatsAppContact] = None
        self.active_body: Optional[str] = None

    def set_provider(self, provider: WhatsAppProvider):
        self.provider = provider

    def is_provider_available(self) -> bool:
        if hasattr(self.provider, "is_available"):
            return self.provider.is_available()
        return True

    def process_whatsapp_request(self, nl_request: str, request_id: str = "req_default") -> str:
        if not self.is_provider_available():
            return "Boss, WhatsApp contact service abhi available nahi hai."

        recipient_query, body_candidate = WhatsAppMessageComposer.parse_nl_request(nl_request)

        # Check follow-up context ("usko hello bhejo" or empty recipient query)
        is_usko = any(w in recipient_query.lower().split() for w in ["usko", "us", "unko", "him", "her", "them"]) if recipient_query else False

        if (not recipient_query or is_usko) and self.active_contact:
            res = ContactResolutionResult(
                status=ContactResolutionStatus.SUCCESS,
                query="usko",
                normalized_query=self.active_contact.display_name.lower(),
                resolved_name=self.active_contact.display_name,
                phone_number=self.active_contact.phone_number_masked,
                confidence=1.0,
                contact=self.active_contact,
                resolution_method="CONTEXT"
            )
        else:
            search_target = recipient_query if recipient_query else nl_request
            res = self.resolver.resolve_contact(search_target)

        if res.is_ambiguous:
            return res.message

        if res.status in [ContactResolutionStatus.CONTACT_NOT_FOUND, ContactResolutionStatus.NOT_FOUND, ContactResolutionStatus.AUTH_REQUIRED, ContactResolutionStatus.PROVIDER_UNAVAILABLE, ContactResolutionStatus.FAILED]:
            return res.message

        if res.success and res.contact:
            self.active_contact = res.contact

            if not body_candidate:
                return f"Boss, {res.contact.display_name} ko kaunsa message bhejna hai?"

            self.active_body = body_candidate
            desc = f"WhatsApp message for {res.contact.display_name}"
            ConversationManager.get_instance().set_active_context(entity=desc)

            prompt, _ = self.conf_mgr.register_pending_message(
                request_id=request_id,
                recipients=[res.contact],
                body=body_candidate
            )
            return prompt

        if self.active_contact and body_candidate:
            self.active_body = body_candidate
            prompt, _ = self.conf_mgr.register_pending_message(
                request_id=request_id,
                recipients=[self.active_contact],
                body=body_candidate
            )
            return prompt

        return res.message or "Boss, kisse WhatsApp message bhejna hai aur kya likhna hai?"

    def execute_confirmed_action(self, user_input: str) -> str:
        pending = self.conf_mgr.get_pending_action()
        if not pending:
            return "Boss, koi WhatsApp message confirmation ke liye pending nahi hai."

        from tools.computer.confirmation_manager import ConfirmationManager
        c_mgr = ConfirmationManager.get_instance()

        if c_mgr.is_negative_response(user_input):
            self.conf_mgr.clear()
            return "Boss, WhatsApp message cancel kar diya gaya hai."

        if c_mgr.is_affirmative_response(user_input):
            if pending.is_broadcast:
                success, msg, refs = self.provider.send_broadcast(pending.recipients, pending.body)
            else:
                success, msg, ref = self.provider.send_message(pending.recipients[0], pending.body)

            self.conf_mgr.clear()
            return f"Boss, {msg}" if success else f"Boss, WhatsApp send fail ho gaya: {msg}"

        return "Boss, kripya 'Haan' bol kar confirm karein ya 'Nahi' bol kar cancel karein."
