"""
agent/task_model.py
Task and Step Models for JARVIS Agent Orchestrator & Task Planner.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class TaskPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class TaskType(str, Enum):
    CONVERSATIONAL = "CONVERSATIONAL"
    SINGLE_AGENT = "SINGLE_AGENT"
    APP_BUILD = "APP_BUILD"
    WEBSITE_BUILD = "WEBSITE_BUILD"
    VIDEO_EDITING = "VIDEO_EDITING"
    CODE_ASSISTANT = "CODE_ASSISTANT"
    STOCK_ANALYSIS = "STOCK_ANALYSIS"
    DESKTOP_AUTOMATION = "DESKTOP_AUTOMATION"
    MEMORY = "MEMORY"
    VISION = "VISION"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"

@dataclass
class StepModel:
    step_id: str
    task_id: str
    name: str
    description: str
    agent_id: str
    status: str = "CREATED"  # CREATED, READY, RUNNING, COMPLETED, FAILED, SKIPPED, CANCELLED
    dependencies: List[str] = field(default_factory=list)
    input: Dict[str, Any] = field(default_factory=dict)
    output: Any = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "agent_id": self.agent_id,
            "status": self.status,
            "dependencies": self.dependencies,
            "input": self.input,
            "output": self.output,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "error": self.error
        }

@dataclass
class TaskModel:
    task_id: str
    request_id: str
    user_request: str
    normalized_goal: str
    parent_task_id: Optional[str] = None
    task_type: TaskType = TaskType.CONVERSATIONAL
    priority: TaskPriority = TaskPriority.NORMAL
    status: str = "CREATED"
    workspace_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    started_at: Optional[str] = None
    updated_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    completed_at: Optional[str] = None
    current_step: int = 0
    total_steps: int = 0
    steps: List[StepModel] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    active_agent: Optional[str] = None
    retry_count: int = 0
    recovery_count: int = 0
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "parent_task_id": self.parent_task_id,
            "request_id": self.request_id,
            "user_request": self.user_request,
            "normalized_goal": self.normalized_goal,
            "task_type": self.task_type.value if isinstance(self.task_type, TaskType) else str(self.task_type),
            "priority": self.priority.value if isinstance(self.priority, TaskPriority) else str(self.priority),
            "status": self.status,
            "workspace_path": self.workspace_path,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "steps": [s.to_dict() for s in self.steps],
            "dependencies": self.dependencies,
            "active_agent": self.active_agent,
            "retry_count": self.retry_count,
            "recovery_count": self.recovery_count,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata
        }
