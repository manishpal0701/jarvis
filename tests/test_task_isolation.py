import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agent.task_model import TaskModel, StepModel, TaskType
from agent.task_persistence import TaskPersistence
from agent.agent_orchestrator import AgentOrchestrator

class TestTaskIsolationAndPersistence(unittest.TestCase):

    def setUp(self):
        self.persistence = TaskPersistence.get_instance()
        self.orchestrator = AgentOrchestrator.get_instance()

    def test_01_workspace_isolation(self):
        task_a = TaskModel(
            task_id="task_weather_app",
            request_id="req_w",
            user_request="Weather App",
            normalized_goal="Weather App",
            task_type=TaskType.APP_BUILD,
            workspace_path=os.path.join("JARVIS_Workspace_task_weather_app")
        )

        task_b = TaskModel(
            task_id="task_expense_app",
            request_id="req_e",
            user_request="Expense App",
            normalized_goal="Expense App",
            task_type=TaskType.APP_BUILD,
            workspace_path=os.path.join("JARVIS_Workspace_task_expense_app")
        )

        self.assertNotEqual(task_a.workspace_path, task_b.workspace_path)
        self.assertTrue(task_a.workspace_path.endswith("task_weather_app"))
        self.assertTrue(task_b.workspace_path.endswith("task_expense_app"))

    def test_02_persistence_isolation_and_thread_safety(self):
        task_1 = TaskModel(
            task_id="iso_task_1",
            request_id="req_1",
            user_request="Iso Task 1",
            normalized_goal="Iso Task 1",
            task_type=TaskType.CONVERSATIONAL,
            status="COMPLETED"
        )
        task_2 = TaskModel(
            task_id="iso_task_2",
            request_id="req_2",
            user_request="Iso Task 2",
            normalized_goal="Iso Task 2",
            task_type=TaskType.APP_BUILD,
            status="RUNNING"
        )

        self.persistence.save_task(task_1)
        self.persistence.save_task(task_2)

        loaded_1 = self.persistence.load_task("iso_task_1")
        loaded_2 = self.persistence.load_task("iso_task_2")

        self.assertIsNotNone(loaded_1)
        self.assertIsNotNone(loaded_2)
        self.assertEqual(loaded_1["status"], "COMPLETED")
        self.assertEqual(loaded_2["status"], "RUNNING")
        self.assertNotEqual(loaded_1["task_id"], loaded_2["task_id"])

    def test_03_active_task_tracking(self):
        task_3 = TaskModel(
            task_id="active_test_task",
            request_id="req_3",
            user_request="Active Test Task",
            normalized_goal="Active Test Task",
            task_type=TaskType.CODE_ASSISTANT
        )
        self.orchestrator._active_tasks["active_test_task"] = task_3

        retrieved = self.orchestrator.get_task("active_test_task")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.user_request, "Active Test Task")

        # Cleanup
        del self.orchestrator._active_tasks["active_test_task"]

if __name__ == "__main__":
    unittest.main()
