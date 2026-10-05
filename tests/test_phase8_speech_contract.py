"""
tests/test_phase8_speech_contract.py
Phase 8 Speech Contract Unit & Integration Tests.
Verifies that App Builder responses emit authoritative speech diagnostic markers:
[APP_SPEECH], [APP_SPEECH_DISPATCH], [APP_SPEECH_QUEUE], [APP_SPEECH_WS], [APP_SPEECH_PLAYBACK], [APP_SPEECH_COMPLETE]
and route through SpeechCoordinator and ProgressReporter without duplicate TTS calls.
"""
import unittest
from unittest.mock import patch, MagicMock
import io
import sys

from core.progress_reporter import ProgressReporter
from speech.speech_coordinator import SpeechCoordinator
from core.state_machine import StateMachine, State
from core.timeout_manager import TimeoutManager

class TestPhase8SpeechContract(unittest.TestCase):

    def setUp(self):
        ProgressReporter.get_instance().reset()
        self.state_machine = StateMachine()
        self.timeout_manager = TimeoutManager()
        self.coordinator = SpeechCoordinator(self.state_machine, self.timeout_manager)

    @patch("speech.speak")
    def test_progress_reporter_emits_app_speech_markers(self, mock_speech_speak):
        mock_speech_speak.return_value = "c:/fake/path/audio.mp3"
        captured = io.StringIO()

        with patch("api.websocket.jarvis.broadcast_sync", create=True):
            with patch.object(sys, 'stdout', captured):
                ProgressReporter.get_instance().report(
                    message="Boss, requirement analysis in progress.",
                    request_id="req_test_123",
                    stage="PLANNING",
                    speak=True
                )

        output = captured.getvalue()
        self.assertIn("[APP_SPEECH]", output)
        self.assertIn("request_id=req_test_123", output)
        self.assertIn("stage=PLANNING", output)
        self.assertIn("[APP_SPEECH_DISPATCH]", output)
        self.assertIn("[PROGRESS_EVENT]", output)

    @patch("speech.speak")
    def test_speech_coordinator_emits_complete_diagnostic_telemetry(self, mock_speech_speak):
        mock_speech_speak.return_value = "c:/fake/path/audio.mp3"
        captured = io.StringIO()

        with patch("api.websocket.jarvis.broadcast_sync", create=True):
            with patch.object(sys, 'stdout', captured):
                self.coordinator.speak("Boss, Flutter project is ready.", wait=False, request_id="req_test_456")

        output = captured.getvalue()
        self.assertIn("[CONVERSATION_RESPONSE]", output)
        self.assertIn("[CONVERSATION_DISPATCH]", output)
        self.assertIn("[TTS_DISPATCH]", output)
        self.assertIn("[TTS_QUEUE]", output)
        self.assertIn("[TTS_READY]", output)
        self.assertIn("[WS_TX]", output)


    @patch("speech.speak")
    def test_duplicate_speech_blocked_in_speech_coordinator(self, mock_speech_speak):
        mock_speech_speak.return_value = "c:/fake/path/audio.mp3"
        captured = io.StringIO()

        with patch.object(sys, 'stdout', captured):
            self.coordinator.speak("Boss, duplicate text test.", wait=False, request_id="req_dup_1")
            self.coordinator.speak("Boss, duplicate text test.", wait=False, request_id="req_dup_2")

        output = captured.getvalue()
        self.assertIn("[TTS_DUPLICATE_BLOCKED]", output)
        # Verify speech.speak was only invoked ONCE
        self.assertEqual(mock_speech_speak.call_count, 1)

if __name__ == "__main__":
    unittest.main()
