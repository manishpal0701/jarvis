"""
tests/test_screen_capture.py
Unit tests for JARVIS Phase 4 ScreenCapture, ScreenFrame, and PrivacyFilter.
"""

import os
import unittest
from vision.screen_frame import ScreenFrame
from vision.screen_capture import ScreenCapture
from vision.privacy_filter import PrivacyFilter


class TestScreenCapture(unittest.TestCase):
    def setUp(self):
        self.capture = ScreenCapture(max_dimension=1280)
        self.privacy = PrivacyFilter.get_instance()

    def test_screen_frame_dataclass(self):
        frame = ScreenFrame(width=1920, height=1080, capture_source="full_screen")
        self.assertTrue(frame.frame_id.startswith("frame_"))
        self.assertEqual(frame.width, 1920)
        self.assertEqual(frame.height, 1080)
        d = frame.to_dict()
        self.assertEqual(d["capture_source"], "full_screen")

    def test_full_screen_capture(self):
        frame = self.capture.capture_full_screen()
        self.assertIsNotNone(frame)
        self.assertEqual(frame.capture_source, "full_screen")
        if frame.image_path:
            self.assertTrue(os.path.exists(frame.image_path))
            self.assertTrue(frame.image_path.endswith(".png"))
            # Test privacy cleanup
            deleted = self.privacy.cleanup_file(frame.image_path)
            self.assertTrue(deleted)
            self.assertFalse(os.path.exists(frame.image_path))

    def test_region_capture(self):
        frame = self.capture.capture_region(bbox=(0, 0, 400, 300))
        self.assertIsNotNone(frame)
        self.assertEqual(frame.capture_source, "region")
        self.assertEqual(frame.region, (0, 0, 400, 300))
        if frame.image_path:
            self.assertTrue(os.path.exists(frame.image_path))
            self.privacy.cleanup_file(frame.image_path)

    def test_privacy_filter_masking(self):
        text = "Here is my secret token: sk-abcdef1234567890abcdef12 and password=Secret123!"
        filtered = self.privacy.filter_text(text)
        self.assertNotIn("sk-abcdef1234567890abcdef12", filtered)
        self.assertIn("[REDACTED_SECRET]", filtered)


if __name__ == "__main__":
    unittest.main()
