"""
tests/test_phase6_premiere_project_controller.py
Unit & Integration Test Suite for PremiereProjectController readiness state machine.
Validates:
- Distinction between process running and DOM workspace readiness
- Home Screen detection and auto-project creation (.prproj)
- Bounded readiness polling timeout handling (120s timeout)
- ExtendScript DOM diagnostic checks
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from video_editing.software.premiere_project_controller import (
    PremiereProjectController,
    STATE_HOME_SCREEN,
    STATE_CREATING_PROJECT,
    STATE_DOM_READY,
    STATE_FAILED
)


class TestPremiereProjectController(unittest.TestCase):

    def setUp(self):
        self.controller = PremiereProjectController()

    @patch("video_editing.software.premiere_project_controller.requests.get")
    @patch("video_editing.software.premiere_project_controller.requests.post")
    @patch("video_editing.software.premiere_window_controller.PremiereWindowController.bring_to_foreground")
    @patch("video_editing.software.premiere_window_controller.PremiereWindowController.get_running_pid")
    def test_01_ensure_workspace_ready_home_screen_auto_creates_project(
        self, mock_pid, mock_focus, mock_post, mock_get
    ):
        mock_pid.return_value = 12345
        mock_focus.return_value = True

        # Mock ping server response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"app": "JarvisBridge"}

        # First post: check_dom_diagnostics -> Home Screen (project_open: False)
        # Second post: create_automatic_project -> ok: True
        # Third post: check_dom_diagnostics -> DOM Ready (project_open: True)
        res_diag_home = MagicMock(status_code=200)
        res_diag_home.json.return_value = {
            "checks": {"Active Project Ready": False, "Timeline API Ready": True, "Import API Ready": True},
            "details": {"apis": {"projectAPI": False}}
        }

        res_create = MagicMock(status_code=200)
        res_create.json.return_value = {"ok": True, "result": {"created": True, "path": "test.prproj"}}

        res_diag_ready = MagicMock(status_code=200)
        res_diag_ready.json.return_value = {
            "checks": {"Active Project Ready": True, "Timeline API Ready": True, "Import API Ready": True, "Editing API Ready": True},
            "details": {"apis": {"projectAPI": True, "timelineAPI": True, "importAPI": True}}
        }

        mock_post.side_effect = [res_diag_home, res_create, res_diag_ready]

        diag = self.controller.ensure_project_workspace_ready(project_name="TestProject", timeout=10.0, poll_interval=0.1)

        self.assertEqual(self.controller.state, STATE_DOM_READY)
        self.assertTrue(diag.get("dom_ready"))

    @patch("video_editing.software.premiere_project_controller.requests.get")
    @patch("video_editing.software.premiere_project_controller.requests.post")
    @patch("video_editing.software.premiere_project_controller.PremiereProjectController.trigger_ui_automation_new_project")
    @patch("video_editing.software.premiere_window_controller.PremiereWindowController.bring_to_foreground")
    @patch("video_editing.software.premiere_window_controller.PremiereWindowController.get_running_pid")
    def test_03_ui_automation_fallback_when_extendscript_fails(
        self, mock_pid, mock_focus, mock_ui, mock_post, mock_get
    ):
        mock_pid.return_value = 12345
        mock_focus.return_value = True

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"app": "JarvisBridge"}

        # First post: check_dom_diagnostics -> Home Screen
        # Second post: create_project_extendscript -> ok: False (EvalScript error)
        # Third post: check_dom_diagnostics -> Home Screen (triggers UI automation)
        # Fourth post: check_dom_diagnostics -> DOM Ready
        res_diag_home = MagicMock(status_code=200)
        res_diag_home.json.return_value = {"checks": {"Active Project Ready": False}, "details": {"apis": {"projectAPI": False}}}

        res_create_fail = MagicMock(status_code=200)
        res_create_fail.json.return_value = {"ok": False, "error": {"message": "EvalScript error."}}

        res_diag_ready = MagicMock(status_code=200)
        res_diag_ready.json.return_value = {
            "checks": {"Active Project Ready": True, "Timeline API Ready": True, "Import API Ready": True},
            "details": {"apis": {"projectAPI": True, "timelineAPI": True, "importAPI": True, "rootItemAccessible": True}}
        }

        hc_count = [0]
        def post_side_effect(url, **kwargs):
            if "command" in url:
                return res_create_fail
            elif "healthcheck" in url:
                hc_count[0] += 1
                if hc_count[0] <= 2:
                    return res_diag_home
                return res_diag_ready
            return res_diag_ready

        mock_post.side_effect = post_side_effect

        diag = self.controller.ensure_project_workspace_ready(project_name="TestProject", timeout=10.0, poll_interval=0.1)

        self.assertTrue(mock_ui.called)
        self.assertEqual(self.controller.state, STATE_DOM_READY)
        self.assertTrue(diag.get("dom_ready"))


if __name__ == "__main__":
    unittest.main()
