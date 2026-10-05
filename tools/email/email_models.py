"""
tools/email/email_models.py
Structured Data Models and Dataclasses for JARVIS Email Agent.
Includes secret input redaction for security compliance.
"""

import time
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class EmailStatus(str, Enum):
    IDLE = "IDLE"
    CONNECTED = "CONNECTED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    SEARCHING = "SEARCHING"
    READING = "READING"
    DRAFT_CREATED = "DRAFT_CREATED"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    SENDING = "SENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class EmailRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|secret|token|password|auth[_-]?header|bearer)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{8,})["\']?'),
    re.compile(r'sk-[a-zA-Z0-9]{20,}'),
    re.compile(r'ghp_[a-zA-Z0-9]{36}'),
    re.compile(r'eyJ[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*'),
]

def mask_email_secrets(text: str) -> str:
    if not text:
        return ""
    res = text
    for pat in SECRET_PATTERNS:
        res = pat.sub("[SECRET_INPUT]", res)
    return res

@dataclass
class EmailMessage:
    message_id: str
    thread_id: str
    sender: str
    recipients: List[str]
    subject: str
    body: str
    snippet: str
    timestamp: str
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    is_unread: bool = False
    attachments_metadata: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "sender": mask_email_secrets(self.sender),
            "recipients": [mask_email_secrets(r) for r in self.recipients],
            "cc": [mask_email_secrets(r) for r in self.cc],
            "bcc": [mask_email_secrets(r) for r in self.bcc],
            "subject": mask_email_secrets(self.subject),
            "body": mask_email_secrets(self.body),
            "snippet": mask_email_secrets(self.snippet),
            "timestamp": self.timestamp,
            "labels": self.labels,
            "is_unread": self.is_unread,
            "attachments_metadata": self.attachments_metadata
        }

@dataclass
class EmailDraft:
    draft_id: str
    recipient: str
    subject: str
    body: str
    thread_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "recipient": mask_email_secrets(self.recipient),
            "subject": mask_email_secrets(self.subject),
            "body": mask_email_secrets(self.body),
            "thread_id": self.thread_id,
            "created_at": self.created_at
        }

@dataclass
class EmailSearchResult:
    query: str
    messages: List[EmailMessage] = field(default_factory=list)
    total_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "total_count": self.total_count,
            "messages": [m.to_dict() for m in self.messages]
        }
