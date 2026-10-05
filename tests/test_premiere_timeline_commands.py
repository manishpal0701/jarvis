"""
tests/test_premiere_timeline_commands.py
Unit Test Suite for Jarvis Premiere Pro Timeline Engine Commands (Phase 1)
"""

import unittest
from unittest.mock import patch, MagicMock
from video_editing.software.premiere import PremiereProController


class TestPremiereTimelineCommands(unittest.TestCase):

    def setUp(self):
        self.controller = PremiereProController()

    # 1. Command schema validation
    @patch("video_editing.software.premiere._send_command")
    def test_01_command_schema_validation(self, mock_send):
        mock_send.return_value = {
            "success": True,
            "command": "insertClip",
            "result": {"action": "insertClip"},
            "error": None
        }
        res = self.controller.insert_clip("sample.mp4", 5.0, "video", 0)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("command"), "insertClip")
        self.assertIn("action", res.get("result", {}))

    # 2. Invalid command rejection (simulated bridge rejection)
    @patch("requests.post")
    def test_02_invalid_command_rejection(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "success": False,
            "command": "invalidCommand",
            "result": None,
            "error": {"code": "UNKNOWN_COMMAND", "message": "Command is not supported."}
        }
        mock_post.return_value = mock_resp

        from video_editing.software.premiere import _send_command
        res = _send_command("invalidCommand")
        self.assertFalse(res.get("success"))
        self.assertEqual(res.get("error", {}).get("code"), "UNKNOWN_COMMAND")

    # 3. Invalid track rejection
    def test_03_invalid_track_rejection(self):
        with self.assertRaises(ValueError):
            self.controller.place_video_clip("clip.mp4", 0.0, track_index=-1)

        with self.assertRaises(ValueError):
            self.controller.move_clip("video", track_index=-1, clip_index=0, new_pos=2.0)

    # 4. Negative timestamp rejection
    def test_04_negative_timestamp_rejection(self):
        with self.assertRaises(ValueError):
            self.controller.place_video_clip("clip.mp4", timeline_pos=-5.0)

        with self.assertRaises(ValueError):
            self.controller.move_clip("video", 0, 0, new_pos=-1.0)

    # 5. Insert command generation payload
    @patch("video_editing.software.premiere._send_command")
    def test_05_insert_command_generation(self, mock_send):
        self.controller.insert_clip("clip.mp4", 12.5, "video", 1)
        mock_send.assert_called_once_with("insertClip", {
            "clipPath": "clip.mp4",
            "timelinePos": 12.5,
            "trackType": "video",
            "trackIndex": 1
        })

    # 6. Move command generation payload
    @patch("video_editing.software.premiere._send_command")
    def test_06_move_command_generation(self, mock_send):
        self.controller.move_clip("video", 0, 2, 18.0)
        mock_send.assert_called_once_with("moveClip", {
            "trackType": "video",
            "trackIndex": 0,
            "clipIndex": 2,
            "newPos": 18.0
        })

    # 7. Trim command generation payload
    @patch("video_editing.software.premiere._send_command")
    def test_07_trim_command_generation(self, mock_send):
        self.controller.trim_clip("video", 0, 0, in_time=2.0, out_time=8.5)
        mock_send.assert_called_once_with("trimClip", {
            "trackType": "video",
            "trackIndex": 0,
            "clipIndex": 0,
            "inTime": 2.0,
            "outTime": 8.5
        })

    # 8. Split command generation payload
    @patch("video_editing.software.premiere._send_command")
    def test_08_split_command_generation(self, mock_send):
        self.controller.split_clip("video", 0, 1, split_time=6.0)
        mock_send.assert_called_once_with("splitClip", {
            "trackType": "video",
            "trackIndex": 0,
            "clipIndex": 1,
            "splitTime": 6.0
        })

    # 9. Delete command generation payload
    @patch("video_editing.software.premiere._send_command")
    def test_09_delete_command_generation(self, mock_send):
        self.controller.delete_clip("video", 0, 0, ripple=True)
        mock_send.assert_called_once_with("deleteClip", {
            "trackType": "video",
            "trackIndex": 0,
            "clipIndex": 0,
            "ripple": True
        })

    # 10. Audio track command generation payload
    @patch("video_editing.software.premiere._send_command")
    def test_10_audio_track_command_generation(self, mock_send):
        self.controller.place_audio_clip("music.mp3", 0.0, track_index=1, overwrite=True)
        mock_send.assert_called_once_with("overwriteClip", {
            "clipPath": "music.mp3",
            "timelinePos": 0.0,
            "trackType": "audio",
            "trackIndex": 1
        })

    # 11. Video track command generation payload
    @patch("video_editing.software.premiere._send_command")
    def test_11_video_track_command_generation(self, mock_send):
        self.controller.place_video_clip("video.mp4", 4.0, track_index=2, overwrite=False)
        mock_send.assert_called_once_with("insertClip", {
            "clipPath": "video.mp4",
            "timelinePos": 4.0,
            "trackType": "video",
            "trackIndex": 2
        })

    # 12. Timeline response parsing
    @patch("video_editing.software.premiere._send_command")
    def test_12_timeline_response_parsing(self, mock_send):
        mock_send.return_value = {
            "success": True,
            "command": "readTimelineDetailed",
            "result": {
                "videoTrackCount": 2,
                "audioTrackCount": 2,
                "videoClipCount": 1,
                "audioClipCount": 1,
                "clips": [
                    {"trackType": "video", "trackIndex": 0, "name": "VClip1"},
                    {"trackType": "audio", "trackIndex": 0, "name": "AClip1"}
                ]
            },
            "error": None
        }
        res = self.controller.read_timeline_detailed()
        self.assertTrue(res.get("success"))
        result = res.get("result", {})
        self.assertEqual(result.get("videoTrackCount"), 2)
        self.assertEqual(len(result.get("clips", [])), 2)

    # 13. Error response parsing
    @patch("video_editing.software.premiere._send_command")
    def test_13_error_response_parsing(self, mock_send):
        mock_send.return_value = {
            "success": False,
            "command": "trimClip",
            "result": None,
            "error": {
                "code": "EXECUTION_FAILED",
                "message": "Clip index out of bounds."
            }
        }
        res = self.controller.trim_clip("video", 0, 99, in_time=1.0)
        self.assertFalse(res.get("success"))
        self.assertIsNotNone(res.get("error"))
        self.assertEqual(res.get("error", {}).get("code"), "EXECUTION_FAILED")

    # 14. Existing getProjectInfo compatibility
    @patch("video_editing.software.premiere._send_command")
    def test_14_existing_get_project_info_compatibility(self, mock_send):
        mock_send.return_value = {"ok": True, "hasProject": True, "projectName": "Jarvis_Edit"}
        res = self.controller.get_project_info()
        mock_send.assert_called_once_with("getProjectInfo")
        self.assertTrue(res.get("ok"))

    # 15. Existing importClip compatibility
    @patch("os.path.isfile", return_value=True)
    @patch("video_editing.software.premiere._send_command")
    def test_15_existing_import_clip_compatibility(self, mock_send, mock_isfile):
        mock_send.return_value = {"ok": True, "imported": ["C:/media/test.mp4"]}
        res = self.controller.import_clip("C:/media/test.mp4")
        mock_send.assert_called_once_with("importClip", {"path": "C:/media/test.mp4"})
        self.assertTrue(res.get("ok"))

    # 16. Existing placeClip compatibility
    @patch("video_editing.software.premiere._send_command")
    def test_16_existing_place_clip_compatibility(self, mock_send):
        mock_send.return_value = {"ok": True, "clipName": "test.mp4", "timelinePos": 0.0}
        res = self.controller.place_clip_on_timeline("test.mp4", 0.0)
        mock_send.assert_called_once_with("placeClip", {"clipPath": "test.mp4", "timelinePos": 0.0})
        self.assertTrue(res.get("ok"))


if __name__ == "__main__":
    unittest.main()
