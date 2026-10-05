"""
tests/test_beat_aware_planning.py
Unit tests for Beat-Aware Edit Planning (Phase 3)
"""

import unittest
from video_editing.ai.edit_plan_schema import validate_edit_plan


class TestBeatAwarePlanning(unittest.TestCase):

    def setUp(self):
        self.metadata = {
            "duration": 30.0,
            "audio_analysis": {
                "bpm": 120.0,
                "beat_timestamps": [0.5, 1.0, 1.5, 2.0],
                "tempo_confidence": 0.95
            }
        }
        self.scenes = [{"scene_id": "scene_001", "start": 0.0, "end": 10.0}]

    def test_01_valid_beat_aligned_operation(self):
        plan = {
            "edit_goal": "beat sync instagram reel",
            "target_duration": 15,
            "aspect_ratio": "9:16",
            "style": "instagram_reel",
            "scenes": [{"source_scene_id": "scene_001"}],
            "operations": [
                {
                    "type": "align_audio_beat",
                    "source_scene_id": "scene_001",
                    "timeline_pos": 0.0,
                    "beat_time": 0.5
                }
            ]
        }
        valid, res = validate_edit_plan(plan, self.metadata, self.scenes)
        self.assertTrue(valid)
        self.assertTrue(res.get("success"))

    def test_02_negative_beat_time_rejection(self):
        plan = {
            "edit_goal": "beat sync reel",
            "target_duration": 15,
            "aspect_ratio": "9:16",
            "style": "instagram_reel",
            "scenes": [{"source_scene_id": "scene_001"}],
            "operations": [
                {
                    "type": "align_audio_beat",
                    "source_scene_id": "scene_001",
                    "beat_time": -1.5
                }
            ]
        }
        valid, res = validate_edit_plan(plan, self.metadata, self.scenes)
        self.assertFalse(valid)
        self.assertEqual(res.get("error", {}).get("code"), "NEGATIVE_TIMESTAMP")


if __name__ == "__main__":
    unittest.main()
