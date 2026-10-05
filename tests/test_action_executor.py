"""
tests/test_action_executor.py
Unit tests for JARVIS Phase 5 ActionExecutor, Focus Safety Verification, and Post-Action Verification.
"""

import unittest
from tools.computer.action_model import Action, ActionStatus, ActionTarget, ActionType
from tools.computer.action_executor import ActionExecutor


class TestActionExecutor(unittest.TestCase):

    def setUp(self):
        self.executor = ActionExecutor()

    def test_focus_verification(self):
        # Current active window title in test environment
        info = self.executor.window_tracker.get_active_window_info()
        proc = info.get("process_name", "")
        if proc:
            self.assertTrue(self.executor._verify_target_focus(proc))

    def test_action_cancellation(self):
        action = Action(action_id="act_cancel_test", action_type=ActionType.CLICK)
        self.executor.cancel_action("act_cancel_test")
        res = self.executor.execute_action(action)
        self.assertEqual(res.status, ActionStatus.CANCELLED)

    def test_open_app_action_execution(self):
        action = Action(
            action_type=ActionType.OPEN_APPLICATION,
            parameters={"app_name": "Notepad"},
            verification_required=False
        )
        res = self.executor.execute_action(action, skip_verification=True)
        self.assertEqual(res.status, ActionStatus.COMPLETED)


if __name__ == "__main__":
    unittest.main()
