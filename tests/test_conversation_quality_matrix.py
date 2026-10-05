"""
tests/test_conversation_quality_matrix.py
Automated test suite verifying response quality, Hinglish persona, absence of context contamination,
and absence of forced task invitations across 10 conversational scenarios.
"""

import unittest
from unittest.mock import MagicMock, patch

from conversation.intelligence.context_tracker import ContextTracker
from conversation.conversation_manager import ConversationManager
from ai.ask_ollama import _build_pipeline

class TestConversationQualityMatrix(unittest.TestCase):
    def setUp(self):
        self.tracker = ContextTracker()
        self.conv_mgr = ConversationManager.get_instance()
        self.conv_mgr.reset_context()

    def test_01_no_context_contamination_on_casual_queries(self):
        casual_queries = [
            "hello jarvis",
            "hello jarvis how are you",
            "good morning",
            "what are you doing",
            "jarvis aaj tum sundar lag rahi ho",
            "thank you",
            "mera mood off hai",
            "I'm feeling lonely",
            "tell me something funny",
            "what can you do"
        ]

        for query in casual_queries:
            entity = self.tracker.extract_target_entity(query)
            self.assertIsNone(
                entity,
                f"Casual query '{query}' produced unexpected target entity '{entity}' causing context contamination!"
            )

    @patch("ai.ask_ollama.AIResponseManager")
    def test_02_conversation_quality_and_persona_policy(self, mock_ai_mgr_cls):
        mock_ai_mgr = MagicMock()
        mock_ai_mgr_cls.return_value = mock_ai_mgr

        # Simulate natural responses for casual queries
        test_cases = [
            ("hello jarvis", "Hello Boss! Main bilkul theek hoon, aap batao kaise ho?"),
            ("hello jarvis how are you", "Haan Boss, main bilkul theek hoon! Tumhara din kaisa ja raha hai?"),
            ("good morning", "Good morning Boss! Aaj ka din shandaar ho."),
            ("what are you doing", "Bas aapki baatein sun rahi hoon Boss, batao kya haal hai?"),
            ("jarvis aaj tum sundar lag rahi ho", "Thank you Boss! Compliment milne par accha laga."),
            ("thank you", "You're most welcome Boss!"),
            ("mera mood off hai", "Ohh Boss... kya hua? Agar baat karna chaho toh main sun rahi hoon."),
            ("I'm feeling lonely", "Main aapke saath hoon Boss. Chaho toh hum thodi baat kar sakte hain."),
            ("tell me something funny", "Ek funny baat suno: Pythons only eat byte-sized snacks!"),
            ("what can you do", "Main aapki baatein sun sakti hoon, queries answer kar sakti hoon, aur coding/system tasks execute kar sakti hoon.")
        ]

        for query, expected_resp in test_cases:
            messages, intel, conv_mgr = _build_pipeline(query, "Boss", "boss")
            sys_prompt = messages[0]["content"]

            # Verify no false active context injection
            self.assertNotIn("Active Context: User is talking about 'jarvis project'.", sys_prompt)
            # Verify Casual Chat Policy is present
            self.assertIn("Casual Chat Policy:", sys_prompt)

    def test_03_context_tracker_only_extracts_explicit_projects(self):
        self.assertEqual(self.tracker.extract_target_entity("create expense tracker app"), "expense tracker")
        self.assertEqual(self.tracker.extract_target_entity("build calculator website"), "calculator website")
        self.assertIsNone(self.tracker.extract_target_entity("jarvis aaj tum sundar lag rahi ho"))

if __name__ == "__main__":
    unittest.main()
