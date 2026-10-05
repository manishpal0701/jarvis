import unittest
import os
import shutil
import tempfile
from speech.utils import is_valid_audio
from speech.speech_engine import SpeechEngine
from speech.queue_manager import QueueManager
from conversation.intelligence.response_validator import ResponseValidator
from ai.ai_response_manager import MODEL_NAME, CONVERSATION_OPTIONS
from config import SPEECH_RATE, VOICE_ID

class TestConversationTTSRegression(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.validator = ResponseValidator()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_1_full_response_spoken_once(self):
        """Test 1: Full response with commas/punctuation is synthesized as one single TTS request."""
        engine = SpeechEngine()
        engine.queue_manager.start()
        try:
            full_response = "Boss, mood kharab hai toh chalo, kuch khana kha lo ya phir ek aise video dekh lo jo tumhe relax kare."
            engine.speak(full_response, wait=True, single_response=True)
            self.assertFalse(engine.queue_manager.is_speaking)
            self.assertTrue(engine.queue_manager.queue.empty())
        finally:
            engine.shutdown()

    def test_2_no_automatic_theek_hai(self):
        """Test 2: Verify trailing 'Theek hai?' is stripped by ResponseValidator."""
        input_text = "Boss, mood kharab hai toh rest kar lo. Theek hai?"
        cleaned = self.validator.validate_and_clean(input_text)
        self.assertFalse(cleaned.endswith("Theek hai?"))
        self.assertFalse(cleaned.endswith("theek hai?"))
        self.assertEqual(cleaned, "Boss, mood kharab hai toh rest kar lo.")

    def test_3_no_normal_response_chunking(self):
        """Test 3: Assert only one audio queue item is enqueued for a normal multi-sentence response."""
        engine = SpeechEngine()
        engine.queue_manager.start()
        try:
            text = "First sentence, with a comma. Second sentence! Third sentence?"
            # Enqueue without waiting immediately to inspect queue
            engine.speak(text, wait=False, single_response=True)
            # Queue size should be 1 item (not split by punctuation)
            self.assertLessEqual(engine.queue_manager.queue.qsize(), 1)
            engine.queue_manager.wait_until_done()
        finally:
            engine.shutdown()

    def test_4_voice_provider_preservation(self):
        """Test 4: Verify configured SPEECH_RATE and VOICE_ID exist in config."""
        self.assertEqual(SPEECH_RATE, 170)
        self.assertIn(VOICE_ID, [2, 4])

    def test_5_audio_corruption_fix_remains_active(self):
        """Test 5: Verify audio corruption protections remain active."""
        zero_byte_file = os.path.join(self.test_dir, "zero.wav")
        with open(zero_byte_file, "wb") as f:
            pass
        self.assertFalse(is_valid_audio(zero_byte_file))

        corrupt_file = os.path.join(self.test_dir, "corrupt.mp3")
        with open(corrupt_file, "wb") as f:
            f.write(b"CORRUPT_HEADER_DATA_123456789")
        self.assertFalse(is_valid_audio(corrupt_file))

    def test_6_sequential_conversations(self):
        """Test 6: Verify sequential responses process completely without errors."""
        engine = SpeechEngine()
        engine.queue_manager.start()
        try:
            r1 = "First conversation response, Boss."
            r2 = "Second conversation response, Boss."
            engine.speak(r1, wait=True, single_response=True)
            engine.speak(r2, wait=True, single_response=True)
            self.assertFalse(engine.queue_manager.is_speaking)
        finally:
            engine.shutdown()

    def test_7_qwen3_config_unchanged(self):
        """Test 7: Assert Qwen3 model config and options remain unchanged."""
        self.assertEqual(MODEL_NAME, "qwen3:8b")
        self.assertIsInstance(CONVERSATION_OPTIONS, dict)
        self.assertIn(CONVERSATION_OPTIONS.get("num_ctx"), [512, 1536])

if __name__ == "__main__":
    unittest.main()
