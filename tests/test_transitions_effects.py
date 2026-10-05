"""
tests/test_transitions_effects.py
Unit tests for Transitions and Visual Effects Abstraction (Phase 3)
"""

import unittest
from unittest.mock import MagicMock
from video_editing.ai.edit_plan_schema import validate_edit_plan
from video_editing.ai.edit_plan_compiler import compile_and_execute_plan


class TestTransitionsEffects(unittest.TestCase):

    def setUp(self):
        self.metadata = {"duration": 30.0}
        self.scenes = [{"scene_id": "scene_001", "start": 0.0, "end": 10.0}]

    def test_01_valid_transition_schema(self):
        plan = {
            "edit_goal": "cinematic transition edit",
            "target_duration": 15,
            "aspect_ratio": "16:9",
            "style": "cinematic",
            "scenes": [{"source_scene_id": "scene_001"}],
            "operations": [
                {
                    "type": "transition",
                    "source_scene_id": "scene_001",
                    "transition_type": "dissolve",
                    "duration": 1.0,
                    "track_index": 0,
                    "clip_index": 0
                }
            ]
        }
        valid, res = validate_edit_plan(plan, self.metadata, self.scenes)
        self.assertTrue(valid)

    def test_02_unsupported_transition_schema_rejection(self):
        plan = {
            "edit_goal": "unsupported transition edit",
            "target_duration": 15,
            "aspect_ratio": "16:9",
            "style": "cinematic",
            "scenes": [{"source_scene_id": "scene_001"}],
            "operations": [
                {
                    "type": "transition",
                    "source_scene_id": "scene_001",
                    "transition_type": "super_star_spin"  # unsupported transition
                }
            ]
        }
        valid, res = validate_edit_plan(plan, self.metadata, self.scenes)
        self.assertFalse(valid)
        self.assertEqual(res.get("error", {}).get("code"), "UNSUPPORTED_TRANSITION")

    def test_03_valid_visual_effect_schema(self):
        plan = {
            "edit_goal": "opacity visual effect",
            "target_duration": 15,
            "aspect_ratio": "16:9",
            "style": "cinematic",
            "scenes": [{"source_scene_id": "scene_001"}],
            "operations": [
                {
                    "type": "visual_effect",
                    "source_scene_id": "scene_001",
                    "effect_name": "opacity",
                    "value": 80.0
                }
            ]
        }
        valid, res = validate_edit_plan(plan, self.metadata, self.scenes)
        self.assertTrue(valid)

    def test_04_unsupported_transition_runtime_propagation(self):
        mock_ctrl = MagicMock()
        mock_ctrl.ensure_project_open.return_value = {"ok": True}
        mock_ctrl.ensure_sequence.return_value = {"ok": True}
        mock_ctrl.apply_transition.return_value = {
            "success": False,
            "error": {
                "code": "NOT_SUPPORTED",
                "message": "NOT_SUPPORTED: Transition 'dissolve' is not supported by current Premiere ExtendScript DOM version."
            }
        }

        plan = {
            "edit_goal": "dissolve edit",
            "target_duration": 15,
            "aspect_ratio": "16:9",
            "style": "cinematic",
            "scenes": [{"source_scene_id": "scene_001"}],
            "operations": [
                {
                    "type": "transition",
                    "source_scene_id": "scene_001",
                    "transition_type": "dissolve"
                }
            ]
        }

        res = compile_and_execute_plan(plan, "C:/media/test.mp4", controller=mock_ctrl)
        self.assertFalse(res.get("success"))
        err_msg = res.get("error", {}).get("message", "")
        self.assertIn("NOT_SUPPORTED", err_msg)


if __name__ == "__main__":
    unittest.main()
