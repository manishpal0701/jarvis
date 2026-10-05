import unittest
import io
import sys
from unittest.mock import patch, MagicMock
from conversation.command_router import CommandRouter
from speech.speech_coordinator import SpeechCoordinator
from core.state_machine import StateMachine
from core.timeout_manager import TimeoutManager
from speech.queue_manager import QueueManager

class TestDuplicateSpeakingFix(unittest.TestCase):

    def test_queue_manager_deduplication(self):
        qm = QueueManager()
        qm.has_pygame = False  # prevent actual sound playback during unit test
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            qm.enqueue("cache/test_audio.mp3", "Hello Boss, how can I help you?", speech_id="speech_123")
            qm.enqueue("cache/test_audio.mp3", "Hello Boss, how can I help you?", speech_id="speech_123")
        finally:
            sys.stdout = sys.__stdout__
            
        logs = captured_output.getvalue()
        self.assertIn("action=ENQUEUE", logs)
        self.assertIn("action=SKIP_DUPLICATE", logs)
        self.assertEqual(qm.queue.qsize(), 1)

    def test_normal_conversation_single_tts_dispatch(self):
        sm = StateMachine()
        tm = TimeoutManager(10.0)
        coordinator = SpeechCoordinator(sm, tm)
        router = CommandRouter(speech_coordinator=coordinator)
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        def mock_streaming_generate(messages, sentence_callback=None, **kwargs):
            if sentence_callback:
                sentence_callback("Hello Boss, how can I help you?")
            return "Hello Boss, how can I help you?"

        with patch("speech.speak", return_value="cache/mock_audio.mp3") as mock_speech_speak, \
             patch("ai.ask_ollama.AIResponseManager.generate_response_streaming", side_effect=mock_streaming_generate):
            try:
                router.route_command("Hello Jarvis")
            finally:
                sys.stdout = sys.__stdout__
                
        output = captured_output.getvalue()
        
        # Verify required log markers
        self.assertIn("[CONVERSATION_REQUEST]", output)
        self.assertIn("[CONVERSATION_RESPONSE]", output)
        self.assertIn("[CONVERSATION_DISPATCH]", output)
        self.assertIn("[TTS_DISPATCH]", output)
        self.assertIn("[TTS_QUEUE]", output)
        
        # Ensure speech.speak was called EXACTLY ONCE for the response
        self.assertEqual(mock_speech_speak.call_count, 1)

if __name__ == "__main__":
    unittest.main()
