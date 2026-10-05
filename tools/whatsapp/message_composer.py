"""
tools/whatsapp/message_composer.py
Natural Language WhatsApp Message Composer, Request Parser, and Preview Generator.
Separates recipient queries from message body payloads cleanly across Hinglish & English requests.
"""

import re
from typing import Tuple
from tools.whatsapp.whatsapp_models import WhatsAppContact

class WhatsAppMessageComposer:
    @staticmethod
    def parse_nl_request(nl_request: str) -> Tuple[str, str]:
        """
        Parses a natural language request into (recipient_query, message_body).
        Handles compound instructions, honorifics, and message payload extraction cleanly.
        """
        if not nl_request or not nl_request.strip():
            return "", ""

        raw = nl_request.strip()

        # Step 0: Strip lead-in command prefixes for cleaner pattern matching
        clean_prefix = re.sub(
            r"(?i)^(?:jarvis,?\s*)?(?:ek\s+kam\s+karo\s*)?(?:whatsapp\s*(?:open\s+karo|kholo|pe|par|me|app)?\s*(?:or|aur|and)?\s*)?",
            "",
            raw
        ).strip()

        message_body = ""
        recipient_query = ""

        # Pattern 0: English patterns like "Send WhatsApp message to [recipient] saying [body]"
        match_eng = re.search(
            r"(?i)^(?:send\s+)?(?:a\s+)?(?:whatsapp\s+message|whatsapp|message)\s+to\s+(.+?)(?:\s+(?:saying|with\s+message|that|telling\s+him|telling\s+her)\s+(.+))?$",
            raw
        )
        if match_eng:
            recipient_query = match_eng.group(1).strip()
            if match_eng.group(2):
                message_body = match_eng.group(2).strip().strip("'\"")

        # Pattern 1: "... ko whatsapp pe message karo ki [body]" or "... ko message/text karo ki [body]"
        if not recipient_query and not message_body:
            match_ki = re.search(r"(?i)^(.+?)\s+\bko\b\s+(?:whatsapp\s*(?:pe|par|me|app)?\s*)?(?:message|msg|text)?\s*(?:karo|bhejo|send|bol|kehna)?\s+\b(?:ki|that)\b\s+(.+)$", clean_prefix)
            if not match_ki:
                match_ki = re.search(r"(?i)^(.+?)\s+\bko\b\s+(?:whatsapp\s*(?:pe|par|me|app)?\s*)?(?:message|msg|text)?\s*(?:karo|bhejo|send|bol|kehna)?\s+\b(?:ki|that)\b\s+(.+)$", raw)
            if match_ki:
                recipient_query = match_ki.group(1).strip()
                message_body = match_ki.group(2).strip().strip("'\"")

        # Pattern 2: "... ko [body] ka message bhejo/karo/send"
        if not recipient_query and not message_body:
            match_ka_msg = re.search(r"(?i)^(.+?)\s+\bko\b\s+(.+?)\s+\bka\s+message\s+(?:bhejo|karo|send|de|do|kar\s+do)\b", clean_prefix)
            if match_ka_msg:
                recipient_query = match_ka_msg.group(1).strip()
                message_body = match_ka_msg.group(2).strip().strip("'\"")

        # Pattern 3a: "... ko whatsapp pe message karo [body]" (e.g. "Mittar ko whatsapp pe message karo bhsdk")
        if not recipient_query and not message_body:
            match_msg_after = re.search(r"(?i)^(.+?)\s+\bko\b\s+(?:whatsapp\s*(?:pe|par|me|app)?\s*)?(?:message|msg|text)\s+(?:karo|bhejo|send|kar\s+do)\s+(.+)$", clean_prefix)
            if match_msg_after:
                recipient_query = match_msg_after.group(1).strip()
                message_body = match_msg_after.group(2).strip().strip("'\"")

        # Pattern 3b: "... ko [body] message kar do / message karo / message bhejo" (e.g. "Rishabh sir ko hello what are you doing message kar do")
        if not recipient_query and not message_body:
            match_msg_before = re.search(r"(?i)^(.+?)\s+\bko\b\s+(.+?)\s+\bmessage\s+(?:kar\s+do|karo|bhejo|send|de|do)\b$", clean_prefix)
            if match_msg_before:
                recipient_query = match_msg_before.group(1).strip()
                potential_body = match_msg_before.group(2).strip().strip("'\"")
                if potential_body.lower() not in ["whatsapp", "text", "msg"]:
                    message_body = potential_body

        # Pattern 4: Direct verb "... ko [body] bhejo / send karo / karo / de / do" (e.g. "Rishabh ko hello bhejo")
        if not recipient_query and not message_body:
            match_direct_verb = re.search(r"(?i)^(.+?)\s+\bko\b\s+(.+?)\s+\b(?:bhejo|send|karo|de|do|kar\s+do|send\s+karo|send\s+kar\s+do)\b$", clean_prefix)
            if match_direct_verb:
                recipient_query = match_direct_verb.group(1).strip()
                potential_body = match_direct_verb.group(2).strip().strip("'\"")
                potential_body = re.sub(r"(?i)\s+\b(?:message|msg|text)?\s*(?:kar\s+do|karo|bhejo|send)\b$", "", potential_body).strip()
                if potential_body.lower() not in ["message", "whatsapp message", "text message", "msg"]:
                    message_body = potential_body

        # Clean trailing command words from message_body if any slipped through
        if message_body:
            message_body = re.sub(r"(?i)\s+\bmessage\s+(?:kar\s+do|karo|bhejo|send|de|do)\b$", "", message_body).strip()
            message_body = re.sub(r"(?i)\s+\b(?:message\s+kar|msg\s+kar|text\s+kar)\b$", "", message_body).strip()

        # Pattern 5: Follow-up message without recipient (e.g. "hello bhejo", "bol main late hounga")
        if not recipient_query:
            match_followup = re.search(r"(?i)^(?:bol|kehna|say)\s+(.+)$", raw)
            if match_followup:
                message_body = match_followup.group(1).strip().strip("'\"")

            if not message_body:
                match_bhejo_only = re.search(r"(?i)^(.+?)\s+\b(?:bhejo|send|karo|de|do|kar\s+do)\b$", clean_prefix)
                if match_bhejo_only:
                    candidate = match_bhejo_only.group(1).strip()
                    words = [w.lower() for w in candidate.split()]
                    if words and words[0] in ["usko", "us", "unko", "him", "her", "them"]:
                        recipient_query = words[0]
                        message_body = " ".join(candidate.split()[1:])
                    elif not any(w in words for w in ["ko", "whatsapp", "message"]):
                        message_body = candidate

        # Fallback recipient extraction if not set
        if not recipient_query:
            clean_rec = clean_prefix
            clean_rec = re.sub(r"(?i)\s+\bko\b.*$", "", clean_rec).strip()
            clean_rec = re.sub(r"(?i)\s+\b(?:message|bhejo|karo|send)\b.*$", "", clean_rec).strip()
            recipient_query = clean_rec

        # Clean capitalization of message body
        if message_body:
            message_body = message_body[0].upper() + message_body[1:] if len(message_body) > 1 else message_body.upper()

        return recipient_query, message_body

    @staticmethod
    def compose_from_nl(nl_request: str) -> str:
        _, body = WhatsAppMessageComposer.parse_nl_request(nl_request)
        return body if body else "Hello!"

    @staticmethod
    def generate_preview(contact: WhatsAppContact, body: str) -> str:
        return (
            f"Boss, WhatsApp message preview:\n"
            f"Recipient: {contact.display_name} ({contact.phone_number_masked})\n"
            f"Message: \"{body}\"\n"
            f"Send karu Boss?"
        )
