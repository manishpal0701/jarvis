"""
agent/agent_result.py
Standardized Agent Result Contract for JARVIS Agent Orchestrator.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class AgentResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AMBIGUOUS = "AMBIGUOUS"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    VALIDATION_FAILED = "VALIDATION_FAILED"

@dataclass
class AgentResult:
    success: bool
    task_id: str
    agent_id: str
    status: AgentResultStatus = AgentResultStatus.SUCCESS
    result: Any = None
    error: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "status": self.status.value if isinstance(self.status, AgentResultStatus) else str(self.status),
            "result": self.result,
            "error": self.error,
            "artifacts": self.artifacts,
            "metadata": self.metadata,
            "duration_ms": round(self.duration_ms, 2)
        }
