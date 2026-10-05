"""
scratch/test_voice_fix_verification.py
Verifies that App Builder responses trigger SpeechCoordinator TTS dispatch.
"""
import sys
import unittest
from unittest.mock import MagicMock
from conversation.command_router import CommandRouter
from conversation.conversation_engine import ConversationEngine
from tools.app_builder.app_manager import AppManager

class TestVoiceFixVerification(unittest.TestCase):
    def setUp(self):
        self.app_mgr = AppManager()
        self.app_mgr.reset()
        self.engine = ConversationEngine()
        self.mock_coordinator = MagicMock()
        self.engine.speech_coordinator = self.mock_coordinator
        self.spoken_texts = []

    def tearDown(self):
        self.app_mgr.reset()

    def test_app_builder_response_dispatches_tts(self):
        def _callback(text):
            self.spoken_texts.append(text)

        router = CommandRouter(speak_callback=_callback)
        router.process_user_input("ek app bana do", source="chat")

        # 1. UI callback received text
        self.assertTrue(len(self.spoken_texts) > 0)
        expected_msg = "Okay Boss. App ka naam, features, requirements aur design references chat me likh do. Main uske according app banaunga."
        self.assertEqual(self.spoken_texts[0], expected_msg)

        # 2. SpeechCoordinator.speak was invoked with expected msg and wait=False
        self.mock_coordinator.speak.assert_called_once_with(expected_msg, wait=False)
        print("TEST SUCCESS: Both chat callback and SpeechCoordinator TTS dispatch executed successfully!")

if __name__ == "__main__":
    unittest.main()
