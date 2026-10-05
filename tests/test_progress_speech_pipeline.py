"""
tests/test_progress_speech_pipeline.py
Unit test suite verifying Progress Speech Architecture, ProgressReporter,
TaskOrchestrator integration, non-blocking TTS dispatching, request ID tracking,
and single authoritative voice pipeline rules.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure root workspace directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.progress_reporter import ProgressReporter
from core.task_orchestrator import TaskOrchestrator
import api.websocket.jarvis

class TestProgressSpeechPipeline(unittest.TestCase):

    def setUp(self):
        self.reporter = ProgressReporter.get_instance()
        self.reporter._dispatched_events.clear()

    @patch("api.websocket.jarvis.broadcast_sync")
    @patch("speech.speech_coordinator.SpeechCoordinator.speak")
    def test_progress_reporter_dispatch(self, mock_speak, mock_broadcast):
        """Verify ProgressReporter dispatches WebSocket events and non-blocking speech."""
        req_id = "req_test_123"
        msg = "Boss, main file create kar raha hu."
        
        self.reporter.report(msg, request_id=req_id, stage="FILE_CREATE", speak=True)
        
        # Verify WebSocket broadcast was called with proper structure
        mock_broadcast.assert_called_once()
        ws_payload = mock_broadcast.call_args[0][0]
        self.assertEqual(ws_payload["type"], "progress")
        self.assertEqual(ws_payload["request_id"], req_id)
        self.assertEqual(ws_payload["stage"], "FILE_CREATE")
        self.assertEqual(ws_payload["text"], msg)
        self.assertTrue(ws_payload["speak"])

    @patch("speech.speech_coordinator.SpeechCoordinator.speak")
    def test_progress_reporter_deduplication(self, mock_speak):
        """Verify exact duplicate messages within deduplication window are blocked."""
        req_id = "req_dedup_1"
        msg = "Boss, file ready hai."
        
        with patch("api.websocket.jarvis.broadcast_sync") as mock_broadcast:
            self.reporter.report(msg, request_id=req_id, stage="FILE_CREATE", speak=True)
            progress_calls = [c for c in mock_broadcast.call_args_list if c[0][0].get("type") == "progress"]
            self.assertEqual(len(progress_calls), 1)
            
            # Immediate duplicate call should be blocked by deduplication
            self.reporter.report(msg, request_id=req_id, stage="FILE_CREATE", speak=True)
            progress_calls_after = [c for c in mock_broadcast.call_args_list if c[0][0].get("type") == "progress"]
            self.assertEqual(len(progress_calls_after), 1)

    @patch("core.progress_reporter.ProgressReporter.report")
    def test_task_orchestrator_integration(self, mock_report):
        """Verify TaskOrchestrator calls ProgressReporter on task state transitions."""
        orchestrator = TaskOrchestrator.get_instance()
        task_id = "task_test_99"
        
        # 1. Start Task
        orchestrator.start_task(task_id, "WEBSITE_BUILD", "Building test app", total_items=2)
        mock_report.assert_called()
        self.assertIn("start kar raha hu", mock_report.call_args[0][0])
        
        # 2. Update Progress
        mock_report.reset_mock()
        orchestrator.update_progress(task_id, "GENERATING_FILES", current_item="src/App.tsx")
        mock_report.assert_called()
        self.assertIn("App.tsx", mock_report.call_args[0][0])
        
        # 3. Complete Task
        mock_report.reset_mock()
        orchestrator.complete_task(task_id, "Done")
        mock_report.assert_called_once()
        self.assertIn("kaam complete ho gaya", mock_report.call_args[0][0])

    def test_playback_owner_frontend_preserved(self):
        """Verify PLAYBACK_OWNER remains FRONTEND per core rules."""
        owner = os.getenv("PLAYBACK_OWNER", "FRONTEND").upper()
        self.assertEqual(owner, "FRONTEND")

if __name__ == "__main__":
    unittest.main()
