"""
tests/test_ai_edit_planner.py
Unit tests for Ollama AI Edit Planner (Phase 2)
"""

import json
import unittest
from unittest.mock import patch, MagicMock
from video_editing.ai.edit_planner import generate_edit_plan, _parse_json_from_response


class TestAIEditPlanner(unittest.TestCase):

    def setUp(self):
        self.media_analysis = {
            "metadata": {"duration": 60.0, "resolution": "1920x1080", "fps": 30.0},
            "scenes": [
                {"scene_id": "scene_001", "start": 0.0, "end": 10.0, "duration": 10.0}
            ]
        }

    # 5. Valid Ollama JSON plan parsing & generation
    @patch("video_editing.ai.edit_planner.AIResponseManager")
    def test_05_valid_ollama_json_plan_generation(self, mock_ai_cls):
        mock_ai = MagicMock()
        mock_ai_cls.return_value = mock_ai

        valid_json_response = json.dumps({
            "edit_goal": "cinematic reel",
            "target_duration": 10,
            "aspect_ratio": "9:16",
            "style": "cinematic",
            "scenes": [{"source_scene_id": "scene_001", "source_start": 0.0, "source_end": 5.0}],
            "operations": [
                {"type": "place_video", "source_scene_id": "scene_001", "timeline_pos": 0.0, "track_index": 0}
            ]
        })
        mock_ai.generate_response.return_value = valid_json_response

        res = generate_edit_plan("Create a cinematic reel", self.media_analysis)
        self.assertTrue(res.get("success"))
        self.assertIsNotNone(res.get("plan"))
        self.assertIsNone(res.get("error"))

    # 6. Invalid Ollama JSON parsing
    def test_06_invalid_ollama_json_parsing(self):
        parsed = _parse_json_from_response("I cannot create a video plan because of XYZ")
        self.assertIsNone(parsed)

        code_block = "Here is your plan:\n```json\n{\"edit_goal\": \"reel\", \"target_duration\": 10, \"aspect_ratio\": \"9:16\", \"style\": \"fast\", \"scenes\": [], \"operations\": [{\"type\": \"place_video\", \"timeline_pos\": 0}]}\n```"
        parsed_block = _parse_json_from_response(code_block)
        self.assertIsNotNone(parsed_block)
        self.assertEqual(parsed_block.get("edit_goal"), "reel")


if __name__ == "__main__":
    unittest.main()
