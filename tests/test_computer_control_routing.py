"""
tests/test_computer_control_routing.py
Unit tests verifying desktop automation command recognition, multi-action planning,
and correct task classification routing to computer_automation_agent.
"""

import unittest
from agent.task_planner import TaskPlanner
from agent.task_model import TaskType
from tools.computer.desktop_automation_engine import DesktopAutomationEngine
from tools.computer.action_planner import ActionPlanner


class TestComputerControlRouting(unittest.TestCase):
    def test_desktop_command_detection(self):
        """Verify is_desktop_command recognizes single and compound desktop queries."""
        queries = [
            "chrome kholo",
            "notepad kholo",
            "open chrome",
            "chrome kholo aur youtube search karo",
            "volume 50 percent karo",
            "screenshot lo",
            "lock laptop",
            "youtube pe song play karo"
        ]
        for q in queries:
            with self.subTest(query=q):
                self.assertTrue(DesktopAutomationEngine.is_desktop_command(q), f"Failed for query: '{q}'")

    def test_task_planner_classification(self):
        """Verify TaskPlanner classifies desktop commands as TaskType.DESKTOP_AUTOMATION."""
        planner = TaskPlanner()
        task_type, is_complex = planner._classify_task("chrome kholo aur youtube search karo")
        self.assertEqual(task_type, TaskType.DESKTOP_AUTOMATION)

        task_type_2, _ = planner._classify_task("notepad open karo")
        self.assertEqual(task_type_2, TaskType.DESKTOP_AUTOMATION)

    def test_action_planner_compound_plan_generation(self):
        """Verify ActionPlanner creates multi-action plans for compound requests."""
        planner = ActionPlanner()
        plan = planner.create_plan_from_request("chrome kholo aur youtube search karo")
        self.assertGreaterEqual(len(plan.actions), 2)


if __name__ == "__main__":
    unittest.main()
