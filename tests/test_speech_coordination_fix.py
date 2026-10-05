import unittest
import os
import sys
import io
from unittest.mock import patch, MagicMock

from core.state_machine import StateMachine, State
from core.timeout_manager import TimeoutManager
from core.session_manager import SessionManager
from speech.speech_coordinator import SpeechCoordinator
from speech.queue_manager import QueueManager
from speech.wake_manager import WakeManager
import speech

class TestSpeechCoordinationFix(unittest.TestCase):

    def test_speak_signature_contract(self):
        """Verify speech.speak facade accepts speech_id, request_id, and kwargs without TypeError."""
        try:
            # Call speech.speak facade directly with kwargs that previously threw TypeError
            with patch.object(speech._engine, "speak", return_value="cache/mock.mp3") as mock_engine_speak:
                result = speech.speak(
                    "JARVIS online. All systems operational.",
                    wait=True,
                    speech_id="speech_test123",
                    request_id="req_test123"
                )
                self.assertEqual(result, "cache/mock.mp3")
                mock_engine_speak.assert_called_once_with(
                    "JARVIS online. All systems operational.",
                    wait=True,
                    callback=None,
                    single_response=True,
                    speech_id="speech_test123",
                    request_id="req_test123"
                )
        except TypeError as e:
            self.fail(f"speech.speak() raised TypeError: {e}")

    def test_startup_speech_flow(self):
        """Verify startup speech 'JARVIS online. All systems operational.' executes without TypeError."""
        sm = StateMachine()
        tm = TimeoutManager(10.0)
        coordinator = SpeechCoordinator(sm, tm)
        
        with patch.object(speech._engine, "speak", return_value="cache/startup.mp3"):
            try:
                coordinator.speak("JARVIS online. All systems operational.", wait=True)
            except TypeError as e:
                self.fail(f"Startup speech failed with TypeError: {e}")

    def test_wake_word_yes_boss(self):
        """Verify wake word response 'Yes Boss' speaks cleanly."""
        sm = StateMachine()
        tm = TimeoutManager(10.0)
        session_mgr = SessionManager(sm)
        listener_mgr = MagicMock()
        listener_mgr.listen_and_recognize.return_value = "Jarvis"
        
        coordinator = MagicMock()
        wake_mgr = WakeManager(sm, tm, session_mgr, listener_mgr, coordinator)
        
        res = wake_mgr.check_wake_word()
        self.assertTrue(res)
        coordinator.speak.assert_called_once_with("Yes Boss")

    def test_queue_manager_unmuted_default(self):
        """Verify QueueManager defaults to unmuted speaker output."""
        qm = QueueManager()
        self.assertFalse(qm.mute_speaker_output)

if __name__ == "__main__":
    unittest.main()
