"""
tools/email/email_formatter.py
Conversational Response Formatter for JARVIS Email Agent.
"""

from typing import List
from tools.email.email_models import EmailMessage, EmailSearchResult, mask_email_secrets

class EmailFormatter:
    @staticmethod
    def format_email_list(result: EmailSearchResult) -> str:
        if not result.messages:
            return "Boss, aapki search ke mutabiq koi emails nahi mile."

        count = len(result.messages)
        lines = [f"Boss, aapke {count} emails hain:"]
        for idx, msg in enumerate(result.messages, 1):
            sender_clean = mask_email_secrets(msg.sender.split("<")[0].strip()) or msg.sender
            subj_clean = mask_email_secrets(msg.subject)
            unread_str = " (Unread)" if msg.is_unread else ""
            lines.append(f"{idx}. From {sender_clean}: '{subj_clean}'{unread_str}")

        return "\n".join(lines)

    @staticmethod
    def format_single_email(msg: EmailMessage) -> str:
        sender_clean = mask_email_secrets(msg.sender)
        subj_clean = mask_email_secrets(msg.subject)
        snippet_clean = mask_email_secrets(msg.snippet)
        return (
            f"Boss, email details:\n"
            f"From: {sender_clean}\n"
            f"Subject: {subj_clean}\n"
            f"Content: {snippet_clean or msg.body[:200]}"
        )

    @staticmethod
    def format_email_summary(msg: EmailMessage) -> str:
        sender_clean = mask_email_secrets(msg.sender.split("<")[0].strip()) or msg.sender
        subj_clean = mask_email_secrets(msg.subject)
        body_snippet = mask_email_secrets(msg.body[:300])

        return (
            f"Boss, {sender_clean} ka email '{subj_clean}' subject ke baare me hai.\n"
            f"Summary: {body_snippet}\n"
            f"Aap chahen toh iska reply draft kar sakta hoon."
        )
