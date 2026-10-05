"""
agent/execution_state_machine.py
Deterministic Task Execution State Machine for JARVIS.
Tracks task status transitions and rejects invalid state movements.
"""

import time
import logging
from enum import Enum
from typing import Callable, List, Optional, Set
from agent.task_model import TaskModel

logger = logging.getLogger("ExecutionStateMachine")

class TaskState(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    PLANNED = "PLANNED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    PAUSED = "PAUSED"
    RETRYING = "RETRYING"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"

# Valid transitions map
VALID_TRANSITIONS: dict[str, set[str]] = {
    TaskState.CREATED: {TaskState.PLANNING, TaskState.READY, TaskState.RUNNING, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.PLANNING: {TaskState.PLANNED, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.PLANNED: {TaskState.READY, TaskState.RUNNING, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.READY: {TaskState.RUNNING, TaskState.PAUSED, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.RUNNING: {TaskState.WAITING, TaskState.PAUSED, TaskState.RETRYING, TaskState.RECOVERING, TaskState.COMPLETED, TaskState.FAILED, TaskState.PARTIAL, TaskState.BLOCKED, TaskState.CANCELLED},
    TaskState.WAITING: {TaskState.RUNNING, TaskState.COMPLETED, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.PAUSED: {TaskState.RUNNING, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.RETRYING: {TaskState.RUNNING, TaskState.FAILED, TaskState.BLOCKED, TaskState.CANCELLED},
    TaskState.RECOVERING: {TaskState.RUNNING, TaskState.RETRYING, TaskState.FAILED, TaskState.BLOCKED, TaskState.CANCELLED},
    TaskState.COMPLETED: set(),  # Terminal state
    TaskState.FAILED: set(),     # Terminal state
    TaskState.PARTIAL: set(),    # Terminal state
    TaskState.BLOCKED: set(),    # Terminal state
    TaskState.CANCELLED: set(),  # Terminal state
}

class ExecutionStateMachine:
    """
    State Machine governing TaskModel execution lifecycle.
    """
    def __init__(self, listener_callback: Optional[Callable[[TaskModel, str, str], None]] = None):
        self.listener_callback = listener_callback

    def transition_to(self, task: TaskModel, new_state: str | TaskState, reason: str = None) -> bool:
        new_state_str = new_state.value if isinstance(new_state, TaskState) else str(new_state)
        current_state_str = task.status

        if current_state_str == new_state_str:
            return True

        allowed = VALID_TRANSITIONS.get(current_state_str, set())
        if new_state_str not in allowed:
            logger.warning(f"[STATE_MACHINE_REJECT] Task '{task.task_id}' invalid transition attempted: {current_state_str} -> {new_state_str}")
            print(f"[STATE_MACHINE_REJECT] task_id={task.task_id} from={current_state_str} to={new_state_str}", flush=True)
            return False

        old_state = current_state_str
        task.status = new_state_str
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        task.updated_at = now_str

        if new_state_str == TaskState.RUNNING and not task.started_at:
            task.started_at = now_str
        elif new_state_str in {TaskState.COMPLETED, TaskState.FAILED, TaskState.PARTIAL, TaskState.BLOCKED, TaskState.CANCELLED}:
            task.completed_at = now_str

        print(f"[TASK_STATE_TRANSITION] task_id={task.task_id} request_id={task.request_id} from={old_state} to={new_state_str} reason=\"{reason or 'normal'}\"", flush=True)

        # Broadcast progress event
        try:
            from core.progress_reporter import ProgressReporter
            ProgressReporter.get_instance().report(
                f"Task status changed to {new_state_str}.",
                request_id=task.request_id,
                stage=new_state_str,
                speak=False
            )
        except Exception:
            pass

        if self.listener_callback:
            try:
                self.listener_callback(task, old_state, new_state_str)
            except Exception as e:
                logger.error(f"Error in state transition listener: {e}")

        return True
