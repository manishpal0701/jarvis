"""
tests/test_export_presets.py
Unit tests for Render Presets (Phase 4)
"""

import unittest
from video_editing.export.export_presets import (
    PRESET_INSTAGRAM_REEL,
    PRESET_YOUTUBE_SHORT,
    PRESET_YOUTUBE,
    PRESET_LANDSCAPE,
    PRESET_CUSTOM,
    get_preset_config
)


class TestExportPresets(unittest.TestCase):

    def test_01_instagram_reel_preset(self):
        cfg = get_preset_config(PRESET_INSTAGRAM_REEL, r"C:\Exports\reel.mp4")
        self.assertEqual(cfg["preset_name"], PRESET_INSTAGRAM_REEL)
        self.assertEqual(cfg["resolution"], "1080x1920")
        self.assertEqual(cfg["format"], "mp4")
        self.assertEqual(cfg["codec"], "h264")
        self.assertTrue(cfg["audio_enabled"])

    def test_02_youtube_short_preset(self):
        cfg = get_preset_config(PRESET_YOUTUBE_SHORT, r"C:\Exports\yt_short.mp4")
        self.assertEqual(cfg["preset_name"], PRESET_YOUTUBE_SHORT)
        self.assertEqual(cfg["resolution"], "1080x1920")

    def test_03_youtube_landscape_preset(self):
        cfg = get_preset_config(PRESET_YOUTUBE, r"C:\Exports\yt_main.mp4")
        self.assertEqual(cfg["preset_name"], PRESET_YOUTUBE)
        self.assertEqual(cfg["resolution"], "1920x1080")

    def test_04_custom_preset_override(self):
        override = {"resolution": "3840x2160", "fps": 60}
        cfg = get_preset_config(PRESET_CUSTOM, r"C:\Exports\4k.mp4", custom_override=override)
        self.assertEqual(cfg["preset_name"], PRESET_CUSTOM)
        self.assertEqual(cfg["resolution"], "3840x2160")
        self.assertEqual(cfg["fps"], 60)


if __name__ == "__main__":
    unittest.main()
