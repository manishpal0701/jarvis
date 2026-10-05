"""
tests/test_ollama_trouble_fix.py
Unit tests verifying the fix for the Ollama trouble bug:
1. Context overflow protection (num_ctx 2048).
2. Delivered sentence chunk preservation (_chunk_count > 0).
3. Exception classification and fallback handling.
"""
import unittest
from unittest.mock import patch, MagicMock

from ai.ai_response_manager import AIResponseManager, CONVERSATION_OPTIONS, LLMTimeoutException
from ai.ask_ollama import ask_ollama_streaming, clean_response_for_tts

class TestOllamaTroubleFix(unittest.TestCase):

    def test_01_conversation_options_num_ctx(self):
        """Verify CONVERSATION_OPTIONS num_ctx is set to 2048 to prevent HTTP 400 context overflow."""
        self.assertEqual(CONVERSATION_OPTIONS.get("num_ctx"), 2048)

    def test_02_preserve_delivered_chunks_on_late_timeout(self):
        """Verify ask_ollama_streaming preserves already delivered chunks when LLMTimeoutException occurs late."""
        def mock_generate(messages, sentence_callback, **kwargs):
            sentence_callback("Hello Boss.")
            sentence_callback("Python is an awesome programming language.")
            raise LLMTimeoutException("Late stream timeout test")

        with patch.object(AIResponseManager, "generate_response_streaming", side_effect=mock_generate):
            response = ask_ollama_streaming("what is python", "Boss", "boss", request_id="test_req_preserve_timeout")
            self.assertIn("Hello Boss", response)
            self.assertIn("Python is an awesome programming language", response)
            self.assertNotIn("trouble thinking", response.lower())

    def test_03_preserve_delivered_chunks_on_late_exception(self):
        """Verify ask_ollama_streaming preserves already delivered chunks when a general Exception occurs late."""
        def mock_generate(messages, sentence_callback, **kwargs):
            sentence_callback("First chunk delivered successfully.")
            sentence_callback("Second chunk delivered successfully.")
            raise RuntimeError("Unexpected stream read disconnection")

        with patch.object(AIResponseManager, "generate_response_streaming", side_effect=mock_generate):
            response = ask_ollama_streaming("tell me a story", "Boss", "boss", request_id="test_req_preserve_exception")
            self.assertIn("First chunk delivered successfully", response)
            self.assertIn("Second chunk delivered successfully", response)
            self.assertNotIn("trouble thinking", response.lower())

    def test_04_genuine_error_when_zero_chunks_delivered(self):
        """Verify genuine error message is returned only when zero chunks have been delivered."""
        with patch.object(AIResponseManager, "generate_response_streaming", side_effect=Exception("Ollama service down")):
            response = ask_ollama_streaming("hello", "Boss", "boss", request_id="test_req_zero_chunks_error")
            self.assertIn("trouble thinking", response.lower())

    def test_05_timeout_fallback_when_zero_chunks_delivered(self):
        """Verify friendly fallback is returned when zero chunks arrive before LLMTimeoutException."""
        with patch.object(AIResponseManager, "generate_response_streaming", side_effect=LLMTimeoutException("First token timeout")):
            response = ask_ollama_streaming("hello", "Boss", "boss", request_id="test_req_zero_chunks_timeout")
            self.assertIn("listening", response.lower())
            self.assertNotIn("trouble thinking", response.lower())

if __name__ == "__main__":
    unittest.main()
