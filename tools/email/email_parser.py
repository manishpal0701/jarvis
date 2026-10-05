"""
tools/email/email_parser.py
Email Payload Parser for JARVIS Email Agent.
Extracts header info and content with strict length bounds (max 1500 chars).
"""

import base64
import logging
from typing import Any, Dict, List, Tuple
from tools.email.email_models import EmailMessage, mask_email_secrets

logger = logging.getLogger("EmailParser")

MAX_BODY_LENGTH = 1500

class EmailParser:
    @staticmethod
    def parse_raw_message(msg_payload: Dict[str, Any]) -> EmailMessage:
        msg_id = msg_payload.get("id", "")
        thread_id = msg_payload.get("threadId", "")
        snippet = msg_payload.get("snippet", "")
        label_ids = msg_payload.get("labelIds", [])
        is_unread = "UNREAD" in label_ids

        headers = msg_payload.get("payload", {}).get("headers", [])
        sender = ""
        recipients = []
        subject = "(No Subject)"
        date_str = ""
        cc = []
        bcc = []

        for h in headers:
            name = h.get("name", "").lower()
            val = h.get("value", "")
            if name == "from":
                sender = val
            elif name == "to":
                recipients = [r.strip() for r in val.split(",") if r.strip()]
            elif name == "subject":
                subject = val
            elif name == "date":
                date_str = val
            elif name == "cc":
                cc = [r.strip() for r in val.split(",") if r.strip()]
            elif name == "bcc":
                bcc = [r.strip() for r in val.split(",") if r.strip()]

        body = EmailParser._extract_body(msg_payload.get("payload", {}))
        if len(body) > MAX_BODY_LENGTH:
            body = body[:MAX_BODY_LENGTH] + "\n... [Truncated for brevity]"

        return EmailMessage(
            message_id=msg_id,
            thread_id=thread_id,
            sender=sender,
            recipients=recipients,
            subject=subject,
            body=body,
            snippet=snippet,
            timestamp=date_str,
            cc=cc,
            bcc=bcc,
            labels=label_ids,
            is_unread=is_unread
        )

    @staticmethod
    def _extract_body(payload: Dict[str, Any]) -> str:
        if not payload:
            return ""

        mime_type = payload.get("mimeType", "")
        body_data = payload.get("body", {}).get("data", "")

        if body_data:
            try:
                decoded = base64.urlsafe_b64decode(body_data.encode("ASCII")).decode("utf-8", errors="replace")
                return decoded.strip()
            except Exception:
                pass

        parts = payload.get("parts", [])
        for part in parts:
            part_mime = part.get("mimeType", "")
            if part_mime == "text/plain":
                part_data = part.get("body", {}).get("data", "")
                if part_data:
                    try:
                        return base64.urlsafe_b64decode(part_data.encode("ASCII")).decode("utf-8", errors="replace").strip()
                    except Exception:
                        pass
            elif part.get("parts"):
                res = EmailParser._extract_body(part)
                if res:
                    return res

        return ""
