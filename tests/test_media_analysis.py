"""
tests/test_media_analysis.py
Unit tests for Media Analysis Engine (Phase 2)
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from video_editing.analysis.media_analyzer import analyze_media, extract_representative_frames, detect_scenes, _fallback_scenes


class TestMediaAnalysis(unittest.TestCase):

    # 1. Media metadata extraction (valid mock video path / fallback)
    @patch("os.path.isfile", return_value=True)
    @patch("video_editing.analysis.media_analyzer._run_ffprobe")
    def test_01_media_metadata_extraction(self, mock_ffprobe, mock_isfile):
        mock_ffprobe.return_value = {
            "duration": 182.4,
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "frame_count": 5472,
            "video_codec": "h264",
            "audio_presence": True,
            "audio_duration": 182.4
        }
        res = analyze_media("C:/media/sample.mp4")
        self.assertEqual(res["status"], "ANALYZED")
        self.assertEqual(res["duration"], 182.4)
        self.assertEqual(res["resolution"], "1920x1080")
        self.assertEqual(res["fps"], 30.0)
        self.assertEqual(res["video_codec"], "h264")
        self.assertTrue(res["audio_presence"])

    # 2. Invalid media handling
    def test_02_invalid_media_handling(self):
        res = analyze_media("C:/nonexistent_file_path_123.mp4")
        self.assertEqual(res["status"], "NOT_FOUND")
        self.assertEqual(res["duration"], 0.0)
        self.assertEqual(res["resolution"], "UNKNOWN")
        self.assertEqual(res["video_codec"], "UNKNOWN")
        self.assertFalse(res["audio_presence"])

    # 3. Scene detection output
    def test_03_scene_detection_fallback_output(self):
        scenes = _fallback_scenes(duration=15.0, segment_len=5.0)
        self.assertEqual(len(scenes), 3)
        self.assertEqual(scenes[0]["scene_id"], "scene_001")
        self.assertEqual(scenes[0]["start"], 0.0)
        self.assertEqual(scenes[0]["end"], 5.0)
        self.assertEqual(scenes[1]["start"], 5.0)
        self.assertEqual(scenes[1]["end"], 10.0)

    # 4. Unknown media data handling
    @patch("os.path.isfile", return_value=True)
    @patch("video_editing.analysis.media_analyzer._run_ffprobe", return_value={})
    @patch("video_editing.analysis.media_analyzer._run_opencv_meta", return_value={})
    def test_04_unknown_media_data_handling(self, mock_cv, mock_ff, mock_file):
        res = analyze_media("C:/media/corrupt.mp4")
        self.assertEqual(res["status"], "ANALYZED")
        self.assertEqual(res["resolution"], "UNKNOWN")
        self.assertEqual(res["video_codec"], "UNKNOWN")
        self.assertEqual(res["audio_duration"], "NOT_AVAILABLE")


if __name__ == "__main__":
    unittest.main()
