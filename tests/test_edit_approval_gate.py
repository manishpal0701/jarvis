"""
tests/test_edit_approval_gate.py
Unit tests for Human Approval Gate & Edit Plan State Machine (Phase 2)
"""

import unittest
from unittest.mock import patch, MagicMock
from video_editing.ai.edit_approval_gate import (
    EditApprovalGate,
    STATE_IDLE,
    STATE_WAITING_FOR_APPROVAL,
    STATE_COMPLETED,
    STATE_FAILED
)


class TestEditApprovalGate(unittest.TestCase):

    def setUp(self):
        self.gate = EditApprovalGate()

    # 11. Approval required before execution
    @patch("video_editing.ai.edit_approval_gate.analyze_media")
    @patch("video_editing.ai.edit_approval_gate.detect_scenes")
    @patch("video_editing.ai.edit_approval_gate.generate_edit_plan")
    def test_11_approval_required_before_execution(self, mock_plan, mock_scenes, mock_meta):
        mock_meta.return_value = {"status": "ANALYZED", "duration": 30.0}
        mock_scenes.return_value = [{"scene_id": "scene_001", "start": 0.0, "end": 10.0}]
        mock_plan.return_value = {
            "success": True,
            "plan": {
                "edit_goal": "travel reel",
                "target_duration": 10,
                "aspect_ratio": "9:16",
                "style": "cinematic",
                "scenes": [{"source_scene_id": "scene_001"}],
                "operations": [{"type": "place_video", "timeline_pos": 0.0}]
            }
        }

        # Submit request
        res = self.gate.submit_request("Make a travel reel", "C:/media/test.mp4")

        # Must pause at WAITING_FOR_APPROVAL
        self.assertEqual(self.gate.state, STATE_WAITING_FOR_APPROVAL)
        self.assertIsNotNone(res.get("preview_summary"))
        self.assertIn("bana do", res.get("preview_summary"))

    # 12. Approval starts execution
    @patch("video_editing.ai.edit_approval_gate.compile_and_execute_plan")
    @patch("video_editing.ai.edit_approval_gate.analyze_media")
    @patch("video_editing.ai.edit_approval_gate.detect_scenes")
    @patch("video_editing.ai.edit_approval_gate.generate_edit_plan")
    def test_12_approval_starts_execution(self, mock_plan, mock_scenes, mock_meta, mock_compile):
        mock_meta.return_value = {"status": "ANALYZED", "duration": 30.0}
        mock_scenes.return_value = [{"scene_id": "scene_001", "start": 0.0, "end": 10.0}]
        mock_plan.return_value = {
            "success": True,
            "plan": {
                "edit_goal": "travel reel",
                "target_duration": 10,
                "aspect_ratio": "9:16",
                "style": "cinematic",
                "scenes": [{"source_scene_id": "scene_001"}],
                "operations": [{"type": "place_video", "timeline_pos": 0.0}]
            }
        }
        mock_compile.return_value = {
            "success": True,
            "planned_count": 1,
            "executed_count": 1,
            "executed_operations": [],
            "error": None
        }

        self.gate.submit_request("Make a travel reel", "C:/media/test.mp4")

        # Process approval
        res = self.gate.process_approval("haan bana do")

        # Must proceed to execution and completion
        self.assertEqual(self.gate.state, STATE_COMPLETED)
        mock_compile.assert_called_once()

    # 13. Phase 1 command compatibility & rejection
    def test_13_rejection_resets_to_idle(self):
        self.gate.state = STATE_WAITING_FOR_APPROVAL
        res = self.gate.reject()
        self.assertEqual(self.gate.state, STATE_IDLE)
        self.assertTrue(res.get("success"))

    # 14. Timeline readback verification
    def test_14_timeline_readback_verification(self):
        mock_ctrl = MagicMock()
        mock_ctrl.read_timeline_detailed.return_value = {
            "success": True,
            "result": {
                "videoClipCount": 2,
                "audioClipCount": 1
            }
        }
        gate = EditApprovalGate(controller=mock_ctrl)
        gate.current_plan = {"operations": [{"type": "place_video"}, {"type": "place_video"}]}
        report = gate.verify_timeline({"planned_count": 2, "executed_count": 2})

        self.assertTrue(report.get("timeline_match"))
        self.assertEqual(report.get("planned_operations"), 2)
        self.assertEqual(report.get("executed_operations"), 2)

    # 15. Premiere NOT_SUPPORTED propagation
    @patch("video_editing.ai.edit_approval_gate.compile_and_execute_plan")
    def test_15_premiere_not_supported_propagation(self, mock_compile):
        mock_compile.return_value = {
            "success": False,
            "planned_count": 1,
            "executed_count": 0,
            "executed_operations": [],
            "error": {"code": "NOT_SUPPORTED", "message": "Razor operation not supported."}
        }
        self.gate.state = STATE_WAITING_FOR_APPROVAL
        self.gate.current_plan = {"operations": [{"type": "split"}]}

        res = self.gate.approve()
        self.assertEqual(self.gate.state, STATE_FAILED)
        self.assertIn("NOT_SUPPORTED", self.gate.last_error)


if __name__ == "__main__":
    unittest.main()
