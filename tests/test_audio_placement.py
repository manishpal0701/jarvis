"""
tests/test_audio_placement.py
Unit tests for Audio Track Placement & Manipulation (Phase 3)
"""

import unittest
from unittest.mock import patch, MagicMock
from video_editing.software.premiere import PremiereProController


class TestAudioPlacement(unittest.TestCase):

    @patch("video_editing.software.premiere._send_command")
    def test_01_place_audio_clip(self, mock_send):
        mock_send.return_value = {"success": True, "result": {"action": "placeAudio"}}
        ctrl = PremiereProController()

        res = ctrl.place_audio_clip("C:/media/music.mp3", 0.0, track_index=1, overwrite=True)
        self.assertTrue(res.get("success"))
        mock_send.assert_called_once_with("overwriteClip", {
            "clipPath": "C:/media/music.mp3",
            "timelinePos": 0.0,
            "trackType": "audio",
            "trackIndex": 1
        })

    def test_02_negative_audio_track_index_rejection(self):
        ctrl = PremiereProController()
        with self.assertRaises(ValueError):
            ctrl.place_audio_clip("C:/media/music.mp3", 0.0, track_index=-1)

    def test_03_move_and_trim_audio_clip(self):
        ctrl = PremiereProController()
        ctrl.move_clip = MagicMock(return_value={"success": True})
        ctrl.trim_clip = MagicMock(return_value={"success": True})

        ctrl.move_audio_clip(0, 0, 5.0)
        ctrl.move_clip.assert_called_once_with("audio", 0, 0, 5.0)

        ctrl.trim_audio_clip(0, 0, in_time=1.0, out_time=4.0)
        ctrl.trim_clip.assert_called_once_with("audio", 0, 0, 1.0, 4.0)


if __name__ == "__main__":
    unittest.main()
