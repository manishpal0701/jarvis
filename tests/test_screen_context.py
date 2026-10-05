"""
tests/test_screen_context.py
Unit tests for JARVIS Phase 4 WindowTracker, OCREngine, ScreenContext, and screen change detection.
"""

import os
import unittest
from vision.window_tracker import WindowTracker
from vision.ocr_engine import OCREngine
from vision.screen_context import ScreenContextAnalyzer
from vision.screen_capture import ScreenCapture
from vision.privacy_filter import PrivacyFilter


class TestScreenContext(unittest.TestCase):
    def setUp(self):
        self.tracker = WindowTracker()
        self.ocr = OCREngine()
        self.analyzer = ScreenContextAnalyzer(self.tracker, self.ocr)
        self.capture = ScreenCapture(max_dimension=800)

    def test_window_tracker(self):
        info = self.tracker.get_active_window_info()
        self.assertIn("window_title", info)
        self.assertIn("process_name", info)
        self.assertIn("app_category", info)
        self.assertIn("rect", info)

    def test_ocr_extraction_on_capture(self):
        frame = self.capture.capture_full_screen()
        if frame.image_path and os.path.exists(frame.image_path):
            ocr_res = self.ocr.extract_text(frame.image_path)
            self.assertIsNotNone(ocr_res)
            self.assertIsInstance(ocr_res.full_text, str)
            PrivacyFilter.cleanup_file(frame.image_path)

    def test_screen_context_analyzer(self):
        frame = self.capture.capture_full_screen()
        if frame.image_path and os.path.exists(frame.image_path):
            ctx = self.analyzer.analyze_frame(frame)
            self.assertIsNotNone(ctx)
            self.assertTrue(len(ctx.summary) > 0)
            self.assertIn("Foreground App", ctx.summary)
            PrivacyFilter.cleanup_file(frame.image_path)


if __name__ == "__main__":
    unittest.main()
