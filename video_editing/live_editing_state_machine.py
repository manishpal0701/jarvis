"""
video_editing/live_editing_state_machine.py
Phase 6 Live Editing State Machine & Operations Lifecycle Manager.
Enforces explicit state transitions, bounded operation retries (MAX_OPERATION_RETRIES = 2),
sub-failure state tracking, and cancellation safety.
"""

from typing import Optional, Dict, Any

MAX_OPERATION_RETRIES = 2

# Core State Constants
STATE_IDLE = "IDLE"
STATE_STARTING_PREMIERE = "STARTING_PREMIERE"
STATE_PREMIERE_READY = "PREMIERE_READY"
STATE_IMPORTING_MEDIA = "IMPORTING_MEDIA"
STATE_CREATING_SEQUENCE = "CREATING_SEQUENCE"
STATE_EDITING_TIMELINE = "EDITING_TIMELINE"
STATE_ADDING_TRANSITIONS = "ADDING_TRANSITIONS"
STATE_ADDING_AUDIO = "ADDING_AUDIO"
STATE_ADDING_TEXT = "ADDING_TEXT"
STATE_APPLYING_EFFECTS = "APPLYING_EFFECTS"
STATE_FINALIZING_SEQUENCE = "FINALIZING_SEQUENCE"
STATE_EXPORTING = "EXPORTING"
STATE_VERIFYING_OUTPUT = "VERIFYING_OUTPUT"
STATE_COMPLETED = "COMPLETED"
STATE_FAILED = "FAILED"
STATE_CANCELLED = "CANCELLED"

# Failure Code Constants
ERR_PREMIERE_DISCONNECTED = "PREMIERE_DISCONNECTED"
ERR_PREMIERE_UNRESPONSIVE = "PREMIERE_UNRESPONSIVE"
ERR_PREMIERE_OPERATION_FAILED = "PREMIERE_OPERATION_FAILED"
ERR_PREMIERE_STATE_UNVERIFIED = "PREMIERE_STATE_UNVERIFIED"
ERR_EXPORT_FAILED = "EXPORT_FAILED"
ERR_OUTPUT_VERIFICATION_FAILED = "OUTPUT_VERIFICATION_FAILED"

# Cancellation Code Constants
STATUS_USER_CANCELLED = "USER_CANCELLED"
STATUS_CANCELLATION_PENDING = "CANCELLATION_PENDING"

# Command Lifecycle Constants
CMD_REQUESTED = "COMMAND_REQUESTED"
CMD_SENT = "COMMAND_SENT"
CMD_EXECUTING = "COMMAND_EXECUTING"
CMD_CHECK = "PREMIERE_STATE_CHECK"
CMD_COMPLETED = "COMMAND_COMPLETED"
CMD_FAILED = "COMMAND_FAILED"


class LiveEditingStateMachine:
    """
    Manages state transitions, step retries, command lifecycles, and cancellation flags.
    """

    def __init__(self):
        self.state = STATE_IDLE
        self.failure_code: Optional[str] = None
        self.failure_reason: Optional[str] = None
        self.cancellation_requested = False
        self.cancellation_status: Optional[str] = None
        self.step_retries: Dict[str, int] = {}
        self.current_command_lifecycle: Optional[str] = None
        self.active_project_name: Optional[str] = None
        self.active_sequence_name: Optional[str] = None

    def reset(self):
        self.state = STATE_IDLE
        self.failure_code = None
        self.failure_reason = None
        self.cancellation_requested = False
        self.cancellation_status = None
        self.step_retries.clear()
        self.current_command_lifecycle = None
        self.active_project_name = None
        self.active_sequence_name = None

    def transition_to(self, new_state: str, details: Optional[str] = None) -> bool:
        """
        Transitions state machine to new state and prints state transition telemetry.
        """
        old_state = self.state

        # Check cancellation intercept
        if self.cancellation_requested and new_state not in (STATE_FAILED, STATE_CANCELLED):
            self.state = STATE_CANCELLED
            self.cancellation_status = STATUS_USER_CANCELLED
            print(f"[STATE_MACHINE]\nold_state={old_state}\nnew_state={STATE_CANCELLED}\nreason=USER_CANCELLED", flush=True)
            return False

        self.state = new_state
        print(f"[STATE_MACHINE]\nold_state={old_state}\nnew_state={new_state}\ndetails={details or ''}", flush=True)
        return True

    def record_failure(self, failure_code: str, reason: str):
        """
        Transitions to FAILED state with explicit error details.
        """
        self.failure_code = failure_code
        self.failure_reason = reason
        self.transition_to(STATE_FAILED, details=f"code={failure_code} reason={reason}")

    def request_cancellation(self):
        """
        Requests session cancellation safely.
        """
        self.cancellation_requested = True
        self.cancellation_status = STATUS_CANCELLATION_PENDING
        print("[STATE_MACHINE]\nstatus=CANCELLATION_REQUESTED", flush=True)

    def can_retry_step(self, step_name: str) -> bool:
        """
        Checks if step retries are within bounded limits (MAX_OPERATION_RETRIES = 2).
        """
        count = self.step_retries.get(step_name, 0)
        return count < MAX_OPERATION_RETRIES

    def increment_step_retry(self, step_name: str) -> int:
        """
        Increments and returns retry count for step.
        """
        count = self.step_retries.get(step_name, 0) + 1
        self.step_retries[step_name] = count
        print(f"[RETRY_TRACKER]\nstep={step_name}\nattempt={count}/{MAX_OPERATION_RETRIES}", flush=True)
        return count

    def set_command_lifecycle(self, stage: str, command_name: str):
        """
        Updates current command lifecycle state.
        """
        self.current_command_lifecycle = stage
        print(f"[COMMAND_LIFECYCLE]\ncommand={command_name}\nstage={stage}", flush=True)
