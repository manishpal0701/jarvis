import unittest
from unittest.mock import MagicMock, patch
from ai.ask_ollama import ask_ollama_streaming
from conversation.command_router import CommandRouter
from speech.speech_coordinator import SpeechCoordinator
from core.state_machine import StateMachine
from core.timeout_manager import TimeoutManager

class TestStreamAndTTSAggregation(unittest.TestCase):
    def setUp(self):
        self.state_machine = StateMachine()
        self.timeout_manager = TimeoutManager(10.0)
        self.speech_coordinator = SpeechCoordinator(self.state_machine, self.timeout_manager)

    @patch("ai.ask_ollama.AIResponseManager")
    @patch("speech.speech_coordinator.speech.speak")
    def test_streaming_produces_single_tts_dispatch(self, mock_speech_speak, mock_ai_manager_cls):
        mock_ai_mgr = MagicMock()
        mock_ai_manager_cls.return_value = mock_ai_mgr

        # Simulate Ollama streaming 3 sentence chunks
        def fake_generate_streaming(messages, sentence_callback, **kwargs):
            sentence_callback("Boss, aaj 8 September 2026 hai,")
            sentence_callback(" Tuesday hai.")
            sentence_callback(" Kuch aur chahiye?")
            return "Boss, aaj 8 September 2026 hai, Tuesday hai. Kuch aur chahiye?"

        mock_ai_mgr.generate_response_streaming.side_effect = fake_generate_streaming
        mock_speech_speak.return_value = "C:/tmp/audio.mp3"

        chunks_received = []
        def speak_cb(chunk):
            chunks_received.append(chunk)

        request_id = "req_test_aggregation_123"
        resp = ask_ollama_streaming(
            "thik he wese aaj date kya he",
            speaker_name="Boss",
            relation="boss",
            speak_callback=speak_cb,
            speech_coordinator=self.speech_coordinator,
            request_id=request_id
        )

        self.assertEqual(resp, "Boss, aaj 8 September 2026 hai, Tuesday hai. Kuch aur chahiye?")
        self.assertEqual(len(chunks_received), 3)

        # Verify TTS speak WAS called for each of the 3 sentence chunks concurrently with speak_callback
        self.assertEqual(mock_speech_speak.call_count, 3)

    @patch("speech.speech_coordinator.speech.speak")
    def test_datetime_query_single_tts_dispatch(self, mock_speech_speak):
        mock_speech_speak.return_value = "C:/tmp/audio.mp3"
        router = CommandRouter(speech_coordinator=self.speech_coordinator)
        
        request_id = "req_dt_test_456"
        router.process_user_input("thik he wese aaj date kya he", source="chat", request_id=request_id)

        # Verify TTS speak was called EXACTLY ONCE
        self.assertEqual(mock_speech_speak.call_count, 1)
        args, kwargs = mock_speech_speak.call_args
        self.assertEqual(kwargs.get("request_id"), request_id)

        # Verify dispatch count for request_id is 1
        dispatch_count = self.speech_coordinator._request_dispatch_counts.get(request_id, 0)
        self.assertEqual(dispatch_count, 1)

if __name__ == "__main__":
    unittest.main()
