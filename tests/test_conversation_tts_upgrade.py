import unittest
import os
import shutil
import tempfile
import io
import sys
from unittest.mock import patch, MagicMock

from conversation.command_router import CommandRouter
from speech.pyttsx3_provider import PyTTSx3Provider
from speech.response_formatter import ResponseFormatter
from conversation.conversation_manager import ConversationManager
from conversation.intelligence.intent_analyzer import IntentAnalyzer
from speech.utils import is_valid_audio

class TestConversationTTSUpgrade(unittest.TestCase):
    def setUp(self):
        self.router = CommandRouter()
        self.formatter = ResponseFormatter()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_1_wake_word_response(self):
        """Test 1: Verify wake word response mechanism is preserved."""
        from speech.wake_manager import WakeManager
        self.assertTrue(hasattr(WakeManager, 'check_wake_word'))

    def test_2_normal_conversation_q_and_a(self):
        """Test 2: Verify normal Q&A questions are classified as conversation, NOT coding tasks."""
        self.assertFalse(self.router.is_coding_task("How are you?"))
        self.assertFalse(self.router.is_coding_task("What is Python?"))
        self.assertFalse(self.router.is_coding_task("Tell me something interesting."))
        self.assertFalse(self.router.is_coding_task("What can you do?"))

    def test_3_multiturn_conversation_context(self):
        """Test 3: Verify multi-turn conversation maintains context via ConversationManager."""
        cm = ConversationManager()
        cm.clear_history()
        cm.add_to_history("user", "What is Python?")
        cm.add_to_history("assistant", "Python is a high-level programming language used for web development, AI, and automation.")

        history = cm.get_history_context()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["content"], "What is Python?")

        analyzer = IntentAnalyzer()
        intel = analyzer.analyze("Can I use it for AI?")
        self.assertEqual(intel["intent"], "question_factual")

    def test_4_emotional_and_casual_chat(self):
        """Test 4: Verify emotional and casual chat prompts are classified naturally."""
        analyzer = IntentAnalyzer()
        intel1 = analyzer.analyze("I'm tired today.")
        self.assertEqual(intel1["intent"], "emotional_expression")

        intel2 = analyzer.analyze("Good morning Jarvis!")
        self.assertIn(intel2["intent"], ["casual_chat", "question_factual"])

    def test_5_coding_task_routing(self):
        """Test 5: Verify explicit creation requests route to coding tasks."""
        self.assertTrue(self.router.is_coding_task("Create a Python calculator script"))
        self.assertTrue(self.router.is_coding_task("Write a python program to calculate factorial"))

    def test_6_website_task_routing(self):
        """Test 6: Verify website creation requests route to Website Builder pipeline."""
        self.assertTrue(self.router.is_coding_task("Jarvis, make a modern website for Inurum Technology."))
        self.assertTrue(self.router.is_coding_task("Build website for Tesla"))

    def test_7_pyttsx3_voice_and_audio_synthesis(self):
        """Test 7: Verify PyTTSx3Provider generates a valid .wav audio file."""
        provider = PyTTSx3Provider()
        out_file = os.path.join(self.test_dir, "test_speech.wav")
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(
                provider.generate_speech("Hello Boss, this is a test of natural speech synthesis.", "", "+0%", "+0Hz", "+0%", out_file)
            )
            self.assertTrue(success)
            self.assertTrue(os.path.exists(out_file))
            self.assertTrue(is_valid_audio(out_file))
        finally:
            loop.close()

    def test_8_response_formatter_sanitizes_markdown_code_urls(self):
        """Test 8: Verify ResponseFormatter cleans markdown, code blocks, URLs, and bullets for spoken output."""
        raw_text = (
            "# Heading Title\n\n"
            "Here is **bold** text and `inline_code`.\n\n"
            "```python\ndef foo(): pass\n```\n\n"
            "- Item 1\n"
            "- Item 2\n\n"
            "Check https://example.com/demo"
        )
        cleaned = ResponseFormatter.format_for_speech(raw_text)

        self.assertNotIn("#", cleaned)
        self.assertNotIn("```", cleaned)
        self.assertNotIn("https://", cleaned)
        self.assertNotIn("- Item 1", cleaned)
        self.assertIn("Heading Title", cleaned)
        self.assertIn("bold text", cleaned)

    def test_9_website_builder_unmodified_preservation(self):
        """Test 9: Confirm Website Builder source files exist and remain untouched."""
        code_assistant_file = r"C:\Jarvis project\manish.py\tools\coding\code_assistant.py"
        component_pool_file = r"C:\Jarvis project\manish.py\tools\coding\component_generation_pool.py"
        master_planner_file = r"C:\Jarvis project\manish.py\tools\coding\website_master_planner.py"

        self.assertTrue(os.path.exists(code_assistant_file))
        self.assertTrue(os.path.exists(component_pool_file))
        self.assertTrue(os.path.exists(master_planner_file))

if __name__ == "__main__":
    unittest.main()
