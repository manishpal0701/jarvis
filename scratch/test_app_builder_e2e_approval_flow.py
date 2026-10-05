"""
scratch/test_app_builder_e2e_approval_flow.py
End-to-End Verification Test for App Builder Approval & Implementation Execution Pipeline.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath("."))

from tools.app_builder.app_manager import AppManager
from tools.app_builder.app_model import AppState
from conversation.command_router import CommandRouter


class TestAppBuilderApprovalFlow(unittest.TestCase):

    def setUp(self):
        self.app_mgr = AppManager()
        self.app_mgr.reset()
        self.router = CommandRouter()
        self.spoken = []
        self.router.speech_coordinator = MagicMock()
        self.router.speech_coordinator.speak.side_effect = lambda msg: self.spoken.append(msg)

    def test_e2e_app_builder_approval_continuation(self):
        # Step 1: Initial creation request
        self.router.route_command("Jarvis, ek app bana do")
        active = self.app_mgr.get_active_app()
        self.assertIsNotNone(active)
        self.assertEqual(active.status, AppState.WAITING_FOR_BRIEF)

        # Step 2: User provides detailed brief with explicit app name
        brief_prompt = (
            "Jarvis, ek complete Spotify-style Music Player Android app banao.\n"
            "App ka naam: JARVIS Music\n"
            "Purpose: Play offline and online music\n"
            "Features: login, home screen, search, playlists, liked songs, recently played, queue, shuffle, repeat\n"
            "Backend: Node.js + Express API"
        )

        with patch("tools.app_builder.app_orchestrator.FlutterProjectGenerator.create_real_flutter_project") as mock_flut_create, \
             patch("tools.app_builder.app_orchestrator.NodeProjectGenerator.generate_backend") as mock_node_gen, \
             patch("tools.app_builder.app_orchestrator.FlutterProjectGenerator.generate_frontend") as mock_flut_gen, \
             patch("tools.app_builder.app_orchestrator.ConcreteFlutterAndroidStudioRunner.open_in_android_studio") as mock_studio, \
             patch("tools.app_builder.app_orchestrator.ConcreteNodeVSCodeRunner.open_in_vscode") as mock_vscode, \
             patch("tools.app_builder.app_runtime_orchestrator.AppRuntimeOrchestrator.execute_runtime_verification") as mock_runtime, \
             patch("tools.app_builder.app_finalization_orchestrator.AppFinalizationOrchestrator.finalize_app") as mock_final:

            mock_flut_create.return_value = {"success": True}
            mock_node_gen.return_value = ["package.json", "src/app.js"]
            mock_flut_gen.return_value = ["lib/main.dart"]
            mock_studio.return_value = {"success": True}
            mock_vscode.return_value = {"success": True}
            mock_runtime.return_value = {"status": "VERIFIED"}
            mock_final.return_value = {"status": "READY"}

            # Send full brief (runs architecture planning synchronously in test mode)
            self.router.route_command(brief_prompt, sync_execution=True)

            active_after_brief = self.app_mgr.get_active_app()
            self.assertIsNotNone(active_after_brief)
            self.assertEqual(active_after_brief.app_id, active.app_id)
            self.assertEqual(active_after_brief.name, "JARVIS Music")
            self.assertEqual(active_after_brief.status, AppState.WAITING_FOR_APPROVAL)

            # Step 3: User says "yes" to approve
            self.router.route_command("yes", sync_execution=True)

            active_after_approval = self.app_mgr.get_app_by_id(active.app_id)
            self.assertTrue(active_after_approval.approved_for_code_generation)
            self.assertEqual(active_after_approval.status, AppState.COMPLETED)

            # Verify mocks were invoked for physical project generation & IDE launch
            mock_node_gen.assert_called_once()
            mock_flut_create.assert_called_once()
            mock_flut_gen.assert_called_once()
            mock_studio.assert_called_once()
            mock_vscode.assert_called_once()
            mock_runtime.assert_called_once()
            mock_final.assert_called_once()


if __name__ == "__main__":
    unittest.main()
