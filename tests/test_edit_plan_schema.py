"""
tests/test_edit_plan_schema.py
Unit tests for AI Edit Plan Schema Validation (Phase 2)
"""

import unittest
from video_editing.ai.edit_plan_schema import validate_edit_plan


class TestEditPlanSchema(unittest.TestCase):

    def setUp(self):
        self.valid_plan = {
            "edit_goal": "cinematic travel reel",
            "target_duration": 30,
            "aspect_ratio": "9:16",
            "style": "cinematic",
            "scenes": [
                {"source_scene_id": "scene_001", "source_start": 0.0, "source_end": 5.0}
            ],
            "operations": [
                {
                    "type": "trim",
                    "source_scene_id": "scene_001",
                    "track_type": "video",
                    "track_index": 0,
                    "in": 1.0,
                    "out": 4.0,
                    "timeline_pos": 0.0
                }
            ]
        }
        self.metadata = {"duration": 60.0}
        self.scenes = [{"scene_id": "scene_001", "start": 0.0, "end": 5.0}]

    # 5. Valid Ollama JSON plan
    def test_05_valid_ollama_json_plan(self):
        valid, res = validate_edit_plan(self.valid_plan, self.metadata, self.scenes)
        self.assertTrue(valid)
        self.assertTrue(res.get("success"))
        self.assertIsNone(res.get("error"))

    # 6. Invalid Ollama JSON format
    def test_06_invalid_ollama_json_format(self):
        valid, res = validate_edit_plan("not a json dict", self.metadata, self.scenes)
        self.assertFalse(valid)
        self.assertFalse(res.get("success"))
        self.assertEqual(res.get("error", {}).get("code"), "INVALID_FORMAT")

    # 7. Invalid scene ID
    def test_07_invalid_scene_id(self):
        invalid_plan = dict(self.valid_plan)
        invalid_plan["operations"] = [
            {
                "type": "trim",
                "source_scene_id": "scene_999",  # non-existent scene
                "in": 1.0,
                "out": 4.0
            }
        ]
        valid, res = validate_edit_plan(invalid_plan, self.metadata, self.scenes)
        self.assertFalse(valid)
        self.assertEqual(res.get("error", {}).get("code"), "INVALID_SCENE_ID")

    # 8. Negative timestamp rejection
    def test_08_negative_timestamp_rejection(self):
        invalid_plan = dict(self.valid_plan)
        invalid_plan["operations"] = [
            {
                "type": "trim",
                "source_scene_id": "scene_001",
                "in": -2.0,  # negative timestamp
                "out": 4.0
            }
        ]
        valid, res = validate_edit_plan(invalid_plan, self.metadata, self.scenes)
        self.assertFalse(valid)
        self.assertEqual(res.get("error", {}).get("code"), "NEGATIVE_TIMESTAMP")

    # 9. Invalid operation rejection
    def test_09_invalid_operation_rejection(self):
        invalid_plan = dict(self.valid_plan)
        invalid_plan["operations"] = [
            {
                "type": "magic_effect",  # unsupported operation
                "source_scene_id": "scene_001"
            }
        ]
        valid, res = validate_edit_plan(invalid_plan, self.metadata, self.scenes)
        self.assertFalse(valid)
        self.assertEqual(res.get("error", {}).get("code"), "UNSUPPORTED_OPERATION")


if __name__ == "__main__":
    unittest.main()
