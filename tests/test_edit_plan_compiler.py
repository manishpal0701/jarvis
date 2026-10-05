"""
tests/test_edit_plan_compiler.py
Unit tests for Edit Plan Compiler (Phase 2)
"""

import unittest
from unittest.mock import MagicMock, patch
from video_editing.ai.edit_plan_compiler import compile_and_execute_plan


class TestEditPlanCompiler(unittest.TestCase):

    def setUp(self):
        self.plan = {
            "edit_goal": "test reel",
            "target_duration": 15,
            "aspect_ratio": "16:9",
            "style": "cinematic",
            "scenes": [],
            "operations": [
                {"type": "place_video", "timeline_pos": 0.0, "track_index": 0},
                {"type": "trim", "track_type": "video", "track_index": 0, "clip_index": 0, "in": 1.0, "out": 4.0},
                {"type": "place_audio", "timeline_pos": 0.0, "track_index": 0}
            ]
        }

    # 10. Plan compilation to Phase 1 commands
    @patch("video_editing.software.premiere.PremiereProController")
    def test_10_plan_compilation(self, mock_controller_cls):
        mock_ctrl = MagicMock()
        mock_ctrl.ensure_project_open.return_value = {"ok": True}
        mock_ctrl.ensure_sequence.return_value = {"ok": True}
        mock_ctrl.place_video_clip.return_value = {"success": True, "result": {"action": "place_video"}}
        mock_ctrl.trim_clip.return_value = {"success": True, "result": {"action": "trim"}}
        mock_ctrl.place_audio_clip.return_value = {"success": True, "result": {"action": "place_audio"}}

        res = compile_and_execute_plan(self.plan, "C:/media/test.mp4", controller=mock_ctrl)

        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("planned_count"), 3)
        self.assertEqual(res.get("executed_count"), 3)
        mock_ctrl.place_video_clip.assert_called_once_with("C:/media/test.mp4", 0.0, track_index=0, overwrite=True)
        mock_ctrl.trim_clip.assert_called_once_with("video", 0, 0, in_time=1.0, out_time=4.0)
        mock_ctrl.place_audio_clip.assert_called_once_with("C:/media/test.mp4", 0.0, track_index=0, overwrite=True)


if __name__ == "__main__":
    unittest.main()
