"""
tools/email/email_service.py
High-level Email Service for JARVIS Email Agent.
Manages active email context state for Phase 1 follow-up resolution ("isko summarize karo", "iska reply draft karo").
"""

import logging
from typing import Any, Dict, Optional, Tuple

from tools.email.email_models import EmailMessage, EmailDraft, EmailSearchResult, EmailStatus
from tools.email.gmail_client import GmailClient
from tools.email.email_search import EmailSearchQueryTranslator
from tools.email.email_formatter import EmailFormatter
from tools.email.email_confirmation import EmailConfirmationManager
from conversation.conversation_manager import ConversationManager

logger = logging.getLogger("EmailService")

class EmailService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = EmailService()
        return cls._instance

    def __init__(self):
        self.client = GmailClient.get_instance()
        self.conf_mgr = EmailConfirmationManager.get_instance()
        self.active_message: Optional[EmailMessage] = None
        self.active_draft: Optional[EmailDraft] = None

    def search_and_format(self, nl_query: str) -> str:
        gmail_query, max_res = EmailSearchQueryTranslator.translate_nl_request(nl_query)
        result = self.client.search_messages(query=gmail_query, max_results=max_res)

        if result.messages:
            self.active_message = result.messages[0]
            desc = f"email from {self.active_message.sender} regarding {self.active_message.subject}"
            ConversationManager.get_instance().set_active_context(entity=desc)

        return EmailFormatter.format_email_list(result)

    def read_email(self, message_id: str = None) -> str:
        msg = self.client.get_message(message_id) if message_id else self.active_message
        if not msg:
            return "Boss, koi select kiya hua email nahi mila."

        self.active_message = msg
        desc = f"email from {msg.sender} regarding {msg.subject}"
        ConversationManager.get_instance().set_active_context(entity=desc)
        return EmailFormatter.format_single_email(msg)

    def summarize_email(self, message_id: str = None) -> str:
        msg = self.client.get_message(message_id) if message_id else self.active_message
        if not msg:
            return "Boss, summarize karne ke liye koi email context me nahi hai."

        self.active_message = msg
        return EmailFormatter.format_email_summary(msg)

    def create_draft_reply(self, recipient: str = None, body: str = None, request_id: str = None) -> str:
        target_msg = self.active_message
        to_addr = recipient or (target_msg.sender if target_msg else "recipient@example.com")
        subject = f"Re: {target_msg.subject}" if target_msg else "Re: Project Update"
        reply_body = body or "Thank you for the update. I have reviewed the details and will get back to you shortly."

        draft = self.client.create_draft(recipient=to_addr, subject=subject, body=reply_body, thread_id=target_msg.thread_id if target_msg else None)
        self.active_draft = draft
        desc = f"draft reply to {to_addr} for email {subject}"
        ConversationManager.get_instance().set_active_context(entity=desc)

        return f"Boss, {to_addr} ke liye draft tayyar kar diya hai.\nSubject: {subject}\nBody: '{reply_body[:120]}'\n(Note: Email send nahi hua hai. Send karne ke liye 'send kar do' bolein.)"

    def prepare_send(self, recipient: str = None, subject: str = None, body: str = None, request_id: str = "req_default") -> str:
        to_addr = recipient
        subj = subject
        content = body

        if self.active_draft and not to_addr:
            to_addr = self.active_draft.recipient
            subj = self.active_draft.subject
            content = self.active_draft.body
        elif self.active_message and not to_addr:
            to_addr = self.active_message.sender
            subj = f"Re: {self.active_message.subject}"
            content = "Thank you for the update."

        to_addr = to_addr or "recipient@example.com"
        subj = subj or "JARVIS Update"
        content = content or "Hello, this is an automated message from JARVIS."

        prompt, _ = self.conf_mgr.register_pending_email(
            request_id=request_id,
            action_type="SEND",
            recipient=to_addr,
            subject=subj,
            body=content,
            thread_id=self.active_message.thread_id if self.active_message else None
        )
        return prompt

    def execute_confirmed_action(self, user_input: str) -> str:
        pending = self.conf_mgr.get_pending_email()
        if not pending:
            return "Boss, koi email action confirmation ke liye pending nahi hai."

        from tools.computer.confirmation_manager import ConfirmationManager
        c_mgr = ConfirmationManager.get_instance()

        if c_mgr.is_negative_response(user_input):
            self.conf_mgr.clear()
            return "Boss, email action cancel kar diya gaya hai."

        if c_mgr.is_affirmative_response(user_input):
            a_type = pending.action_type
            if a_type == "DELETE":
                success, msg = self.client.delete_email(pending.target_msg_id or "msg_001")
            elif a_type == "REPLY":
                success, msg, _ = self.client.reply_to_email(pending.thread_id or "thread_001", pending.body)
            elif a_type == "FORWARD":
                success, msg, _ = self.client.forward_email(pending.target_msg_id or "msg_001", pending.recipient, pending.body)
            else:
                success, msg, _ = self.client.send_email(pending.recipient, pending.subject, pending.body, pending.thread_id)

            self.conf_mgr.clear()
            return f"Boss, {msg}" if success else f"Boss, email operation fail ho gaya: {msg}"

        return "Boss, kripya 'Haan' bol kar confirm karein ya 'Nahi' bol kar cancel karein."
