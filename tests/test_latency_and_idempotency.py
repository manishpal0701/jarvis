import unittest
import os
import sys
import io
import time
from unittest.mock import patch, MagicMock

from core.performance_profiler import PerformanceProfiler
from memory.memory_store import MemoryStore
from ai.ai_response_manager import AIResponseManager, LLMTimeoutException, CONVERSATION_OPTIONS
from ai.ask_ollama import ask_ollama_streaming
from speech.speech_coordinator import SpeechCoordinator
from speech.queue_manager import QueueManager
from core.state_machine import StateMachine
from core.timeout_manager import TimeoutManager

class TestLatencyAndIdempotency(unittest.TestCase):

    def test_1_memory_store_single_load_ready(self):
        """Test 1: Verify MemoryStore initializes once per process and logs READY."""
        store1 = MemoryStore()
        store2 = MemoryStore()
        self.assertIs(store1, store2)

    def test_2_ollama_timeout_fallback(self):
        """Test 2: Verify Ollama timeout triggers [CONVERSATION_LLM_TIMEOUT] and fallback message."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            with patch.object(AIResponseManager, "generate_response_streaming", side_effect=LLMTimeoutException("Timed out")):
                resp = ask_ollama_streaming("Tell me a story", "Boss", "boss", request_id="req_timeout_test")
                self.assertIn("Boss, response generation thoda slow ho raha hai", resp)
        finally:
            sys.stdout = sys.__stdout__

        logs = captured_output.getvalue()
        self.assertIn("[CONVERSATION_LLM_TIMEOUT]", logs)
        self.assertIn("request_id=req_timeout_test", logs)

    def test_3_duplicate_request_idempotency(self):
        """Test 3: Verify duplicate request_id is blocked with [CONVERSATION_DUPLICATE_REQUEST]."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            # Simulate simultaneous execution of same request_id
            from ai.ask_ollama import _active_request_ids, _active_req_lock
            req_id = "req_dup_test_123"
            with _active_req_lock:
                _active_request_ids.add(req_id)

            resp = ask_ollama_streaming("Duplicate query test", "Boss", "boss", request_id=req_id)
            self.assertEqual(resp, "")

            with _active_req_lock:
                _active_request_ids.discard(req_id)
        finally:
            sys.stdout = sys.__stdout__

        logs = captured_output.getvalue()
        self.assertIn("[CONVERSATION_DUPLICATE_REQUEST]", logs)
        self.assertIn("action=IGNORED", logs)

    def test_4_tts_response_idempotency(self):
        """Test 4: Verify duplicate speech_id in SpeechCoordinator logs [TTS_DUPLICATE_BLOCKED]."""
        sm = StateMachine()
        tm = TimeoutManager(10.0)
        coordinator = SpeechCoordinator(sm, tm)

        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            with patch("speech.speak", return_value="cache/mock.mp3"):
                # Manually add speech_id to dispatched set to test guard
                coordinator._dispatched_responses.add("speech_dup_456")
                coordinator.speak_chunk("Duplicate TTS text", request_id="req_dup_tts")
        finally:
            sys.stdout = sys.__stdout__

        logs = captured_output.getvalue()
        self.assertIn("[TTS_DUPLICATE_BLOCKED]", logs)

    def test_5_audio_queue_idempotency(self):
        """Test 5: Verify QueueManager blocks duplicate audio with [AUDIO_DUPLICATE_BLOCKED]."""
        qm = QueueManager()
        qm.has_pygame = False

        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            qm.enqueue("cache/audio_dup.mp3", "Duplicate Audio", speech_id="speech_audio_dup")
            qm.enqueue("cache/audio_dup.mp3", "Duplicate Audio", speech_id="speech_audio_dup")
        finally:
            sys.stdout = sys.__stdout__

        logs = captured_output.getvalue()
        self.assertIn("[AUDIO_DUPLICATE_BLOCKED]", logs)
        self.assertIn("reason=already_queued_or_playing", logs)

    def test_6_conversation_options_token_limit(self):
        """Test 6: Verify CONVERSATION_OPTIONS num_predict is limited to 180 tokens."""
        self.assertEqual(CONVERSATION_OPTIONS.get("num_predict"), 180)

if __name__ == "__main__":
    unittest.main()
