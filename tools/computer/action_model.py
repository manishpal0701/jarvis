"""
tools/computer/action_model.py
Action and ActionPlan data models for JARVIS Phase 5 Computer Control & Action Execution.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ActionType(str, Enum):
    MOVE = "MOVE"
    CLICK = "CLICK"
    DOUBLE_CLICK = "DOUBLE_CLICK"
    RIGHT_CLICK = "RIGHT_CLICK"
    TYPE = "TYPE"
    KEY_PRESS = "KEY_PRESS"
    HOTKEY = "HOTKEY"
    SCROLL = "SCROLL"
    FOCUS_WINDOW = "FOCUS_WINDOW"
    SWITCH_WINDOW = "SWITCH_WINDOW"
    OPEN_APPLICATION = "OPEN_APPLICATION"
    SELECT = "SELECT"
    COPY = "COPY"
    PASTE = "PASTE"


class ActionStatus(str, Enum):
    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ActionTarget:
    semantic_label: str
    bbox: Optional[Tuple[int, int, int, int]] = None  # (left, top, width, height)
    center_x: int = 0
    center_y: int = 0
    confidence: float = 1.0
    frame_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "semantic_label": self.semantic_label,
            "bbox": self.bbox,
            "center_x": self.center_x,
            "center_y": self.center_y,
            "confidence": self.confidence,
            "frame_id": self.frame_id,
            "metadata": self.metadata
        }


@dataclass
class Action:
    action_id: str = field(default_factory=lambda: f"act_{uuid.uuid4().hex[:8]}")
    action_type: ActionType = ActionType.CLICK
    target: Optional[ActionTarget] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    source_turn_id: Optional[str] = None
    task_id: Optional[str] = None
    confidence: float = 1.0
    risk_level: RiskLevel = RiskLevel.LOW
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    timeout: float = 10.0
    retry_count: int = 0
    status: ActionStatus = ActionStatus.PENDING
    result: Optional[Any] = None
    verification_required: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value if isinstance(self.action_type, ActionType) else str(self.action_type),
            "target": self.target.to_dict() if self.target else None,
            "parameters": self.parameters,
            "source_turn_id": self.source_turn_id,
            "task_id": self.task_id,
            "confidence": self.confidence,
            "risk_level": self.risk_level.value if isinstance(self.risk_level, RiskLevel) else str(self.risk_level),
            "created_at": self.created_at,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "status": self.status.value if isinstance(self.status, ActionStatus) else str(self.status),
            "result": self.result,
            "verification_required": self.verification_required,
            "error": self.error
        }


@dataclass
class ActionPlan:
    plan_id: str = field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    task_id: Optional[str] = None
    user_intent: str = ""
    actions: List[Action] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False
    confidence: float = 1.0
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    status: str = "CREATED"  # CREATED, VALIDATED, EXECUTING, COMPLETED, FAILED, CANCELLED, BLOCKED
    verification_policy: str = "STANDARD"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "request_id": self.request_id,
            "task_id": self.task_id,
            "user_intent": self.user_intent,
            "actions": [a.to_dict() for a in self.actions],
            "risk_level": self.risk_level.value if isinstance(self.risk_level, RiskLevel) else str(self.risk_level),
            "requires_confirmation": self.requires_confirmation,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "status": self.status,
            "verification_policy": self.verification_policy
        }


@dataclass
class ActionResult:
    action_id: str
    status: ActionStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    verification_status: str = "UNVERIFIED"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "status": self.status.value if isinstance(self.status, ActionStatus) else str(self.status),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "verification_status": self.verification_status,
            "metadata": self.metadata
        }
