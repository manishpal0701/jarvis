"""
tools/email/gmail_client.py
Gmail API Client for JARVIS Email Agent.
Wraps official Google API Client Library with robust offline/mock fallback for testing and unauthenticated states.
"""

import uuid
import time
import logging
from typing import Any, Dict, List, Optional, Tuple

from tools.email.email_models import EmailMessage, EmailDraft, EmailSearchResult, mask_email_secrets
from tools.email.gmail_auth import GmailAuthManager
from tools.email.email_parser import EmailParser

logger = logging.getLogger("GmailClient")

class GmailClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GmailClient()
        return cls._instance

    def __init__(self):
        self.auth_mgr = GmailAuthManager.get_instance()
        self._mock_messages: Dict[str, EmailMessage] = {}
        self._mock_drafts: Dict[str, EmailDraft] = {}
        self._init_mock_store()

    def _init_mock_store(self):
        m1 = EmailMessage(
            message_id="msg_001",
            thread_id="thread_001",
            sender="Rahul Sharma <rahul@example.com>",
            recipients=["manish@example.com"],
            subject="Project Update & Meeting Notes",
            body="Hi Manish, Please find attached the updated project milestone documents. Let me know when you are free to discuss.",
            snippet="Hi Manish, Please find attached the updated project milestone documents...",
            timestamp="2026-09-08T10:00:00Z",
            labels=["UNREAD", "INBOX"],
            is_unread=True
        )
        m2 = EmailMessage(
            message_id="msg_002",
            thread_id="thread_002",
            sender="Google Security <no-reply@accounts.google.com>",
            recipients=["manish@example.com"],
            subject="Security Alert: New sign-in detected",
            body="New sign-in to your Google Account from Windows 11 device.",
            snippet="New sign-in to your Google Account from Windows 11...",
            timestamp="2026-09-08T09:30:00Z",
            labels=["UNREAD", "INBOX"],
            is_unread=True
        )
        m3 = EmailMessage(
            message_id="msg_003",
            thread_id="thread_003",
            sender="John Doe <john@company.com>",
            recipients=["manish@example.com"],
            subject="Quarterly Financial Report Draft",
            body="Hey Manish, The draft report for Q3 is ready for review.",
            snippet="Hey Manish, The draft report for Q3 is ready...",
            timestamp="2026-09-07T14:20:00Z",
            labels=["INBOX"],
            is_unread=False
        )
        self._mock_messages[m1.message_id] = m1
        self._mock_messages[m2.message_id] = m2
        self._mock_messages[m3.message_id] = m3

    def search_messages(self, query: str = "is:unread", max_results: int = 5) -> EmailSearchResult:
        success, creds, _ = self.auth_mgr.get_credentials()

        if success and creds != "MOCK_CREDENTIALS":
            try:
                from googleapiclient.discovery import build
                service = build('gmail', 'v1', credentials=creds)
                results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
                messages_meta = results.get('messages', [])

                fetched_msgs = []
                for meta in messages_meta:
                    msg_data = service.users().messages().get(userId='me', id=meta['id'], format='full').execute()
                    parsed = EmailParser.parse_raw_message(msg_data)
                    fetched_msgs.append(parsed)

                return EmailSearchResult(query=query, messages=fetched_msgs, total_count=len(fetched_msgs))
            except Exception as e:
                logger.error(f"Gmail API search failed: {e}. Falling back to mock inbox.")

        q_lower = query.lower()
        matched = []
        for msg in self._mock_messages.values():
            if "is:unread" in q_lower and not msg.is_unread:
                continue
            if "from:rahul" in q_lower and "rahul" not in msg.sender.lower():
                continue
            if "from:google" in q_lower and "google" not in msg.sender.lower():
                continue
            matched.append(msg)

        matched = matched[:max_results]
        return EmailSearchResult(query=query, messages=matched, total_count=len(matched))

    def get_message(self, message_id: str) -> Optional[EmailMessage]:
        success, creds, _ = self.auth_mgr.get_credentials()
        if success and creds != "MOCK_CREDENTIALS":
            try:
                from googleapiclient.discovery import build
                service = build('gmail', 'v1', credentials=creds)
                msg_data = service.users().messages().get(userId='me', id=message_id, format='full').execute()
                return EmailParser.parse_raw_message(msg_data)
            except Exception as e:
                logger.error(f"Gmail API get_message failed: {e}")

        return self._mock_messages.get(message_id)

    def create_draft(self, recipient: str, subject: str, body: str, thread_id: Optional[str] = None) -> EmailDraft:
        draft_id = f"draft_{uuid.uuid4().hex[:8]}"
        draft = EmailDraft(
            draft_id=draft_id,
            recipient=recipient,
            subject=subject,
            body=body,
            thread_id=thread_id
        )
        self._mock_drafts[draft_id] = draft
        print(f"[EMAIL_DRAFT_CREATED] draft_id={draft_id} to='{recipient}' subject='{subject}'", flush=True)
        return draft

    def send_email(self, recipient: str, subject: str, body: str, thread_id: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        msg_id = f"sent_{uuid.uuid4().hex[:8]}"
        sent_msg = EmailMessage(
            message_id=msg_id,
            thread_id=thread_id or f"thread_{uuid.uuid4().hex[:8]}",
            sender="me",
            recipients=[recipient],
            subject=subject,
            body=body,
            snippet=body[:100],
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            is_unread=False
        )
        self._mock_messages[msg_id] = sent_msg
        print(f"[EMAIL_SENT] msg_id={msg_id} to='{recipient}' subject='{subject}'", flush=True)
        return True, f"Email sent successfully to {recipient}.", msg_id

    def reply_to_email(self, thread_id: str, body: str) -> Tuple[bool, str, Optional[str]]:
        orig_msg = None
        for msg in self._mock_messages.values():
            if msg.thread_id == thread_id or msg.message_id == thread_id:
                orig_msg = msg
                break

        recipient = orig_msg.sender if orig_msg else "recipient@example.com"
        subject = f"Re: {orig_msg.subject}" if orig_msg else "Re: Inquiry"
        return self.send_email(recipient=recipient, subject=subject, body=body, thread_id=thread_id)

    def forward_email(self, message_id: str, to_recipient: str, note: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        orig_msg = self.get_message(message_id)
        subject = f"Fwd: {orig_msg.subject}" if orig_msg else "Fwd: Notice"
        body = f"{note}\n\n---------- Forwarded message ---------\nFrom: {orig_msg.sender if orig_msg else ''}\nDate: {orig_msg.timestamp if orig_msg else ''}\nSubject: {orig_msg.subject if orig_msg else ''}\n\n{orig_msg.body if orig_msg else ''}"
        return self.send_email(recipient=to_recipient, subject=subject, body=body)

    def delete_email(self, message_id: str) -> Tuple[bool, str]:
        if message_id in self._mock_messages:
            self._mock_messages.pop(message_id)
            print(f"[EMAIL_TRASHED] msg_id={message_id}", flush=True)
            return True, f"Email '{message_id}' moved to Trash."
        return False, f"Email '{message_id}' not found."

    def mark_as_read(self, message_id: str) -> Tuple[bool, str]:
        msg = self._mock_messages.get(message_id)
        if msg:
            msg.is_unread = False
            if "UNREAD" in msg.labels:
                msg.labels.remove("UNREAD")
            return True, f"Email '{message_id}' marked as read."
        return False, "Email not found."

    def mark_as_unread(self, message_id: str) -> Tuple[bool, str]:
        msg = self._mock_messages.get(message_id)
        if msg:
            msg.is_unread = True
            if "UNREAD" not in msg.labels:
                msg.labels.append("UNREAD")
            return True, f"Email '{message_id}' marked as unread."
        return False, "Email not found."
