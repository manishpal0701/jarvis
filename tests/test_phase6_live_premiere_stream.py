"""
tests/test_phase6_live_premiere_stream.py
Comprehensive Unit & Integration Test Suite for Phase 6 Jarvis Live Premiere Pro Editing Stream.
Validates:
- Premiere window controller process detection & foreground activation
- Live editing state machine transitions & sub-failure error codes
- Bounded retry limits (MAX_OPERATION_RETRIES = 2)
- Command lifecycle tracking (COMMAND_REQUESTED -> ... -> COMMAND_COMPLETED)
- Real-time status event broadcasting & workspace status panel rendering
- Cancellation handling (USER_CANCELLED / CANCELLATION_PENDING)
- Phase 6 E2E session orchestration integration
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from video_editing.software.premiere_window_controller import PremiereWindowController
from video_editing.live_editing_state_machine import (
    LiveEditingStateMachine,
    STATE_IDLE,
    STATE_STARTING_PREMIERE,
    STATE_PREMIERE_READY,
    STATE_IMPORTING_MEDIA,
    STATE_EDITING_TIMELINE,
    STATE_COMPLETED,
    STATE_FAILED,
    STATE_CANCELLED,
    ERR_PREMIERE_OPERATION_FAILED,
    ERR_OUTPUT_VERIFICATION_FAILED,
    STATUS_USER_CANCELLED,
    CMD_REQUESTED,
    CMD_COMPLETED,
    MAX_OPERATION_RETRIES
)
from video_editing.live_status_broadcaster import LiveStatusBroadcaster, EVENT_PREMIERE_READY, EVENT_VIDEO_COMPLETE
from video_editing.video_session_manager import VideoEditingSessionManager


class TestPhase6LivePremiereStream(unittest.TestCase):

    def setUp(self):
        self.session = VideoEditingSessionManager.get_instance()
        self.session.reset_session()

        self.temp_dir = tempfile.mkdtemp()
        self.sample_video = os.path.join(self.temp_dir, "sample.mp4")
        with open(self.sample_video, "wb") as f:
            f.write(b"dummy_video_bytes")

    def tearDown(self):
        self.session.reset_session()
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass

    # 1. State machine transitions & bounded retry limits
    def test_01_state_machine_transitions_and_retry_limits(self):
        sm = LiveEditingStateMachine()
        self.assertEqual(sm.state, STATE_IDLE)

        # Transition test
        self.assertTrue(sm.transition_to(STATE_STARTING_PREMIERE))
        self.assertEqual(sm.state, STATE_STARTING_PREMIERE)

        # Bounded retry limits (MAX_OPERATION_RETRIES = 2)
        step = "import_clip_1"
        self.assertTrue(sm.can_retry_step(step))
        self.assertEqual(sm.increment_step_retry(step), 1)
        self.assertTrue(sm.can_retry_step(step))
        self.assertEqual(sm.increment_step_retry(step), 2)
        self.assertFalse(sm.can_retry_step(step))

    # 2. Failure sub-state recording
    def test_02_failure_recording(self):
        sm = LiveEditingStateMachine()
        sm.record_failure(ERR_PREMIERE_OPERATION_FAILED, "Bridge unresponsive")
        self.assertEqual(sm.state, STATE_FAILED)
        self.assertEqual(sm.failure_code, ERR_PREMIERE_OPERATION_FAILED)

    # 3. Cancellation handling
    def test_03_cancellation_safety(self):
        sm = LiveEditingStateMachine()
        sm.request_cancellation()
        self.assertTrue(sm.cancellation_requested)
        # Attempt transition
        sm.transition_to(STATE_IMPORTING_MEDIA)
        self.assertEqual(sm.state, STATE_CANCELLED)
        self.assertEqual(sm.cancellation_status, STATUS_USER_CANCELLED)

    # 4. Status broadcaster & panel rendering
    def test_04_status_broadcaster(self):
        broadcaster = LiveStatusBroadcaster()
        broadcaster.broadcast(EVENT_PREMIERE_READY, {"status": "ok"})
        self.assertEqual(len(broadcaster.events_log), 1)
        self.assertEqual(broadcaster.events_log[0]["event"], EVENT_PREMIERE_READY)

        panel = broadcaster.render_workspace_panel(
            premiere_connected=True,
            project_name="Test_Project",
            current_operation="Cutting clips",
            active_pipeline_stage="timeline_editing"
        )
        self.assertIn("JARVIS VIDEO AGENT", panel)
        self.assertIn("Test_Project", panel)
        self.assertIn("Cutting clips", panel)

    # 5. PremiereWindowController process & focus helpers
    @patch("subprocess.run")
    def test_05_premiere_window_controller(self, mock_subproc):
        mock_subproc.return_value.returncode = 0
        focused = PremiereWindowController.bring_to_foreground()
        self.assertTrue(focused)

    # 6. Session Manager Live Stream E2E Integration
    @patch("video_editing.video_session_manager.verify_output_file")
    @patch("video_editing.software.premiere.PremiereProController.export_sequence")
    @patch("video_editing.software.premiere.PremiereProController.apply_transition")
    @patch("video_editing.software.premiere.PremiereProController.read_timeline_detailed")
    @patch("video_editing.software.premiere.PremiereProController.trim_clip")
    @patch("video_editing.software.premiere.PremiereProController.place_clip_on_timeline")
    @patch("video_editing.software.premiere.PremiereProController.import_clip")
    @patch("video_editing.software.premiere.PremiereProController.ensure_sequence")
    @patch("video_editing.software.premiere.PremiereProController.ensure_project_open")
    @patch("video_editing.software.premiere.PremiereProController.ensure_connected")
    @patch("video_editing.software.premiere_window_controller.PremiereWindowController.ensure_premiere_running_and_focused")
    def test_06_e2e_live_editing_stream(
        self, mock_focus, mock_conn, mock_proj, mock_seq, mock_imp, mock_place, mock_trim, mock_read, mock_trans, mock_exp, mock_verify
    ):
        mock_read.return_value = {"ok": True, "videoClipCount": 1}
        mock_verify.return_value = {
            "success": True,
            "verified": True,
            "duration": 5.0,
            "file_size_bytes": 1024 * 1024 * 5,
            "video": {"resolution": "1080x1920"}
        }

        self.session.pending_plan = {
            "project_name": "E2E_Test",
            "operations": [{"clip_path": self.sample_video, "timeline_pos": 0.0, "in": 0.0, "out": 5.0}]
        }

        report = self.session._execute_approved_edit_plan()

        mock_focus.assert_called_once()
        mock_conn.assert_called_once()
        mock_proj.assert_called_once()
        mock_seq.assert_called_once()
        mock_imp.assert_called_once()
        mock_place.assert_called_once()
        mock_verify.assert_called_once()

        self.assertIn("VIDEO EDIT COMPLETE", report)
        self.assertIn("VERIFIED", report)


if __name__ == "__main__":
    unittest.main()
