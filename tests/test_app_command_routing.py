"""
tests/test_app_command_routing.py
Comprehensive unit test suite for JARVIS Command Router and App Builder Intent Routing.
Verifies routing priority, semantic intent detection, brief continuation, source tracking, and non-regression.
"""
import unittest
from tools.app_builder.app_manager import AppManager
from tools.app_builder.app_model import AppState
from tools.app_builder.app_intent_router import AppIntentRouter
from conversation.command_router import CommandRouter


class TestAppCommandRouting(unittest.TestCase):

    def setUp(self):
        self.app_mgr = AppManager()
        self.app_mgr.reset()
        self.spoken_messages = []

        def mock_speak(text):
            self.spoken_messages.append(text)

        self.router = CommandRouter(speak_callback=mock_speak)

    def tearDown(self):
        self.app_mgr.reset()

    def test_1_what_time_is_it_routes_to_time(self):
        """1. 'what time is it' -> TIME response"""
        self.router.process_user_input("what time is it", source="voice")
        self.assertTrue(len(self.spoken_messages) > 0)
        self.assertIn("It's", self.spoken_messages[-1])

    def test_2_explicit_hindi_app_creation_routes_to_app_builder(self):
        """2. 'Jarvis ek Android app bana do' -> APP_BUILD"""
        self.router.process_user_input("Jarvis ek Android app bana do", source="voice")
        active = self.app_mgr.get_active_app()
        self.assertIsNotNone(active)
        self.assertEqual(active.status, AppState.WAITING_FOR_BRIEF)

    def test_3_create_music_player_app_routes_to_app_builder(self):
        """3. 'Create a Music Player app' -> APP_BUILD"""
        self.router.process_user_input("Create a Music Player app", source="chat")
        active = self.app_mgr.get_active_app()
        self.assertIsNotNone(active)
        self.assertIn(active.status, [AppState.WAITING_FOR_BRIEF, AppState.BRIEF_READY, AppState.STARTING, AppState.PLANNING])

    def test_4_detailed_spotify_brief_routes_to_app_builder_and_advances(self):
        """4. Detailed Spotify-style Music Player brief -> APP_BUILD & auto-advances"""
        brief = (
            "Create a Spotify-style music player with login, home screen, search, playlists, "
            "liked songs, recently played, queue, shuffle, repeat, categories, album pages, "
            "artist pages, persistent playback state and a Node.js backend."
        )
        self.router.process_user_input(brief, source="chat")
        active = self.app_mgr.get_active_app()
        self.assertIsNotNone(active)
        # Should not be trapped in WAITING_FOR_BRIEF, should auto-advance
        self.assertIn(active.status, [AppState.BRIEF_READY, AppState.STARTING, AppState.PLANNING])
        self.assertTrue(len(active.brief.features) > 0)

    def test_5_detailed_brief_with_time_words_routes_to_app_builder(self):
        """5. Detailed brief containing 'time' or 'date' -> APP_BUILD (not TIME)"""
        brief = (
            "Create a time tracking mobile app with real-time sync, current time display, "
            "date picker, project categories, timer logs, and Node.js backend REST APIs."
        )
        self.router.process_user_input(brief, source="voice")
        active = self.app_mgr.get_active_app()
        self.assertIsNotNone(active)
        # Verify it did not return current clock time
        for msg in self.spoken_messages:
            self.assertNotIn("It's ", msg)
        self.assertIn(active.status, [AppState.BRIEF_READY, AppState.STARTING, AppState.PLANNING])

    def test_6_waiting_for_brief_app_name_continuation(self):
        """6. WAITING_FOR_BRIEF + 'App ka naam Music Player hai' -> APP_BRIEF_CONTINUATION"""
        # Create initial pending app project
        self.app_mgr.create_app_project(initial_prompt="Jarvis ek app bana do", task_type="APP")
        active = self.app_mgr.get_active_app()
        self.assertEqual(active.status, AppState.WAITING_FOR_BRIEF)

        # User sends continuation message
        self.router.process_user_input("App ka naam Music Player hai.", source="chat")
        updated = self.app_mgr.get_active_app()
        self.assertEqual(updated.brief.name, "Music Player")

    def test_7_waiting_for_brief_feature_continuation(self):
        """7. WAITING_FOR_BRIEF + feature description -> APP_BRIEF_CONTINUATION"""
        self.app_mgr.create_app_project(initial_prompt="Jarvis ek app bana do", task_type="APP")
        active = self.app_mgr.get_active_app()

        self.router.process_user_input(
            "App ka naam Music Player hai. Isme login, search, playlists, liked songs aur persistent player screen honi chahiye.",
            source="chat"
        )
        updated = self.app_mgr.get_active_app()
        self.assertIn(updated.status, [AppState.BRIEF_READY, AppState.STARTING, AppState.PLANNING])
        self.assertTrue(len(updated.brief.features) > 0)

    def test_8_chat_source_routing(self):
        """8. Chat source produces identical routing as voice source"""
        self.router.process_user_input("Create an expense tracker app with login and reports", source="chat")
        active = self.app_mgr.get_active_app()
        self.assertIsNotNone(active)

    def test_9_voice_source_routing(self):
        """9. Voice source produces identical routing as chat source"""
        self.router.process_user_input("Create an expense tracker app with login and reports", source="voice")
        active = self.app_mgr.get_active_app()
        self.assertIsNotNone(active)

    def test_10_existing_normal_commands_functional(self):
        """10. Existing normal commands (date, time) remain fully functional"""
        self.spoken_messages.clear()
        self.router.process_user_input("what is today's date", source="voice")
        self.assertTrue(len(self.spoken_messages) > 0)
        self.assertIn("Today is", self.spoken_messages[-1])


if __name__ == "__main__":
    unittest.main()
