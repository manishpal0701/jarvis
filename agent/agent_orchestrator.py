"""
agent/agent_orchestrator.py
Central Agent Orchestrator for JARVIS.
Coordinates intent classification, task planning, agent selection, state machine execution,
bounded auto-recovery, task isolation, and progress speech integration.
"""

import time
import uuid
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any

from agent.agent_result import AgentResult, AgentResultStatus
from agent.agent_registry import AgentRegistry, AgentDescriptor
from agent.task_model import TaskModel, StepModel, TaskType, TaskPriority
from agent.task_planner import TaskPlanner
from agent.execution_state_machine import ExecutionStateMachine, TaskState
from agent.task_persistence import TaskPersistence

logger = logging.getLogger("AgentOrchestrator")

MAX_RECOVERY_ATTEMPTS = 3

class FailureClass:
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    BUILD_ERROR = "BUILD_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    API_ERROR = "API_ERROR"
    TIMEOUT = "TIMEOUT"
    INVALID_INPUT = "INVALID_INPUT"
    AGENT_ERROR = "AGENT_ERROR"
    ENVIRONMENT_ERROR = "ENVIRONMENT_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

class AgentOrchestrator:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = AgentOrchestrator()
            return cls._instance

    def __init__(self):
        self.registry = AgentRegistry.get_instance()
        self.planner = TaskPlanner()
        self.state_machine = ExecutionStateMachine()
        self.persistence = TaskPersistence()
        self._active_tasks: Dict[str, TaskModel] = {}
        self._cancellation_requested: set[str] = set()

    def classify_failure(self, error_msg: str) -> str:
        if not error_msg:
            return FailureClass.UNKNOWN_ERROR
        err_lower = error_msg.lower()
        if "timeout" in err_lower:
            return FailureClass.TIMEOUT
        if "build" in err_lower or "compile" in err_lower:
            return FailureClass.BUILD_ERROR
        if "syntax" in err_lower or "parse" in err_lower:
            return FailureClass.SYNTAX_ERROR
        if "dependenc" in err_lower or "import" in err_lower:
            return FailureClass.DEPENDENCY_ERROR
        if "api" in err_lower or "http" in err_lower or "500" in err_lower:
            return FailureClass.API_ERROR
        if "input" in err_lower or "invalid" in err_lower:
            return FailureClass.INVALID_INPUT
        if "agent" in err_lower:
            return FailureClass.AGENT_ERROR
        return FailureClass.RUNTIME_ERROR

    def request_cancellation(self, task_id: str = None) -> bool:
        """Requests safe cancellation of a running task."""
        with self._lock:
            if task_id:
                self._cancellation_requested.add(task_id)
                if task_id in self._active_tasks:
                    task = self._active_tasks[task_id]
                    self.state_machine.transition_to(task, TaskState.CANCELLED, reason="User cancellation request")
                    self.persistence.save_task(task)
                    print(f"[TASK_CANCELLED] task_id={task_id} status=CANCELLED", flush=True)
                    return True
            else:
                # Cancel all active tasks
                for tid, task in list(self._active_tasks.items()):
                    self._cancellation_requested.add(tid)
                    self.state_machine.transition_to(task, TaskState.CANCELLED, reason="Global user cancellation request")
                    self.persistence.save_task(task)
                return True
        return False

    def is_cancelled(self, task_id: str) -> bool:
        with self._lock:
            return task_id in self._cancellation_requested

    def get_task(self, task_id: str) -> Optional[TaskModel]:
        with self._lock:
            if task_id in self._active_tasks:
                return self._active_tasks[task_id]
        data = self.persistence.get_task(task_id)
        return TaskModel(**data) if data else None

    def orchestrate(self, user_request: str, source: str = "voice", request_id: str = None) -> AgentResult:
        start_time = time.time()
        req_id = request_id or f"req_{uuid.uuid4().hex[:8]}"

        # Check for cancellation command
        req_lower = user_request.lower().strip()
        if any(kw in req_lower for kw in ["stop this", "cancel task", "stop app build", "stop development"]):
            cancelled = self.request_cancellation()
            return AgentResult(
                success=True,
                task_id="global_cancel",
                agent_id="orchestrator",
                status=AgentResultStatus.CANCELLED,
                result="Active task cancelled cleanly as requested.",
                duration_ms=(time.time() - start_time) * 1000.0
            )

        # 1. Generate Task Plan
        task = self.planner.generate_plan(user_request, request_id=req_id)
        with self._lock:
            self._active_tasks[task.task_id] = task

        self.state_machine.transition_to(task, TaskState.PLANNING)
        self.state_machine.transition_to(task, TaskState.PLANNED)
        self.state_machine.transition_to(task, TaskState.READY)
        self.persistence.save_task(task)

        # 2. Proportional execution for simple conversational requests
        if task.task_type == TaskType.CONVERSATIONAL:
            self.state_machine.transition_to(task, TaskState.RUNNING)
            agent_desc = self.registry.get_agent("conversation_agent")
            res = agent_desc.handler(task, task.steps[0]) if agent_desc and agent_desc.handler else AgentResult(success=False, task_id=task.task_id, agent_id="conversation_agent", status=AgentResultStatus.FAILURE, error="Handler missing")

            if res.success:
                self.state_machine.transition_to(task, TaskState.COMPLETED)
            else:
                self.state_machine.transition_to(task, TaskState.FAILED)

            task.result = res.result
            task.error = res.error
            self.persistence.save_task(task)
            with self._lock:
                self._active_tasks.pop(task.task_id, None)
            return res

        # 3. Task Execution Loop for Single / Multi-step Agents
        self.state_machine.transition_to(task, TaskState.RUNNING)

        # Isolated workspace path for project tasks
        workspace_folder = f"JARVIS_Workspace_{task.task_id}"
        task.workspace_path = workspace_folder
        print(f"[TASK_ISOLATION] task_id={task.task_id} workspace='{workspace_folder}'", flush=True)

        overall_success = True
        failed_step_name = None
        executed_artifacts = []

        completed_step_ids = set()

        for step_idx, step in enumerate(task.steps):
            if self.is_cancelled(task.task_id):
                self.state_machine.transition_to(task, TaskState.CANCELLED, reason="Cancelled during step execution")
                self.persistence.save_task(task)
                with self._lock:
                    self._active_tasks.pop(task.task_id, None)
                return AgentResult(
                    success=False,
                    task_id=task.task_id,
                    agent_id="orchestrator",
                    status=AgentResultStatus.CANCELLED,
                    result="Task cancelled before completion.",
                    duration_ms=(time.time() - start_time) * 1000.0
                )

            # Verify step dependencies
            unresolved_deps = [dep for dep in step.dependencies if dep not in completed_step_ids]
            if unresolved_deps:
                error_msg = f"Step '{step.name}' blocked by unresolved dependencies: {unresolved_deps}"
                step.status = "FAILED"
                step.error = error_msg
                task.error = error_msg
                overall_success = False
                failed_step_name = step.name
                self.state_machine.transition_to(task, TaskState.BLOCKED, reason=error_msg)
                break

            step.status = "RUNNING"
            step.started_at = time.strftime("%Y-%m-%dT%H:%M:%S")
            task.current_step = step_idx + 1
            task.active_agent = step.agent_id
            self.persistence.save_task(task)

            print(f"[STEP_START] task_id={task.task_id} step_id={step.step_id} name='{step.name}' agent={step.agent_id}", flush=True)

            agent_desc = self.registry.get_agent(step.agent_id) or self.registry.match_agent_for_task(task.task_type)
            step_result = None

            if agent_desc and agent_desc.handler:
                # Bounded recovery execution loop
                attempt = 0
                step_success = False

                while attempt < MAX_RECOVERY_ATTEMPTS and not step_success:
                    attempt += 1
                    if attempt > 1:
                        task.recovery_count += 1
                        print(f"[RECOVERY_ATTEMPT] task_id={task.task_id} step_id={step.step_id} attempt={attempt}/{MAX_RECOVERY_ATTEMPTS}", flush=True)
                        self.state_machine.transition_to(task, TaskState.RECOVERING, reason=f"Bounded recovery attempt {attempt}")
                        self.state_machine.transition_to(task, TaskState.RETRYING, reason=f"Retrying step {step.step_id}")
                        self.state_machine.transition_to(task, TaskState.RUNNING)

                    try:
                        step_result = agent_desc.handler(task, step)
                        if step_result:
                            # Handle explicit non-success states cleanly
                            if step_result.status == AgentResultStatus.WAITING_FOR_CONFIRMATION:
                                step.status = "WAITING"
                                step.output = step_result.result
                                self.state_machine.transition_to(task, TaskState.WAITING, reason="Waiting for user confirmation")
                                task.result = step_result.result
                                self.persistence.save_task(task)
                                with self._lock:
                                    self._active_tasks.pop(task.task_id, None)
                                return step_result

                            if step_result.status == AgentResultStatus.AUTH_REQUIRED:
                                step.status = "AUTH_REQUIRED"
                                step.output = step_result.result
                                self.state_machine.transition_to(task, TaskState.WAITING, reason="Authentication required")
                                task.result = step_result.result
                                self.persistence.save_task(task)
                                with self._lock:
                                    self._active_tasks.pop(task.task_id, None)
                                return step_result

                            if step_result.status == AgentResultStatus.AMBIGUOUS:
                                step.status = "WAITING"
                                step.output = step_result.result
                                self.state_machine.transition_to(task, TaskState.WAITING, reason="User input ambiguous")
                                task.result = step_result.result
                                self.persistence.save_task(task)
                                with self._lock:
                                    self._active_tasks.pop(task.task_id, None)
                                return step_result

                            if step_result.status in [AgentResultStatus.NOT_IMPLEMENTED, AgentResultStatus.PROVIDER_UNAVAILABLE]:
                                step.status = "FAILED"
                                step.error = str(step_result.result)
                                task.error = str(step_result.result)
                                overall_success = False
                                failed_step_name = step.name
                                print(f"[STEP_PROVIDER_UNAVAILABLE] task_id={task.task_id} status={step_result.status.value}", flush=True)
                                break

                            if step_result.success and step_result.status == AgentResultStatus.SUCCESS:
                                step_success = True
                            else:
                                err_msg = step_result.error or str(step_result.result) if step_result else "Execution failed"
                                fail_cls = self.classify_failure(err_msg)
                                print(f"[STEP_FAILED] task_id={task.task_id} step_id={step.step_id} failure_class={fail_cls} error='{err_msg}'", flush=True)
                        else:
                            err_msg = "No result returned from agent"
                            fail_cls = self.classify_failure(err_msg)
                            print(f"[STEP_FAILED] task_id={task.task_id} step_id={step.step_id} failure_class={fail_cls} error='{err_msg}'", flush=True)
                    except Exception as ex:
                        err_msg = str(ex)
                        fail_cls = self.classify_failure(err_msg)
                        print(f"[STEP_EXCEPTION] task_id={task.task_id} step_id={step.step_id} failure_class={fail_cls} error='{err_msg}'", flush=True)

                if step_success and step_result and step_result.status == AgentResultStatus.SUCCESS:
                    step.status = "COMPLETED"
                    step.completed_at = time.strftime("%Y-%m-%dT%H:%M:%S")
                    step.output = step_result.result
                    completed_step_ids.add(step.step_id)
                    if step_result.artifacts:
                        executed_artifacts.extend(step_result.artifacts)
                    print(f"[STEP_COMPLETED] task_id={task.task_id} step_id={step.step_id}", flush=True)
                else:
                    step.status = "FAILED"
                    step.error = step_result.error if (step_result and step_result.error) else (step_result.result if step_result else "Max recovery attempts exceeded")
                    overall_success = False
                    failed_step_name = step.name
                    task.error = str(step.error)
                    print(f"[STEP_PERMANENT_FAILURE] task_id={task.task_id} step_id={step.step_id} max_attempts_exceeded=True", flush=True)
                    break
            else:
                step.status = "FAILED"
                step.error = f"Agent '{step.agent_id}' not registered"
                overall_success = False
                failed_step_name = step.name
                break

        total_duration = (time.time() - start_time) * 1000.0

        # Strict No False Success Gate
        if overall_success and len(completed_step_ids) == len(task.steps):
            self.state_machine.transition_to(task, TaskState.COMPLETED)
            task.result = f"Task completed successfully across {len(task.steps)} steps."
            status_enum = AgentResultStatus.SUCCESS
        elif completed_step_ids:
            self.state_machine.transition_to(task, TaskState.PARTIAL, reason=f"Failed at step '{failed_step_name}'")
            task.result = f"Partial success: {len(completed_step_ids)} of {len(task.steps)} steps succeeded. Failed at '{failed_step_name}'."
            status_enum = AgentResultStatus.PARTIAL
        else:
            self.state_machine.transition_to(task, TaskState.FAILED, reason=task.error or "Task failed")
            status_enum = AgentResultStatus.FAILURE

        self.persistence.save_task(task)
        with self._lock:
            self._active_tasks.pop(task.task_id, None)

        return AgentResult(
            success=overall_success,
            task_id=task.task_id,
            agent_id=task.active_agent or "orchestrator",
            status=status_enum,
            result=task.result,
            error=task.error,
            artifacts=executed_artifacts,
            metadata=task.metadata,
            duration_ms=total_duration
        )
