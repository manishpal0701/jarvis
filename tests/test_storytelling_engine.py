"""
tests/test_storytelling_engine.py
Unit tests for Qwen3 7-Style Storytelling Engine (Phase 3)
"""

import json
import unittest
from unittest.mock import patch, MagicMock
from video_editing.ai.edit_planner import generate_edit_plan, SYSTEM_PROMPT


class TestStorytellingEngine(unittest.TestCase):

    def test_01_system_prompt_includes_7_styles(self):
        styles = ["cinematic", "travel_reel", "instagram_reel", "youtube_video", "product_promo", "birthday_montage", "corporate_video"]
        for s in styles:
            self.assertIn(s, SYSTEM_PROMPT)

    @patch("video_editing.ai.edit_planner.AIResponseManager")
    def test_02_travel_reel_plan_generation(self, mock_ai_cls):
        mock_ai = MagicMock()
        mock_ai_cls.return_value = mock_ai

        valid_travel_plan = json.dumps({
            "edit_goal": "travel reel edit",
            "target_duration": 15,
            "aspect_ratio": "9:16",
            "style": "travel_reel",
            "scenes": [{"source_scene_id": "scene_001"}],
            "operations": [
                {"type": "place_video", "source_scene_id": "scene_001", "timeline_pos": 0.0},
                {"type": "transition", "source_scene_id": "scene_001", "transition_type": "cut", "duration": 0.5}
            ]
        })
        mock_ai.generate_response.return_value = valid_travel_plan

        media_analysis = {
            "metadata": {"duration": 30.0, "resolution": "1080x1920", "fps": 30.0},
            "scenes": [{"scene_id": "scene_001", "start": 0.0, "end": 10.0}]
        }

        res = generate_edit_plan("Make a fast travel reel synced to music", media_analysis)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("plan", {}).get("style"), "travel_reel")


if __name__ == "__main__":
    unittest.main()
