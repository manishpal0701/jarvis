"""
tests/test_app_builder_progress_speech.py
Unit tests verifying that App Builder orchestrators and agents dispatch all progress speech
updates via the authoritative ProgressReporter/TTS pipeline.
"""
import unittest
from unittest.mock import MagicMock, patch
import os
import shutil
import tempfile

from core.progress_reporter import ProgressReporter
from tools.app_builder.app_model import AppProject, AppBrief, AppState
from tools.app_builder.app_orchestrator import AppDevelopmentOrchestrator
from tools.app_builder.app_runtime_orchestrator import AppRuntimeOrchestrator
from tools.app_builder.app_finalization_orchestrator import AppFinalizationOrchestrator
from tools.app_builder.app_coding_agent import AppCodingAgent
from tools.app_builder.app_manager import AppManager


class TestAppBuilderProgressSpeech(unittest.TestCase):

    def setUp(self):
        self.reporter = ProgressReporter.get_instance()
        self.reporter.reset()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        self.reporter.reset()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch.object(ProgressReporter, "report")
    def test_app_orchestrator_speak_dispatches_progress_reporter(self, mock_report):
        orch = AppDevelopmentOrchestrator(request_id="req_dev_123")
        orch.speak("Boss, Flutter development start kar raha hoon.")

        mock_report.assert_called_once_with(
            message="Boss, Flutter development start kar raha hoon.",
            request_id="req_dev_123",
            stage="EXECUTION",
            speak=True
        )

    @patch.object(ProgressReporter, "report")
    def test_app_runtime_orchestrator_speak_dispatches_progress_reporter(self, mock_report):
        orch = AppRuntimeOrchestrator(request_id="req_runtime_456")
        orch.speak("Boss, Flutter application aur Node.js backend performance test plan execute kar raha hoon.", stage="RUNTIME_TEST_PLAN")

        mock_report.assert_called_once_with(
            message="Boss, Flutter application aur Node.js backend performance test plan execute kar raha hoon.",
            request_id="req_runtime_456",
            stage="RUNTIME_TEST_PLAN",
            speak=True
        )

    @patch.object(ProgressReporter, "report")
    def test_app_finalization_orchestrator_speak_dispatches_progress_reporter(self, mock_report):
        orch = AppFinalizationOrchestrator(request_id="req_final_789")
        orch.speak("Boss, application final release readiness start kar raha hoon.", stage="FINALIZATION_START")

        mock_report.assert_called_once_with(
            message="Boss, application final release readiness start kar raha hoon.",
            request_id="req_final_789",
            stage="FINALIZATION_START",
            speak=True
        )

    @patch.object(ProgressReporter, "report")
    def test_app_coding_agent_speak_dispatches_progress_reporter(self, mock_report):
        agent = AppCodingAgent(request_id="req_coding_000")
        agent.speak("Boss, source files generate kar raha hoon.", stage="CODING_START")

        mock_report.assert_called_once_with(
            message="Boss, source files generate kar raha hoon.",
            request_id="req_coding_000",
            stage="CODING_START",
            speak=True
        )

    @patch("tools.app_builder.command_executor.AppCommandExecutor.execute")
    @patch.object(ProgressReporter, "report")
    def test_app_project_request_id_propagation(self, mock_report, mock_cmd_exec):
        mock_cmd_exec.return_value = {"success": True, "stdout": "Flutter 3.19.0"}

        project = AppProject(
            name="WeatherApp",
            description="Weather tracking app",
            request_id="req_unified_999"
        )
        orch = AppDevelopmentOrchestrator()

        with patch.object(orch.workspace_mgr, "create_workspace", return_value={"frontend": self.test_dir, "backend": self.test_dir}):
            with patch("tools.app_builder.app_development_planner.AppDevelopmentPlanner.generate_plan", return_value={"app_name": "WeatherApp", "screens": []}):
                orch.execute_pipeline(project)

        self.assertTrue(mock_report.called)
        for call_args in mock_report.call_args_list:
            kwargs = call_args.kwargs
            self.assertEqual(kwargs.get("request_id"), "req_unified_999")
            self.assertTrue(kwargs.get("speak"))


if __name__ == "__main__":
    unittest.main()
