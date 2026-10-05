"""
tests/test_video_intent_routing.py
Comprehensive Integration & Unit Test Suite for Jarvis Video Editing Intent Routing.
Validates intent classification, routing priority, memory immunity, source media protection,
and human approval gate safety.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from video_editing.video_intent_router import (
    classify_video_intent,
    INTENT_VIDEO_EDIT,
    INTENT_VIDEO_EXPORT,
    INTENT_VIDEO_ANALYSIS,
    INTENT_GENERAL_CONVERSATION
)
from video_editing.video_session_manager import VideoEditingSessionManager
from conversation.command_router import CommandRouter
from memory.memory_manager import MemoryManager


class TestVideoIntentRouting(unittest.TestCase):

    def setUp(self):
        self.session_mgr = VideoEditingSessionManager.get_instance()
        self.session_mgr.reset_session()

        # Create dummy sample video file for source media tests
        self.temp_dir = tempfile.mkdtemp()
        self.sample_video = os.path.join(self.temp_dir, "test_clip.mp4")
        with open(self.sample_video, "wb") as f:
            f.write(b"dummy_video_content")

    def tearDown(self):
        self.session_mgr.reset_session()
        if os.path.exists(self.sample_video):
            try:
                os.remove(self.sample_video)
            except Exception:
                pass
        if os.path.exists(self.temp_dir):
            try:
                os.rmdir(self.temp_dir)
            except Exception:
                pass

    # 1. "meri ek cinematic video edit karke do" -> VIDEO_EDIT, NOT GENERAL_CONVERSATION
    def test_01_cinematic_edit_command_intent(self):
        cmd = "meri ek cinematic video edit karke do"
        res = classify_video_intent(cmd)
        self.assertEqual(res["intent"], INTENT_VIDEO_EDIT)
        self.assertNotEqual(res["intent"], INTENT_GENERAL_CONVERSATION)

    # 2. "video edit karo" -> VIDEO_EDIT
    def test_02_video_edit_karo_intent(self):
        cmd = "video edit karo"
        res = classify_video_intent(cmd)
        self.assertEqual(res["intent"], INTENT_VIDEO_EDIT)

    # 3. "cinematic video bana do" -> VIDEO_EDIT
    def test_03_cinematic_video_bana_do_intent(self):
        cmd = "cinematic video bana do"
        res = classify_video_intent(cmd)
        self.assertEqual(res["intent"], INTENT_VIDEO_EDIT)

    # 4. "Instagram reel bana do" -> VIDEO_EDIT
    def test_04_instagram_reel_bana_do_intent(self):
        cmd = "Instagram reel bana do"
        res = classify_video_intent(cmd)
        self.assertEqual(res["intent"], INTENT_VIDEO_EDIT)

    # 5. "Instagram ke liye export karo" -> VIDEO_EXPORT
    def test_05_instagram_export_intent(self):
        cmd = "Instagram ke liye export karo"
        res = classify_video_intent(cmd)
        self.assertEqual(res["intent"], INTENT_VIDEO_EXPORT)

    # 6. "YouTube Short export karo" -> VIDEO_EXPORT
    def test_06_youtube_short_export_intent(self):
        cmd = "YouTube Short export karo"
        res = classify_video_intent(cmd)
        self.assertEqual(res["intent"], INTENT_VIDEO_EXPORT)

    # 7. "video analyze karo" -> VIDEO_ANALYSIS
    def test_07_video_analyze_intent(self):
        cmd = "video analyze karo"
        res = classify_video_intent(cmd)
        self.assertEqual(res["intent"], INTENT_VIDEO_ANALYSIS)

    # 8. Normal: "aaj weather kaisa hai" -> GENERAL_CONVERSATION
    def test_08_general_conversation_intent(self):
        cmd = "aaj weather kaisa hai"
        res = classify_video_intent(cmd)
        self.assertEqual(res["intent"], INTENT_GENERAL_CONVERSATION)

    # 9. Memory preference must NOT override VIDEO_EDIT
    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askdirectory")
    @patch("tkinter.filedialog.askopenfilename")
    @patch("ai.ask_ollama.ask_ollama")
    def test_09_memory_preference_does_not_override_video_edit(self, mock_ask_ollama, mock_filedialog, mock_askdir, mock_tk):
        mock_filedialog.return_value = ""
        mock_askdir.return_value = ""
        mem = MemoryManager()
        mem.remember("I prefer VSCode for video editing", category="user", key="preferred_editor", value="VSCode")

        cmd = "meri ek cinematic video edit karke do"
        spoken_messages = []

        router = CommandRouter()
        router.speech_coordinator = MagicMock()
        router.speech_coordinator.speak.side_effect = lambda msg, *args, **kwargs: spoken_messages.append(msg)

        router.route_command(cmd)

        mock_ask_ollama.assert_not_called()
        self.assertTrue(len(spoken_messages) > 0)
        self.assertIn("cinematic edit prepare kar rahi hoon", spoken_messages[0].lower())

    # 10. No source media: VIDEO_EDIT intent detected
    @patch("tkinter.Tk")
    @patch("tkinter.filedialog.askdirectory")
    @patch("tkinter.filedialog.askopenfilename")
    def test_10_no_source_media_does_not_start_premiere(self, mock_filedialog, mock_askdir, mock_tk):
        mock_filedialog.return_value = ""
        mock_askdir.return_value = ""
        cmd = "meri ek cinematic video edit karke do"
        res = self.session_mgr.handle_command(cmd, sync_execution=True)

        self.assertIn("video folder ki zaroorat hai", res.lower())
        self.assertEqual(self.session_mgr.state, "WAITING_FOR_SOURCE_MEDIA")

    # 11. Video export request pauses at WAITING_FOR_EXPORT_APPROVAL
    @patch("video_editing.export.export_manager.validate_export_config")
    def test_13_export_pauses_at_approval_gate(self, mock_validate):
        mock_validate.return_value = (True, {"valid": True})

        cmd = "Instagram ke liye export karo"
        res = self.session_mgr.handle_command(cmd)

        self.assertEqual(self.session_mgr.state, "WAITING_FOR_EXPORT_APPROVAL")
        self.assertIn("Export ready hai", res)
        self.assertIn("Export start karu?", res)


if __name__ == "__main__":
    unittest.main()
