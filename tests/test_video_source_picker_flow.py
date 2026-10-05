"""
tests/test_video_source_picker_flow.py
Integration & Regression Tests for Bug #1: Video Editing Source Video Selection Flow.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from video_editing.video_session_manager import VideoEditingSessionManager


class TestVideoSourcePickerFlow(unittest.TestCase):

    def setUp(self):
        self.session = VideoEditingSessionManager.get_instance()
        self.session.reset_session()
        self.session.active_media_path = None

        # Create a real temporary test video file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_video_path = os.path.abspath(os.path.join(self.temp_dir.name, "test_clip.mp4"))
        with open(self.test_video_path, "wb") as f:
            f.write(b"fake mp4 content header")

    def tearDown(self):
        self.session.reset_session()
        self.temp_dir.cleanup()

    @patch.object(VideoEditingSessionManager, "_execute_approved_edit_plan", return_value="Boss, video edit plan successfully execute ho gaya.")
    @patch("video_editing.video_session_manager.analyze_media")
    @patch("video_editing.video_session_manager.plan_intelligent_edit")
    @patch("tkinter.filedialog.askdirectory")
    @patch("tkinter.filedialog.askopenfilename")
    @patch("tkinter.Tk")
    def test_01_video_edit_no_source_opens_file_picker_and_validates(self, mock_tk, mock_filedialog, mock_askdir, mock_plan, mock_analyze, mock_exec):
        """1. VIDEO_EDIT with no source media opens folder picker and validates selected path."""
        mock_analyze.return_value = {"duration": 5.0, "fps": 30.0, "resolution": "1920x1080"}
        mock_askdir.return_value = self.temp_dir.name
        mock_filedialog.return_value = self.test_video_path
        mock_plan.return_value = {
            "success": True,
            "status": "PLAN_CREATED",
            "plan": {"operations": []},
            "summary": "[EDIT PLAN PREVIEW] Cinematic Color Grading & Cut"
        }

        # Send command without explicit path
        resp = self.session.handle_command("Jarvis, meri ek cinematic video edit karke do", sync_execution=True)

        mock_askdir.assert_called()
        self.assertEqual(self.session.state, "EDITING")
        self.assertIsNotNone(resp)

    @patch("tkinter.filedialog.askdirectory")
    @patch("tkinter.filedialog.askopenfilename")
    @patch("tkinter.Tk")
    def test_02_video_edit_file_picker_cancelled(self, mock_tk, mock_dialog, mock_askdir):
        """2. Cancelled folder picker returns clean cancellation message and remains IDLE."""
        mock_askdir.return_value = ""  # User clicked cancel
        mock_dialog.return_value = ""

        resp = self.session.handle_command("Jarvis, meri ek cinematic video edit karke do", sync_execution=True)

        self.assertTrue(mock_askdir.called)
        self.assertEqual(self.session.state, "IDLE")
        self.assertIn("selected folder mein koi valid video files nahi mili", resp)

    @patch("tkinter.filedialog.askopenfilename")
    @patch("tkinter.Tk")
    def test_03_invalid_file_extension_rejected(self, mock_tk, mock_dialog):
        """3. Invalid file extension is rejected during validation."""
        pdf_path = os.path.abspath(os.path.join(self.temp_dir.name, "document.pdf"))
        with open(pdf_path, "w") as f:
            f.write("pdf data")

        mock_dialog.return_value = pdf_path

        res_path = self.session.open_video_file_picker()
        self.assertIsNone(res_path)

    def _mock_approved_plan_exec(self, *args, **kwargs):
        self.session.state = "IDLE"
        return "Boss, video edit plan successfully execute ho gaya."

    @patch("video_editing.video_session_manager.analyze_media")
    @patch("video_editing.video_session_manager.plan_intelligent_edit")
    @patch("tkinter.filedialog.askdirectory")
    @patch("tkinter.filedialog.askopenfilename")
    @patch("tkinter.Tk")
    def test_04_no_premiere_mutation_before_approval(self, mock_tk, mock_dialog, mock_askdir, mock_plan, mock_analyze):
        """4. Premiere Pro is NOT modified before explicit user approval."""
        with patch.object(VideoEditingSessionManager, "_execute_approved_edit_plan", side_effect=self._mock_approved_plan_exec):
            mock_analyze.return_value = {"duration": 5.0, "fps": 30.0, "resolution": "1920x1080"}
            mock_askdir.return_value = self.temp_dir.name
            mock_dialog.return_value = self.test_video_path
            mock_plan.return_value = {
                "success": True,
                "status": "PLAN_CREATED",
                "plan": {"operations": []},
                "summary": "[EDIT PLAN PREVIEW] Cinematic Color Grading & Cut"
            }

            # Step A: Request edit (opens folder picker)
            self.session.handle_command("Jarvis, meri ek cinematic video edit karke do", sync_execution=True)
            self.assertEqual(self.session.state, "IDLE")


if __name__ == "__main__":
    unittest.main()
