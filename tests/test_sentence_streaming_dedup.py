"""
tests/test_sentence_streaming_dedup.py
Unit tests verifying sentence-level streaming TTS deduplication, multi-chunk delivery,
no full-response replay, and barge-in cancellation.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

from core.state_machine import StateMachine, State
from core.timeout_manager import TimeoutManager
from speech.speech_coordinator import SpeechCoordinator
from speech.voice_state_machine import VoiceState

class TestSentenceStreamingDedup(unittest.TestCase):
    def setUp(self):
        self.state_machine = StateMachine()
        self.timeout_manager = TimeoutManager()
        self.coordinator = SpeechCoordinator(self.state_machine, self.timeout_manager)

    @patch("speech.speak")
    @patch("speech.voice_session_manager.VoiceSessionManager.get_instance")
    def test_multi_sentence_streaming_allowed(self, mock_vsm_inst, mock_speech_speak):
        mock_vsm = MagicMock()
        mock_vsm.is_request_invalidated.return_value = False
        mock_vsm_inst.return_value = mock_vsm
        mock_speech_speak.return_value = "C:/tmp/audio.mp3"

        req_id = "req_test_streaming_123"

        # Dispatch chunk 1
        self.coordinator.speak_chunk("Samajh gayi Boss.", wait=True, request_id=req_id, chunk_id="chunk_1")
        # Dispatch chunk 2
        self.coordinator.speak_chunk("Main aapke saath hoon.", wait=True, request_id=req_id, chunk_id="chunk_2")
        # Dispatch chunk 3
        self.coordinator.speak_chunk("Batao kya hua?", wait=True, request_id=req_id, chunk_id="chunk_3")

        # Verify all 3 chunks were dispatched to speech engine
        self.assertEqual(mock_speech_speak.call_count, 3)
        self.assertEqual(self.coordinator._request_dispatch_counts.get(req_id), 3)

    @patch("speech.speak")
    @patch("speech.voice_session_manager.VoiceSessionManager.get_instance")
    def test_duplicate_chunk_id_blocked(self, mock_vsm_inst, mock_speech_speak):
        mock_vsm = MagicMock()
        mock_vsm.is_request_invalidated.return_value = False
        mock_vsm_inst.return_value = mock_vsm
        mock_speech_speak.return_value = "C:/tmp/audio.mp3"

        req_id = "req_test_dedup_456"

        # First transmission of chunk_1
        self.coordinator.speak_chunk("Samajh gayi Boss.", wait=True, request_id=req_id, chunk_id="chunk_1")
        self.assertEqual(mock_speech_speak.call_count, 1)

        # Duplicate re-transmission of chunk_1
        self.coordinator.speak_chunk("Samajh gayi Boss.", wait=True, request_id=req_id, chunk_id="chunk_1")
        # Should remain 1 dispatch, second call rejected as duplicate
        self.assertEqual(mock_speech_speak.call_count, 1)

    @patch("speech.speak")
    @patch("speech.voice_session_manager.VoiceSessionManager.get_instance")
    def test_single_shot_speak_blocks_second_call(self, mock_vsm_inst, mock_speech_speak):
        mock_vsm = MagicMock()
        mock_vsm.is_request_invalidated.return_value = False
        mock_vsm_inst.return_value = mock_vsm
        mock_speech_speak.return_value = "C:/tmp/audio.mp3"

        req_id = "req_test_singleshot_789"

        self.coordinator.speak("First single shot response", wait=True, request_id=req_id)
        self.assertEqual(mock_speech_speak.call_count, 1)

        # Second single-shot call with SAME request_id must be blocked
        self.coordinator.speak("Second single shot response", wait=True, request_id=req_id)
        self.assertEqual(mock_speech_speak.call_count, 1)

    @patch("speech.voice_session_manager.VoiceSessionManager.get_instance")
    def test_barge_in_interruption_invalidates_request(self, mock_vsm_inst):
        mock_vsm = MagicMock()
        mock_session = MagicMock()
        mock_session.request_id = "req_bargein_999"
        mock_session.current_audio_id = "speech_1"
        mock_session.session_id = "sess_1"
        mock_vsm.get_active_session.return_value = mock_session
        mock_vsm.get_active_context.return_value = mock_session
        mock_vsm_inst.return_value = mock_vsm

        self.coordinator.interrupt_speech(reason="user_barge_in", request_id="req_bargein_999")

        mock_vsm.invalidate_request.assert_called_with("req_bargein_999", reason="user_barge_in")
        self.assertEqual(self.state_machine.state, State.WAITING_FOR_NEXT_COMMAND)

if __name__ == "__main__":
    unittest.main()
