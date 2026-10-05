import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from speech.voice_config import VoiceConfig
from speech.voice_session import VoiceSession
from speech.voice_session_manager import VoiceSessionManager

class TestVoiceConfigAndSession(unittest.TestCase):

    def setUp(self):
        self.vsm = VoiceSessionManager.get_instance()

    def test_01_voice_config_defaults(self):
        self.assertGreater(VoiceConfig.MIN_INTERRUPTION_SPEECH_DURATION_MS, 0.0)
        self.assertGreater(VoiceConfig.INTERRUPTION_CONFIDENCE_THRESHOLD, 0.0)
        self.assertIn("stop", VoiceConfig.EXPLICIT_STOP_PHRASES)
        self.assertIn("stop this task", VoiceConfig.EXPLICIT_CANCEL_TASK_PHRASES)

    def test_02_voice_session_model_identity(self):
        session = VoiceSession(metadata={"source": "test"})
        self.assertTrue(session.session_id.startswith("vses_"))
        self.assertTrue(session.request_id.startswith("req_"))
        self.assertTrue(session.message_id.startswith("msg_"))
        self.assertEqual(session.state, "IDLE")

    def test_03_single_active_session_invariant(self):
        session1 = self.vsm.start_session("First prompt", request_id="req_s1")
        self.assertTrue(session1.is_active)

        session2 = self.vsm.start_session("Second prompt", request_id="req_s2")
        self.assertTrue(session2.is_active)
        # Previous session should be invalidated and deactivated
        self.assertFalse(session1.is_active)
        self.assertTrue(self.vsm.is_request_invalidated("req_s1"))

if __name__ == "__main__":
    unittest.main()
