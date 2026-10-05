"""
tests/test_false_completion_prevention.py
Unit tests verifying false completion prevention across WhatsApp Agent, Email Agent,
Agent Orchestrator, and Execution State Machine.
"""

import unittest
from agent.agent_result import AgentResult, AgentResultStatus
from agent.task_model import TaskModel, StepModel, TaskType
from agent.agent_orchestrator import AgentOrchestrator
from agent.execution_state_machine import ExecutionStateMachine, TaskState
from tools.whatsapp.whatsapp_agent import WhatsAppAgent
from tools.whatsapp.whatsapp_confirmation import WhatsAppConfirmationManager
from tools.email.email_agent import EmailAgent
from tools.email.email_confirmation import EmailConfirmationManager


class TestFalseCompletionPrevention(unittest.TestCase):
    def setUp(self):
        WhatsAppConfirmationManager.get_instance().clear()
        EmailConfirmationManager.get_instance().clear()

    def tearDown(self):
        WhatsAppConfirmationManager.get_instance().clear()
        EmailConfirmationManager.get_instance().clear()

    def test_agent_result_status_extended_enum(self):
        """Verify that extended status codes exist in AgentResultStatus."""
        self.assertEqual(AgentResultStatus.WAITING_FOR_CONFIRMATION.value, "WAITING_FOR_CONFIRMATION")
        self.assertEqual(AgentResultStatus.AUTH_REQUIRED.value, "AUTH_REQUIRED")
        self.assertEqual(AgentResultStatus.AMBIGUOUS.value, "AMBIGUOUS")
        self.assertEqual(AgentResultStatus.PROVIDER_UNAVAILABLE.value, "PROVIDER_UNAVAILABLE")
        self.assertEqual(AgentResultStatus.NOT_IMPLEMENTED.value, "NOT_IMPLEMENTED")
        self.assertEqual(AgentResultStatus.VALIDATION_FAILED.value, "VALIDATION_FAILED")

    def test_whatsapp_agent_requires_confirmation_status(self):
        """Verify WhatsApp agent returns WAITING_FOR_CONFIRMATION status, not fake SUCCESS."""
        task = TaskModel(
            task_id="t_wa_1",
            request_id="r_wa_1",
            user_request="Send WhatsApp message to Rahul saying I will be late",
            normalized_goal="Send WhatsApp message to Rahul saying I will be late",
            task_type=TaskType.WHATSAPP
        )
        step = StepModel(
            step_id="t_wa_1_s1",
            task_id="t_wa_1",
            name="WhatsApp Action",
            description="Send WhatsApp message step",
            agent_id="whatsapp_agent"
        )
        agent = WhatsAppAgent.get_instance()
        res = agent.handle_task(task, step)

        self.assertIn(res.status, [AgentResultStatus.WAITING_FOR_CONFIRMATION, AgentResultStatus.AMBIGUOUS])
        self.assertFalse(res.success)

    def test_email_agent_requires_confirmation_status(self):
        """Verify Email agent returns WAITING_FOR_CONFIRMATION status, not fake SUCCESS."""
        task = TaskModel(
            task_id="t_em_1",
            request_id="r_em_1",
            user_request="Send email to boss@company.com with subject Update",
            normalized_goal="Send email to boss@company.com with subject Update",
            task_type=TaskType.EMAIL
        )
        step = StepModel(
            step_id="t_em_1_s1",
            task_id="t_em_1",
            name="Email Action",
            description="Send email step",
            agent_id="email_agent"
        )
        agent = EmailAgent.get_instance()
        res = agent.handle_task(task, step)

        self.assertEqual(res.status, AgentResultStatus.WAITING_FOR_CONFIRMATION)
        self.assertFalse(res.success)

    def test_orchestrator_prevents_false_completion_on_waiting_status(self):
        """Verify AgentOrchestrator does not mark task COMPLETED when result is WAITING_FOR_CONFIRMATION or AMBIGUOUS."""
        orchestrator = AgentOrchestrator.get_instance()
        result = orchestrator.orchestrate("Send WhatsApp message to Alex saying hello")

        self.assertIsNotNone(result)
        self.assertIn(result.status, [AgentResultStatus.WAITING_FOR_CONFIRMATION, AgentResultStatus.AMBIGUOUS])
        self.assertFalse(result.success)

    def test_state_machine_supports_waiting_to_completed(self):
        """Verify state machine can transition from WAITING to COMPLETED upon user confirmation."""
        sm = ExecutionStateMachine()
        task = TaskModel(task_id="t_sm_1", request_id="r_sm_1", user_request="test", normalized_goal="test", status="CREATED")

        # Transition to RUNNING
        sm.transition_to(task, TaskState.RUNNING, reason="Start task")
        self.assertEqual(task.status, TaskState.RUNNING.value)

        # Transition to WAITING
        sm.transition_to(task, TaskState.WAITING, reason="Waiting for confirmation")
        self.assertEqual(task.status, TaskState.WAITING.value)

        # Transition to COMPLETED after user confirms
        sm.transition_to(task, TaskState.COMPLETED, reason="Confirmed and executed")
        self.assertEqual(task.status, TaskState.COMPLETED.value)


if __name__ == "__main__":
    unittest.main()
