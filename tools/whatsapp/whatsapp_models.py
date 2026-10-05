"""
tools/whatsapp/whatsapp_models.py
Structured Data Models for JARVIS WhatsApp Automation.
Enforces phone number masking for privacy compliance (+91******1234).
"""

import time
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class WhatsAppStatus(str, Enum):
    IDLE = "IDLE"
    CONNECTED = "CONNECTED"
    RESOLVING_CONTACT = "RESOLVING_CONTACT"
    COMPOSING = "COMPOSING"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    SENDING = "SENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ContactResolutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    CONTACT_NOT_FOUND = "CONTACT_NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_FOUND = "NOT_FOUND"  # Backwards compatibility alias
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    FAILED = "FAILED"

def mask_phone_number(phone: str) -> str:
    if not phone:
        return ""
    digits = re.sub(r"[^\d+]", "", phone)
    if len(digits) >= 10:
        prefix = digits[:3] if digits.startswith("+") else digits[:2]
        suffix = digits[-4:]
        return f"{prefix}******{suffix}"
    return digits[:2] + "****" if len(digits) > 4 else "****"

@dataclass
class WhatsAppContact:
    contact_id: str
    display_name: str
    phone_number_masked: str
    raw_phone_unmasked: str = ""
    provider_reference: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contact_id": self.contact_id,
            "display_name": self.display_name,
            "phone_number_masked": self.phone_number_masked,
            "provider_reference": self.provider_reference
        }

@dataclass
class WhatsAppMessage:
    message_id: str
    recipient: WhatsAppContact
    body: str
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    status: WhatsAppStatus = WhatsAppStatus.IDLE
    provider_reference: Optional[str] = None
    media_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "recipient": self.recipient.to_dict(),
            "body": self.body,
            "timestamp": self.timestamp,
            "status": self.status.value,
            "provider_reference": self.provider_reference
        }
