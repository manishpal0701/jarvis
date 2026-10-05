"""
tests/test_action_model.py
Unit tests for JARVIS Phase 5 Action, ActionPlan, ActionTarget, and ActionResult data models.
"""

import unittest
from tools.computer.action_model import (
    Action, ActionPlan, ActionResult, ActionTarget, ActionStatus, ActionType, RiskLevel
)


class TestActionModel(unittest.TestCase):

    def test_action_target_dataclass(self):
        target = ActionTarget(
            semantic_label="Run button",
            bbox=(100, 200, 50, 30),
            center_x=125,
            center_y=215,
            confidence=0.95,
            frame_id="frame_01"
        )
        self.assertEqual(target.semantic_label, "Run button")
        self.assertEqual(target.center_x, 125)
        d = target.to_dict()
        self.assertEqual(d["confidence"], 0.95)

    def test_action_dataclass(self):
        action = Action(
            action_type=ActionType.CLICK,
            parameters={"x": 100, "y": 200},
            risk_level=RiskLevel.LOW,
            status=ActionStatus.PENDING
        )
        self.assertTrue(action.action_id.startswith("act_"))
        self.assertEqual(action.action_type, ActionType.CLICK)
        d = action.to_dict()
        self.assertEqual(d["risk_level"], "LOW")
        self.assertEqual(d["status"], "PENDING")

    def test_action_plan_dataclass(self):
        act1 = Action(action_type=ActionType.OPEN_APPLICATION, parameters={"app_name": "Notepad"})
        act2 = Action(action_type=ActionType.TYPE, parameters={"text": "Hello"})
        plan = ActionPlan(
            user_intent="Open Notepad and write Hello",
            actions=[act1, act2],
            risk_level=RiskLevel.LOW
        )
        self.assertTrue(plan.plan_id.startswith("plan_"))
        self.assertEqual(len(plan.actions), 2)
        d = plan.to_dict()
        self.assertEqual(len(d["actions"]), 2)

    def test_action_result_dataclass(self):
        res = ActionResult(
            action_id="act_123",
            status=ActionStatus.COMPLETED,
            verification_status="VERIFIED_SUCCESS",
            metadata={"clicked": True}
        )
        self.assertEqual(res.status, ActionStatus.COMPLETED)
        d = res.to_dict()
        self.assertEqual(d["verification_status"], "VERIFIED_SUCCESS")


if __name__ == "__main__":
    unittest.main()
