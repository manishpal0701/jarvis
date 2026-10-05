"""
tests/test_audio_analysis.py
Unit tests for Real Audio & Beat Analysis Engine (Phase 3)
"""

import unittest
from unittest.mock import patch, MagicMock
from video_editing.analysis.audio_analyzer import analyze_audio, _unavailable_payload


class TestAudioAnalysis(unittest.TestCase):

    # 1. Non-existent audio file handling
    def test_01_nonexistent_audio_file(self):
        res = analyze_audio("C:/nonexistent_audio_123.mp3")
        self.assertEqual(res["status"], "UNAVAILABLE")
        self.assertEqual(res["bpm"], "UNKNOWN")
        self.assertEqual(res["beat_timestamps"], [])
        self.assertEqual(res["tempo_confidence"], "NOT_AVAILABLE")

    # 2. Audio analysis mock success
    @patch("os.path.isfile", return_value=True)
    def test_02_audio_analysis_mock_success(self, mock_file):
        mock_librosa = MagicMock()
        mock_librosa.load.return_value = ("y_data", 22050)
        mock_librosa.get_duration.return_value = 60.0
        mock_librosa.beat.beat_track.return_value = (120.0, [10, 20, 30])
        mock_librosa.frames_to_time.return_value = [0.5, 1.0, 1.5]
        mock_librosa.effects.split.return_value = []

        with patch.dict("sys.modules", {"librosa": mock_librosa}):
            res = analyze_audio("C:/media/sample_song.mp3")
            self.assertEqual(res["status"], "ANALYZED")
            self.assertEqual(res["bpm"], 120.0)
            self.assertEqual(res["beat_timestamps"], [0.5, 1.0, 1.5])
            self.assertEqual(res["audio_duration"], 60.0)

    # 3. Audio analysis fallback
    def test_03_fallback_unavailable_payload(self):
        res = _unavailable_payload("Module missing")
        self.assertEqual(res["status"], "UNAVAILABLE")
        self.assertEqual(res["bpm"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
