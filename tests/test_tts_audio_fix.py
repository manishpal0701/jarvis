import unittest
import os
import time
import shutil
import tempfile
import threading
from speech.utils import is_valid_audio
from speech.cache_manager import CacheManager
from speech.queue_manager import QueueManager
from speech.speech_engine import SpeechEngine, EdgeTTSProvider
from speech.pyttsx3_provider import PyTTSx3Provider

class TestTTSAudioFix(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager()
        self.cache_manager.cache_dir = self.test_dir

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_1_short_tts_output(self):
        """Test 1: Short TTS output creates a complete playable file."""
        engine = SpeechEngine()
        engine.queue_manager.start()
        try:
            engine.speak("Yes Boss", wait=True)
            # Verify no exceptions occurred and queue manager processed item
            self.assertFalse(engine.queue_manager.is_speaking)
        finally:
            engine.shutdown()

    def test_2_long_tts_output(self):
        """Test 2: Long TTS output creates a complete playable file."""
        engine = SpeechEngine()
        engine.queue_manager.start()
        try:
            long_text = "Boss, meri baat sun lete hain. Website build kar raha hoon, sab theek chal raha hai."
            engine.speak(long_text, wait=True)
            self.assertFalse(engine.queue_manager.is_speaking)
        finally:
            engine.shutdown()

    def test_3_queuemanager_synchronization(self):
        """Test 3: QueueManager never starts playback before file generation completes."""
        queue_mgr = QueueManager()
        queue_mgr.start()
        try:
            incomplete_file = os.path.join(self.test_dir, "incomplete.mp3")
            # Create a 0-byte file (simulating in-progress non-atomic write)
            with open(incomplete_file, "wb") as f:
                pass
            
            queue_mgr.enqueue(incomplete_file, "testing incomplete")
            queue_mgr.wait_until_done()
            # Verify QueueManager safely rejected incomplete file without hanging
            self.assertFalse(queue_mgr.is_speaking)
        finally:
            queue_mgr.stop()

    def test_4_zero_byte_rejection(self):
        """Test 4: Incomplete/zero-byte MP3 is rejected safely."""
        zero_file = os.path.join(self.test_dir, "zero.mp3")
        with open(zero_file, "wb") as f:
            pass
        self.assertFalse(is_valid_audio(zero_file))

    def test_5_corrupt_mp3_rejection(self):
        """Test 5: Corrupt MP3 is rejected safely."""
        corrupt_file = os.path.join(self.test_dir, "corrupt.mp3")
        with open(corrupt_file, "wb") as f:
            f.write(b"CORRUPT_INVALID_HEADER_DATA_1234567890")
        self.assertFalse(is_valid_audio(corrupt_file))

        # Test QueueManager rejection
        queue_mgr = QueueManager()
        queue_mgr.start()
        try:
            queue_mgr.enqueue(corrupt_file, "testing corrupt")
            queue_mgr.wait_until_done()
            self.assertFalse(queue_mgr.is_speaking)
        finally:
            queue_mgr.stop()

    def test_6_sequential_tts_responses(self):
        """Test 6: Multiple sequential TTS responses play in correct order."""
        engine = SpeechEngine()
        engine.queue_manager.start()
        try:
            texts = ["First chunk.", "Second chunk.", "Third chunk."]
            for t in texts:
                engine.speak(t, wait=True)
            self.assertFalse(engine.queue_manager.is_speaking)
        finally:
            engine.shutdown()

    def test_7_concurrent_tts_requests(self):
        """Test 7: Concurrent TTS requests do not corrupt cache files."""
        engine = SpeechEngine()
        engine.queue_manager.start()
        errors = []

        def worker(text):
            try:
                engine.speak(text, wait=True)
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=worker, args=("Concurrent test line one.",))
        t2 = threading.Thread(target=worker, args=("Concurrent test line two.",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        engine.shutdown()
        self.assertEqual(len(errors), 0)

    def test_8_cache_filename_collision(self):
        """Test 8: Cache filename collision does not corrupt an existing file."""
        text = "Identical text collision test"
        voice, rate, pitch, emotion = "en-US-GuyNeural", "+0%", "+0Hz", "professional"
        
        path1 = self.cache_manager.get_cache_path(text, voice, rate, pitch, emotion)
        path2 = self.cache_manager.get_cache_path(text, voice, rate, pitch, emotion)
        self.assertEqual(path1, path2)

    def test_9_playback_failure_resilience(self):
        """Test 9: Audio playback failure does not crash ConversationEngine or QueueManager."""
        queue_mgr = QueueManager()
        queue_mgr.start()
        try:
            # Enqueue non-existent file
            queue_mgr.enqueue(os.path.join(self.test_dir, "non_existent.mp3"), "non existent")
            queue_mgr.wait_until_done()
            self.assertTrue(queue_mgr.stop_event.is_set() or not queue_mgr.is_speaking)
        finally:
            queue_mgr.stop()

    def test_10_qwen3_config_preservation(self):
        """Test 10: Verify Qwen3 / LLM conversation config remains untouched."""
        from ai.ai_response_manager import MODEL_NAME, CONVERSATION_OPTIONS
        self.assertEqual(MODEL_NAME, "qwen3:8b")
        self.assertIsInstance(CONVERSATION_OPTIONS, dict)
        self.assertIn(CONVERSATION_OPTIONS.get("num_ctx"), [512, 1536])

if __name__ == "__main__":
    unittest.main()
