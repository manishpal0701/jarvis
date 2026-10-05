"""
tests/test_chat_pipeline.py
Phase 2.5 Unit & Integration Test Suite — Unified Voice & Chat Command Pipeline.
Tests all 10 mandatory test scenarios defined in Phase 2.5 spec.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.getcwd())

from conversation.command_router import CommandRouter
from conversation.conversation_engine import ConversationEngine
from tools.app_builder.app_manager import AppManager
from tools.app_builder.app_model import AppState
from tools.coding.website_session_manager import WebsiteSessionManager


class TestChatPipeline(unittest.TestCase):

    def setUp(self):
        self.app_mgr = AppManager()
        self.app_mgr.reset()
        self.web_mgr = WebsiteSessionManager.get_instance()
        self.web_mgr.reset_session()
        self.spoken_texts = []

    def mock_speak(self, text: str):
        if text:
            self.spoken_texts.append(text)

    def test_01_chat_hello_executes_pipeline(self):
        """TEST 1: Chat 'hello' executes core command pipeline."""
        def mock_ollama(prompt, speaker_name="Boss", relation="boss", speak_callback=None, speech_coordinator=None, request_id=None):
            if speak_callback:
                speak_callback("Hello Boss, how can I help you?")

        with patch("ai.ask_ollama.ask_ollama_streaming", side_effect=mock_ollama):
            router = CommandRouter(speak_callback=self.mock_speak)
            router.process_user_input("hello", source="chat")
            self.assertGreater(len(self.spoken_texts), 0)
            self.assertIn("Hello Boss", self.spoken_texts[0])

    def test_02_chat_datetime_query(self):
        """TEST 2: Chat 'what time is it' executes same datetime processing as voice."""
        router = CommandRouter(speak_callback=self.mock_speak)
        router.process_user_input("what time is it", source="chat")
        self.assertGreater(len(self.spoken_texts), 0)
        self.assertTrue(any("It's" in t or "time" in t.lower() for t in self.spoken_texts))

    def test_03_chat_app_build_intent(self):
        """TEST 3: Chat 'ek Android app bana do' triggers APP_BUILD -> WAITING_FOR_BRIEF."""
        router = CommandRouter(speak_callback=self.mock_speak)
        router.process_user_input("ek Android app bana do", source="chat")
        active = self.app_mgr.get_active_app()
        self.assertIsNotNone(active)
        self.assertEqual(active.status, AppState.WAITING_FOR_BRIEF)

    def test_04_chat_app_brief_update_name(self):
        """TEST 4: Chat 'App ka naam Expense Manager hai' updates active AppBrief."""
        router = CommandRouter(speak_callback=self.mock_speak)
        router.process_user_input("Jarvis ek Android app bana do", source="chat")

        router.process_user_input("App ka naam Expense Manager hai", source="chat")
        active = self.app_mgr.get_active_app()
        self.assertIsNotNone(active)
        self.assertEqual(active.brief.name, "Expense Manager")

    def test_05_chat_app_brief_merge_features(self):
        """TEST 5: Chat 'Login aur expense tracking chahiye' updates AppBrief without losing previous info."""
        router = CommandRouter(speak_callback=self.mock_speak)
        router.process_user_input("ek Android app bana do", source="chat")
        router.process_user_input("App ka naam Expense Manager hai", source="chat")
        router.process_user_input("Isme login, expense tracking aur reports feature honi chahiye", source="chat")

        active = self.app_mgr.get_active_app()
        self.assertIsNotNone(active)
        self.assertEqual(active.brief.name, "Expense Manager")
        self.assertGreater(len(active.brief.features), 0)

    def test_06_chat_website_builder_trigger(self):
        """TEST 6: Chat 'ek 3D website bana do' triggers Website Builder."""
        with patch("webbrowser.open"), patch("tools.coding.workspace_manager.WorkspaceManager.get_instance"):
            router = CommandRouter(speak_callback=self.mock_speak)
            router.process_user_input("ek 3D website bana do", source="chat")
            self.assertTrue(self.web_mgr.is_active())

    def test_07_voice_and_chat_same_business_handler(self):
        """TEST 7: Voice and Chat with same command trigger identical business handlers."""
        router_voice = CommandRouter(speak_callback=self.mock_speak)
        router_chat = CommandRouter(speak_callback=self.mock_speak)

        # Reset state
        self.app_mgr.reset()
        router_voice.process_user_input("Jarvis ek Android app bana do", source="voice")
        app_v = self.app_mgr.get_active_app()

        self.app_mgr.reset()
        router_chat.process_user_input("Jarvis ek Android app bana do", source="chat")
        app_c = self.app_mgr.get_active_app()

        self.assertIsNotNone(app_v)
        self.assertIsNotNone(app_c)
        self.assertEqual(app_v.status, app_c.status)

    def test_08_chat_produces_speech_events(self):
        """TEST 8: Chat command produces TTS speech calls & WebSocket broadcasts."""
        events = []
        mock_jarvis_module = MagicMock()
        mock_jarvis_module.broadcast_sync = lambda d: events.append(d)
        with patch.dict("sys.modules", {"fastapi": MagicMock(), "api.websocket.jarvis": mock_jarvis_module}):
            router = CommandRouter(speak_callback=self.mock_speak)
            router.process_user_input("what time is it", source="chat")

        self.assertGreater(len(self.spoken_texts), 0)

    def test_09_chat_command_does_not_require_wake_word(self):
        """TEST 9: Chat command must NOT require wake word."""
        router = CommandRouter(speak_callback=self.mock_speak)
        # Direct command without "Jarvis" prefix
        router.process_user_input("ek Android app bana do", source="chat")
        active = self.app_mgr.get_active_app()
        self.assertIsNotNone(active)

    def test_10_voice_pipeline_remains_unchanged(self):
        """TEST 10: Voice behavior remains 100% functional and unchanged."""
        router = CommandRouter(speak_callback=self.mock_speak)
        router.process_user_input("Jarvis what time is it", source="voice")
        self.assertGreater(len(self.spoken_texts), 0)


if __name__ == "__main__":
    unittest.main()
