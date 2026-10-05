"""
tests/test_phase6_premiere_readiness_regression.py
Regression tests for Premiere Pro Project Readiness & Phase 5/6 E2E Pipeline.

Coverage:
A. Premiere already has an open project -> DOM_READY.
B. Premiere is on HOME_SCREEN -> project creation -> PROJECT_READY -> DOM_READY.
C. Project creation fails -> bounded recovery -> explicit failure.
D. Ctrl+N fallback does not falsely report success when app.project remains null.
E. After DOM_READY, the existing video edit pipeline actually continues.
F. ffprobe executable discovery works.
G. No infinite HOME_SCREEN polling.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, call

from video_editing.software.premiere_project_controller import (
    PremiereProjectController,
    STATE_PROCESS_NOT_RUNNING,
    STATE_WINDOW_READY,
    STATE_HOME_SCREEN,
    STATE_CREATING_PROJECT,
    STATE_PROJECT_LOADING,
    STATE_PROJECT_WORKSPACE,
    STATE_DOM_READY,
    STATE_FAILED
)
from video_editing.utils.ffprobe_finder import find_ffprobe_executable, run_ffprobe


class TestPremiereReadinessRegression(unittest.TestCase):

    def setUp(self):
        self.controller = PremiereProjectController()

    @patch("video_editing.software.premiere_project_controller.PremiereWindowController.get_running_pid", return_value=1234)
    @patch("video_editing.software.premiere_project_controller.PremiereWindowController.bring_to_foreground", return_value=True)
    @patch("requests.get")
    @patch("requests.post")
    def test_A_premiere_already_has_open_project(self, mock_post, mock_get, mock_bring, mock_pid):
        """Test Scenario A: Premiere already has an open project -> DOM_READY directly."""
        mock_ping = MagicMock()
        mock_ping.status_code = 200
        mock_ping.json.return_value = {"app": "JarvisBridge"}
        mock_get.return_value = mock_ping

        mock_hc = MagicMock()
        mock_hc.status_code = 200
        mock_hc.json.return_value = {
            "checks": {
                "Active Project Ready": True,
                "Timeline API Ready": True,
                "Import API Ready": True,
                "Editing API Ready": True
            },
            "details": {
                "apis": {
                    "projectAPI": True,
                    "rootItemAccessible": True,
                    "projectName": "Existing_Project.prproj"
                }
            }
        }
        mock_post.return_value = mock_hc

        diag = self.controller.ensure_project_workspace_ready(timeout=5.0, poll_interval=0.1)

        self.assertEqual(self.controller.state, STATE_DOM_READY)
        self.assertTrue(diag.get("project_exists"))
        self.assertTrue(diag.get("dom_ready"))
        self.assertEqual(diag.get("project_path"), "Existing_Project.prproj")

    @patch("video_editing.software.premiere_project_controller.PremiereWindowController.get_running_pid", return_value=1234)
    @patch("video_editing.software.premiere_project_controller.PremiereWindowController.bring_to_foreground", return_value=True)
    @patch("requests.get")
    @patch("requests.post")
    def test_B_home_screen_to_project_creation_to_dom_ready(self, mock_post, mock_get, mock_bring, mock_pid):
        """Test Scenario B: Premiere on HOME_SCREEN -> ExtendScript project creation -> PROJECT_READY -> DOM_READY."""
        mock_ping = MagicMock()
        mock_ping.status_code = 200
        mock_ping.json.return_value = {"app": "JarvisBridge"}
        mock_get.return_value = mock_ping

        # Sequence of healthchecks: 1st call -> HOME_SCREEN, 2nd+ call -> Project ready
        mock_hc_home = MagicMock()
        mock_hc_home.status_code = 200
        mock_hc_home.json.return_value = {
            "checks": {"Active Project Ready": False},
            "details": {"apis": {"projectAPI": False}}
        }

        mock_hc_ready = MagicMock()
        mock_hc_ready.status_code = 200
        mock_hc_ready.json.return_value = {
            "checks": {
                "Active Project Ready": True,
                "Timeline API Ready": True,
                "Import API Ready": True,
                "Editing API Ready": True
            },
            "details": {
                "apis": {
                    "projectAPI": True,
                    "rootItemAccessible": True,
                    "projectName": "Jarvis_Live_Project"
                }
            }
        }

        mock_cmd = MagicMock()
        mock_cmd.status_code = 200
        mock_cmd.json.return_value = {"ok": True, "result": {"created": True}}

        hc_count = [0]
        def post_side_effect(url, **kwargs):
            if "command" in url:
                return mock_cmd
            elif "healthcheck" in url:
                hc_count[0] += 1
                if hc_count[0] <= 1:
                    return mock_hc_home
                return mock_hc_ready
            return mock_hc_ready

        mock_post.side_effect = post_side_effect

        diag = self.controller.ensure_project_workspace_ready("Jarvis_Live_Project", timeout=5.0, poll_interval=0.1)

        self.assertEqual(self.controller.state, STATE_DOM_READY)
        self.assertTrue(diag.get("project_exists"))
        self.assertTrue(diag.get("dom_ready"))

    @patch("video_editing.software.premiere_project_controller.PremiereWindowController.get_running_pid", return_value=1234)
    @patch("video_editing.software.premiere_project_controller.PremiereWindowController.bring_to_foreground", return_value=True)
    @patch("video_editing.software.premiere_project_controller.PremiereProjectController.trigger_direct_project_file_open")
    @patch("video_editing.software.premiere_project_controller.PremiereProjectController.trigger_ui_automation_new_project")
    @patch("requests.get")
    @patch("requests.post")
    def test_C_and_G_bounded_recovery_failure_no_infinite_home_screen_polling(
        self, mock_post, mock_get, mock_ui_fallback, mock_file_fallback, mock_bring, mock_pid
    ):
        """Test Scenarios C & G: Project creation fails -> bounded recovery attempts -> explicit failure without infinite polling."""
        mock_ping = MagicMock()
        mock_ping.status_code = 200
        mock_ping.json.return_value = {"app": "JarvisBridge"}
        mock_get.return_value = mock_ping

        # Healthcheck always reports HOME_SCREEN (project_exists=False)
        mock_hc_home = MagicMock()
        mock_hc_home.status_code = 200
        mock_hc_home.json.return_value = {
            "checks": {"Active Project Ready": False},
            "details": {"apis": {"projectAPI": False}}
        }

        mock_cmd_fail = MagicMock()
        mock_cmd_fail.status_code = 200
        mock_cmd_fail.json.return_value = {"ok": False, "error": "ExtendScript createProject returned error: EvalScript error"}

        def post_side_effect(url, **kwargs):
            if "command" in url:
                return mock_cmd_fail
            return mock_hc_home

        mock_post.side_effect = post_side_effect

        with self.assertRaises(RuntimeError) as ctx:
            self.controller.ensure_project_workspace_ready("Fail_Project", timeout=15.0, poll_interval=0.1)

        err_msg = str(ctx.exception)
        self.assertIn("PREMIERE_READINESS_FAILED", err_msg)
        self.assertEqual(self.controller.state, STATE_FAILED)

    @patch("video_editing.software.premiere_project_controller.PremiereWindowController.get_running_pid", return_value=1234)
    @patch("video_editing.software.premiere_project_controller.PremiereWindowController.bring_to_foreground", return_value=True)
    @patch("video_editing.software.premiere_project_controller.PremiereProjectController.trigger_direct_project_file_open")
    @patch("video_editing.software.premiere_project_controller.PremiereProjectController.trigger_ui_automation_new_project")
    @patch("requests.get")
    @patch("requests.post")
    def test_D_ctrl_n_fallback_does_not_falsely_report_success(
        self, mock_post, mock_get, mock_ui_fallback, mock_file_fallback, mock_bring, mock_pid
    ):
        """Test Scenario D: Ctrl+N fallback triggered, but if app.project remains null, state does NOT falsely report DOM_READY."""
        mock_ping = MagicMock()
        mock_ping.status_code = 200
        mock_ping.json.return_value = {"app": "JarvisBridge"}
        mock_get.return_value = mock_ping

        # Healthcheck always returns project_exists=False
        mock_hc = MagicMock()
        mock_hc.status_code = 200
        mock_hc.json.return_value = {"checks": {"Active Project Ready": False}}
        mock_post.return_value = mock_hc

        with self.assertRaises(RuntimeError):
            self.controller.ensure_project_workspace_ready("Fallback_Test", timeout=15.0, poll_interval=0.1)

        self.assertNotEqual(self.controller.state, STATE_DOM_READY)
        self.assertEqual(self.controller.state, STATE_FAILED)

    def test_F_ffprobe_executable_discovery(self):
        """Test Scenario F: ffprobe executable discovery finds a valid executable."""
        exe = find_ffprobe_executable()
        self.assertIsNotNone(exe, "ffprobe_finder should locate a valid ffprobe/ffmpeg executable.")
        self.assertTrue(os.path.isfile(exe), f"Discovered executable does not exist: {exe}")

    @patch("video_editing.video_session_manager.VideoEditingSessionManager._execute_approved_edit_plan")
    def test_E_pipeline_continues_after_dom_ready(self, mock_exec_plan):
        """Test Scenario E: User approval ('haan bana do') triggers pipeline continuation via _execute_approved_edit_plan."""
        from video_editing.video_session_manager import VideoEditingSessionManager
        sm = VideoEditingSessionManager.get_instance()
        sm.reset_session()
        sm.state = "WAITING_FOR_APPROVAL"
        sm.pending_plan = {"project_name": "Jarvis_Test", "operations": []}
        mock_exec_plan.return_value = "VIDEO EDIT COMPLETE"

        res = sm.handle_command("haan bana do")
        self.assertEqual(res, "VIDEO EDIT COMPLETE")
        mock_exec_plan.assert_called_once()
        sm.reset_session()


if __name__ == "__main__":
    unittest.main()
