import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agent.agent_orchestrator import AgentOrchestrator, FailureClass
from agent.execution_state_machine import ExecutionStateMachine, TaskState
from agent.task_model import TaskModel, StepModel, TaskType
from agent.agent_result import AgentResult, AgentResultStatus

class TestBoundedRecoveryAndNoFalseSuccess(unittest.TestCase):

    def setUp(self):
        self.orchestrator = AgentOrchestrator.get_instance()
        self.state_machine = ExecutionStateMachine()

    def test_01_failure_classifier(self):
        self.assertEqual(self.orchestrator.classify_failure("Syntax error on line 5"), FailureClass.SYNTAX_ERROR)
        self.assertEqual(self.orchestrator.classify_failure("Package flutter_bloc import error"), FailureClass.DEPENDENCY_ERROR)
        self.assertEqual(self.orchestrator.classify_failure("Request timeout after 30s"), FailureClass.TIMEOUT)
        self.assertEqual(self.orchestrator.classify_failure("Runtime crash null pointer"), FailureClass.RUNTIME_ERROR)

    def test_02_max_recovery_attempts_enforced(self):
        # Create a task model
        task = TaskModel(
            task_id="recovery_test_task",
            request_id="req_test_1",
            user_request="Test Task",
            normalized_goal="Test Task",
            task_type=TaskType.APP_BUILD,
            steps=[
                StepModel(
                    step_id="step_1",
                    task_id="recovery_test_task",
                    name="Failing Step",
                    description="Failing Step Description",
                    agent_id="app_builder_agent"
                )
            ]
        )
        self.state_machine.transition_to(task, TaskState.PLANNING)
        self.state_machine.transition_to(task, TaskState.PLANNED)
        self.state_machine.transition_to(task, TaskState.READY)
        self.state_machine.transition_to(task, TaskState.RUNNING)

        # Failures count up to MAX_RECOVERY_ATTEMPTS = 3
        fail_cls = self.orchestrator.classify_failure("build failed")
        self.assertEqual(fail_cls, FailureClass.BUILD_ERROR)

    def test_03_no_false_success_prevention(self):
        task = TaskModel(
            task_id="false_success_task",
            request_id="req_test_2",
            user_request="False Success Task",
            normalized_goal="False Success Task",
            task_type=TaskType.APP_BUILD,
            steps=[
                StepModel(
                    step_id="step_1",
                    task_id="false_success_task",
                    name="Verify Step",
                    description="Verify Step Description",
                    agent_id="app_builder_agent"
                )
            ]
        )
        self.state_machine.transition_to(task, TaskState.PLANNING)
        self.state_machine.transition_to(task, TaskState.PLANNED)
        self.state_machine.transition_to(task, TaskState.READY)
        self.state_machine.transition_to(task, TaskState.RUNNING)

        # Build verification fails
        result = AgentResult(
            success=False,
            task_id=task.task_id,
            agent_id="app_builder_agent",
            status=AgentResultStatus.FAILURE,
            error="0 tests passed, 2 errors in flutter analyze",
            duration_ms=50.0
        )

        # Orchestrator must not mark task completed if result.success is False
        self.assertFalse(result.success)
        self.assertNotEqual(task.status, "COMPLETED")

    def test_04_cancellation_flow(self):
        task = TaskModel(
            task_id="cancellation_task",
            request_id="req_test_3",
            user_request="Cancel Me",
            normalized_goal="Cancel Me",
            task_type=TaskType.APP_BUILD,
            steps=[
                StepModel(
                    step_id="step_1",
                    task_id="cancellation_task",
                    name="Long Step",
                    description="Long Step Description",
                    agent_id="app_builder_agent"
                )
            ]
        )
        self.orchestrator._active_tasks["cancellation_task"] = task
        self.state_machine.transition_to(task, TaskState.PLANNING)
        self.state_machine.transition_to(task, TaskState.PLANNED)
        self.state_machine.transition_to(task, TaskState.READY)
        self.state_machine.transition_to(task, TaskState.RUNNING)

        res = self.orchestrator.request_cancellation("cancellation_task")
        self.assertTrue(res)
        self.assertEqual(task.status, TaskState.CANCELLED.value)

        # Cleanup
        self.orchestrator._active_tasks.pop("cancellation_task", None)

if __name__ == "__main__":
    unittest.main()
