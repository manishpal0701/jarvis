"""
tests/test_export_verifier.py
Unit tests for ffprobe Output File Verifier (Phase 4)
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from video_editing.export.export_verifier import verify_output_file


class TestExportVerifier(unittest.TestCase):

    # 1. Missing File Detection
    def test_01_missing_output_file(self):
        res = verify_output_file(r"C:\nonexistent_export_dir\missing.mp4")
        self.assertFalse(res.get("success"))
        self.assertFalse(res.get("verified"))
        self.assertEqual(res.get("error", {}).get("code"), "OUTPUT_NOT_FOUND")

    # 2. Zero-Byte File Detection
    def test_02_zero_byte_output_file(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            res = verify_output_file(tmp_path)
            self.assertFalse(res.get("success"))
            self.assertEqual(res.get("error", {}).get("code"), "ZERO_BYTE_OUTPUT")
        finally:
            if os.path.isfile(tmp_path):
                os.remove(tmp_path)

    # 3. Successful Verification Mock
    @patch("os.path.isfile", return_value=True)
    @patch("os.path.getsize", return_value=1048576)
    @patch("builtins.open", MagicMock())
    @patch("video_editing.export.export_verifier._run_ffprobe")
    def test_03_successful_verification(self, mock_ffprobe, mock_size, mock_file):
        mock_ffprobe.return_value = {
            "duration": 15.0,
            "has_video": True,
            "has_audio": True,
            "width": 1080,
            "height": 1920,
            "video_codec": "h264"
        }

        expected = {
            "resolution": "1080x1920",
            "audio_enabled": True
        }

        res = verify_output_file(r"C:\Exports\reel.mp4", expected_config=expected)
        self.assertTrue(res.get("success"))
        self.assertTrue(res.get("verified"))
        self.assertEqual(res.get("duration"), 15.0)
        self.assertEqual(res.get("video", {}).get("resolution"), "1080x1920")


if __name__ == "__main__":
    unittest.main()
