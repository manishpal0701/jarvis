"""
tests/test_export_manager.py
Unit tests for Natural Export Intent Parsing & Export Manager (Phase 4)
"""

import unittest
from video_editing.export.export_presets import (
    PRESET_INSTAGRAM_REEL,
    PRESET_YOUTUBE_SHORT,
    PRESET_YOUTUBE,
    PRESET_LANDSCAPE
)
from video_editing.export.export_manager import parse_export_intent, ExportManager


class TestExportManager(unittest.TestCase):

    def test_01_parse_export_intents(self):
        self.assertEqual(parse_export_intent("Instagram ke liye export karo"), PRESET_INSTAGRAM_REEL)
        self.assertEqual(parse_export_intent("YouTube Short export karo"), PRESET_YOUTUBE_SHORT)
        self.assertEqual(parse_export_intent("YouTube 1080p video render karo"), PRESET_YOUTUBE)
        self.assertEqual(parse_export_intent("Landscape video export karo"), PRESET_LANDSCAPE)

    def test_02_configure_from_user_request(self):
        mgr = ExportManager()
        res = mgr.configure_from_user_request("Instagram ke liye export karo", r"C:\Exports\reel.mp4", overwrite=True)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("config", {}).get("preset_name"), PRESET_INSTAGRAM_REEL)
        self.assertTrue(res.get("config", {}).get("overwrite"))


if __name__ == "__main__":
    unittest.main()
