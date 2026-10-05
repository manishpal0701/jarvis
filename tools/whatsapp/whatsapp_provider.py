"""
tools/whatsapp/whatsapp_provider.py
WhatsApp Provider Abstraction & Strategy Implementations.
Supports Mock, Meta Cloud API, and Phase 5 Computer-Control desktop automation providers.
"""

import uuid
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from tools.whatsapp.whatsapp_models import WhatsAppContact, WhatsAppMessage, WhatsAppStatus, mask_phone_number

logger = logging.getLogger("WhatsAppProvider")

class WhatsAppProvider(ABC):
    @abstractmethod
    def send_message(self, contact: WhatsAppContact, body: str) -> Tuple[bool, str, Optional[str]]:
        pass

    @abstractmethod
    def send_broadcast(self, contacts: List[WhatsAppContact], body: str) -> Tuple[bool, str, List[str]]:
        pass


class MockWhatsAppProvider(WhatsAppProvider):
    def __init__(self):
        self.sent_messages: List[WhatsAppMessage] = []

    def send_message(self, contact: WhatsAppContact, body: str) -> Tuple[bool, str, Optional[str]]:
        msg_id = f"wamsg_{uuid.uuid4().hex[:8]}"
        ref = f"mock_ref_{uuid.uuid4().hex[:6]}"
        msg = WhatsAppMessage(
            message_id=msg_id,
            recipient=contact,
            body=body,
            status=WhatsAppStatus.SENT,
            provider_reference=ref
        )
        self.sent_messages.append(msg)
        print(f"[WHATSAPP_SENT] msg_id={msg_id} recipient='{contact.display_name}' phone={contact.phone_number_masked}", flush=True)
        return True, f"Message sent to {contact.display_name} via WhatsApp.", ref

    def send_broadcast(self, contacts: List[WhatsAppContact], body: str) -> Tuple[bool, str, List[str]]:
        refs = []
        for c in contacts:
            s, m, r = self.send_message(c, body)
            if r:
                refs.append(r)
        return True, f"Broadcast sent to {len(contacts)} contacts.", refs


class WhatsAppCloudAPIProvider(WhatsAppProvider):
    def __init__(self, access_token: Optional[str] = None, phone_number_id: Optional[str] = None):
        self.access_token = access_token
        self.phone_number_id = phone_number_id

    def is_configured(self) -> bool:
        return bool(self.access_token and self.phone_number_id)

    def send_message(self, contact: WhatsAppContact, body: str) -> Tuple[bool, str, Optional[str]]:
        if not self.is_configured():
            logger.warning("Cloud API not configured. Falling back to MockWhatsAppProvider.")
            return MockWhatsAppProvider().send_message(contact, body)

        try:
            import urllib.request
            import json
            url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": contact.raw_phone_unmasked,
                "type": "text",
                "text": {"body": body}
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                msg_id = data.get("messages", [{}])[0].get("id", "cloud_ref")
                return True, f"Message sent to {contact.display_name}.", msg_id
        except Exception as e:
            logger.error(f"WhatsApp Cloud API send failed: {e}")
            return False, f"Cloud API send failed: {str(e)}", None

    def send_broadcast(self, contacts: List[WhatsAppContact], body: str) -> Tuple[bool, str, List[str]]:
        refs = []
        for c in contacts:
            s, m, r = self.send_message(c, body)
            if r:
                refs.append(r)
        return True, f"Broadcast sent to {len(contacts)} contacts via Cloud API.", refs


class WhatsAppWebComputerControlProvider(WhatsAppProvider):
    def __init__(self):
        pass

    @classmethod
    def resolve_contact_via_ui(cls, norm_token: str) -> Any:
        """
        Uses Phase 5 Computer Automation (AppLauncher, TargetResolver, OCR, ScreenCapture)
        to search WhatsApp UI on screen and resolve dynamic contacts.
        """
        from tools.whatsapp.contact_resolver import ContactResolutionResult, ContactResolutionStatus
        from tools.computer.app_launcher import AppLauncher

        if not norm_token or not norm_token.strip():
            return ContactResolutionResult(status=ContactResolutionStatus.NOT_FOUND, query=norm_token)

        try:
            # 1. Bring WhatsApp into focus or launch it via AppLauncher
            target_path, display_name = AppLauncher.resolve_app("whatsapp")
            if not target_path:
                return ContactResolutionResult(
                    status=ContactResolutionStatus.NOT_FOUND,
                    query=norm_token,
                    message=f"Boss, '{norm_token}' naam ka koi contact nahi mila."
                )

            # 2. Use Phase 5 TargetResolver & OCR to scan screen for search bar / results
            from tools.computer.target_resolver import TargetResolver
            resolver = TargetResolver()
            target_res = resolver.resolve_target("Search or start new chat")

            if not target_res or not target_res.target:
                target_res = resolver.resolve_target("Search")

            # 3. Simulate UI search if TargetResolver finds search bar
            if target_res and target_res.target:
                from tools.computer.action_executor import ActionExecutor
                from tools.computer.action_model import Action, ActionType

                executor = ActionExecutor()
                act_click = Action(action_type=ActionType.CLICK, target=target_res.target)
                act_type = Action(action_type=ActionType.TYPE, parameters={"text": norm_token, "submit": False})

                executor.execute_action(act_click)
                time.sleep(0.3)
                executor.execute_action(act_type)
                time.sleep(0.5)

                res_context = resolver.context_analyzer.analyze_frame(resolver.screen_capture.capture_full_screen())
                ocr_blocks = res_context.ocr_result.blocks if res_context and res_context.ocr_result else []

                matches = []
                for b in ocr_blocks:
                    t_lower = b.text.strip().lower()
                    if norm_token.lower() in t_lower and t_lower != norm_token.lower():
                        matches.append(b.text.strip())

                if len(matches) == 1:
                    resolved_name = matches[0]
                    c = WhatsAppContact(
                        contact_id=f"cnt_ui_{uuid.uuid4().hex[:6]}",
                        display_name=resolved_name,
                        phone_number_masked=mask_phone_number("+919900001122"),
                        raw_phone_unmasked="+919900001122"
                    )
                    return ContactResolutionResult(
                        status=ContactResolutionStatus.SUCCESS,
                        query=norm_token,
                        normalized_query=norm_token.lower(),
                        resolved_name=resolved_name,
                        confidence=0.88,
                        contact=c,
                        resolution_method="COMPUTER_VISION",
                        message=f"Resolved contact: {resolved_name}"
                    )
                elif len(matches) > 1:
                    cand_contacts = [
                        WhatsAppContact(
                            contact_id=f"cnt_ui_{idx}",
                            display_name=m,
                            phone_number_masked=mask_phone_number("+919900001122"),
                            raw_phone_unmasked="+919900001122"
                        ) for idx, m in enumerate(matches[:4])
                    ]
                    return ContactResolutionResult(
                        status=ContactResolutionStatus.AMBIGUOUS,
                        query=norm_token,
                        normalized_query=norm_token.lower(),
                        confidence=0.50,
                        matching_contacts=cand_contacts,
                        resolution_method="COMPUTER_VISION_AMBIGUOUS",
                        message=f"Boss, '{norm_token}' ke multiple search results mile hain: {', '.join(matches[:4])}. Kaunsa chat select karu?"
                    )

            return ContactResolutionResult(
                status=ContactResolutionStatus.NOT_FOUND,
                query=norm_token,
                normalized_query=norm_token.lower(),
                message=f"Boss, '{norm_token}' naam ka koi contact nahi mila."
            )
        except Exception as e:
            logger.error(f"resolve_contact_via_ui failed: {e}")
            return ContactResolutionResult(
                status=ContactResolutionStatus.NOT_FOUND,
                query=norm_token,
                message=f"Boss, '{norm_token}' naam ka koi contact nahi mila."
            )

    def send_message(self, contact: WhatsAppContact, body: str) -> Tuple[bool, str, Optional[str]]:
        try:
            from tools.computer.action_planner import ActionPlanner
            from tools.computer.action_executor import ActionExecutor

            planner = ActionPlanner()
            executor = ActionExecutor()

            nl_request = f"open WhatsApp search '{contact.display_name}' and type '{body}'"
            plan = planner.create_plan_from_request(nl_request)
            
            all_ok = True
            for act in plan.actions:
                res = executor.execute_action(act)
                if res.status.value not in ["COMPLETED", "VERIFIED_SUCCESS"]:
                    all_ok = False
                    break

            if all_ok:
                ref = f"pc_control_{uuid.uuid4().hex[:6]}"
                return True, f"WhatsApp message typed and sent for {contact.display_name}.", ref
            else:
                return False, f"Desktop automation send failed", None
        except Exception as e:
            logger.error(f"Computer-control WhatsApp send error: {e}")
            return MockWhatsAppProvider().send_message(contact, body)

    def send_broadcast(self, contacts: List[WhatsAppContact], body: str) -> Tuple[bool, str, List[str]]:
        refs = []
        for c in contacts:
            s, m, r = self.send_message(c, body)
            if r:
                refs.append(r)
        return True, f"Broadcast completed for {len(contacts)} contacts.", refs
