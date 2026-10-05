"""
tests/test_action_planner.py
Unit tests for JARVIS Phase 5 ActionPlanner, NL-to-ActionPlan translation, and Phase 1 context resolution.
"""

import unittest
from tools.computer.action_planner import ActionPlanner
from tools.computer.action_model import ActionType, RiskLevel
from conversation.conversation_manager import ConversationManager


class TestActionPlanner(unittest.TestCase):

    def setUp(self):
        self.planner = ActionPlanner()
        self.conversation_manager = ConversationManager.get_instance()

    def test_open_app_plan_creation(self):
        plan = self.planner.create_plan_from_request("Jarvis, Notepad kholo")
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan.actions), 1)
        self.assertEqual(plan.actions[0].action_type, ActionType.OPEN_APPLICATION)

    def test_scroll_plan_creation(self):
        plan = self.planner.create_plan_from_request("page ko neeche scroll karo")
        self.assertIsNotNone(plan)
        self.assertEqual(plan.actions[0].action_type, ActionType.SCROLL)
        self.assertEqual(plan.actions[0].parameters["amount"], -300)

    def test_type_plan_creation(self):
        plan = self.planner.create_plan_from_request("type Hello Boss")
        self.assertIsNotNone(plan)
        self.assertEqual(plan.actions[0].action_type, ActionType.TYPE)
        self.assertEqual(plan.actions[0].parameters["text"], "Hello Boss")

    def test_context_resolution_isme(self):
        self.conversation_manager.set_active_context(entity="VS Code")
        resolved, active = self.planner._resolve_context_references("isme terminal kholo")
        self.assertIn("in VS Code", resolved)
        self.assertEqual(active, "VS Code")


if __name__ == "__main__":
    unittest.main()
