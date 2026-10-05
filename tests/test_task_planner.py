import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agent.task_planner import TaskPlanner
from agent.task_model import TaskType, TaskPriority
from agent.execution_state_machine import ExecutionStateMachine, TaskState

class TestTaskPlannerAndStateMachine(unittest.TestCase):

    def setUp(self):
        self.planner = TaskPlanner()
        self.state_machine = ExecutionStateMachine()

    def test_01_simple_conversational_plan(self):
        task = self.planner.generate_plan("What is Riverpod?")
        self.assertEqual(task.task_type, TaskType.CONVERSATIONAL)
        self.assertEqual(len(task.steps), 1)
        self.assertEqual(task.steps[0].agent_id, "conversation_agent")

    def test_02_complex_app_build_plan(self):
        task = self.planner.generate_plan("Create a production expense tracker app with Flutter, FastAPI backend, authentication, and search.")
        self.assertEqual(task.task_type, TaskType.APP_BUILD)
        self.assertEqual(task.priority, TaskPriority.HIGH)
        self.assertEqual(len(task.steps), 5)
        
        # Verify dependency ordering
        step1 = task.steps[0]
        step2 = task.steps[1]
        step4 = task.steps[3]

        self.assertIn(step1.step_id, step2.dependencies)
        self.assertIn(step2.step_id, step4.dependencies)

    def test_03_state_machine_valid_transitions(self):
        task = self.planner.generate_plan("Simple task")
        
        # CREATED -> PLANNING -> PLANNED -> READY -> RUNNING -> COMPLETED
        self.assertTrue(self.state_machine.transition_to(task, TaskState.PLANNING))
        self.assertTrue(self.state_machine.transition_to(task, TaskState.PLANNED))
        self.assertTrue(self.state_machine.transition_to(task, TaskState.READY))
        self.assertTrue(self.state_machine.transition_to(task, TaskState.RUNNING))
        self.assertTrue(self.state_machine.transition_to(task, TaskState.COMPLETED))

    def test_04_state_machine_invalid_transitions(self):
        task = self.planner.generate_plan("Simple task")
        task.status = "COMPLETED"

        # COMPLETED -> RUNNING should be rejected
        self.assertFalse(self.state_machine.transition_to(task, TaskState.RUNNING))

if __name__ == "__main__":
    unittest.main()
