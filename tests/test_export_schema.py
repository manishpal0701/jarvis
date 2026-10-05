"""
tests/test_export_schema.py
Unit tests for Phase 4 Export Schema & Path Safety Validation
"""

import os
import unittest
from video_editing.export.export_schema import validate_export_config, validate_output_path


class TestExportSchema(unittest.TestCase):

    def setUp(self):
        self.valid_config = {
            "format": "mp4",
            "codec": "h264",
            "resolution": "1080x1920",
            "fps": 30,
            "output_path": r"C:\Exports\test_reel.mp4",
            "overwrite": True
        }

    # 1. MP4 / H264 Valid Config
    def test_01_valid_export_config(self):
        valid, res = validate_export_config(self.valid_config)
        self.assertTrue(valid)
        self.assertTrue(res.get("success"))

    # 2. Invalid Format Rejection
    def test_02_invalid_format_rejection(self):
        cfg = dict(self.valid_config, format="avi")
        valid, res = validate_export_config(cfg)
        self.assertFalse(valid)
        self.assertEqual(res.get("error", {}).get("code"), "INVALID_FORMAT")

    # 3. Invalid Codec Rejection
    def test_03_invalid_codec_rejection(self):
        cfg = dict(self.valid_config, codec="prores")
        valid, res = validate_export_config(cfg)
        self.assertFalse(valid)
        self.assertEqual(res.get("error", {}).get("code"), "INVALID_CODEC")

    # 4. Invalid Resolution Rejection
    def test_04_invalid_resolution_rejection(self):
        cfg = dict(self.valid_config, resolution="invalid_res")
        valid, res = validate_export_config(cfg)
        self.assertFalse(valid)
        self.assertEqual(res.get("error", {}).get("code"), "INVALID_RESOLUTION")

    # 5. Negative FPS Rejection
    def test_05_negative_fps_rejection(self):
        cfg = dict(self.valid_config, fps=-30)
        valid, res = validate_export_config(cfg)
        self.assertFalse(valid)
        self.assertEqual(res.get("error", {}).get("code"), "INVALID_FPS")

    # 6. Relative Path Rejection
    def test_06_relative_path_rejection(self):
        cfg = dict(self.valid_config, output_path="relative/path/video.mp4")
        valid, res = validate_export_config(cfg)
        self.assertFalse(valid)
        self.assertEqual(res.get("error", {}).get("code"), "RELATIVE_PATH_REJECTED")

    # 7. Path Traversal Rejection
    def test_07_path_traversal_rejection(self):
        cfg = dict(self.valid_config, output_path=r"C:\Exports\..\..\Windows\video.mp4")
        valid, res = validate_export_config(cfg)
        self.assertFalse(valid)
        self.assertEqual(res.get("error", {}).get("code"), "PATH_TRAVERSAL_REJECTED")

    # 8. Invalid Extension Rejection
    def test_08_invalid_extension_rejection(self):
        cfg = dict(self.valid_config, output_path=r"C:\Exports\video.mkv")
        valid, res = validate_export_config(cfg)
        self.assertFalse(valid)
        self.assertEqual(res.get("error", {}).get("code"), "INVALID_EXTENSION")


if __name__ == "__main__":
    unittest.main()
