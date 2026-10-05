import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from conversation.intelligence.conversation_analyzer import ConversationAnalyzer
from conversation.intelligence.conversation_state import ConversationState
from conversation.intelligence.intent_analyzer import IntentAnalyzer
from conversation.intelligence.emotion_analyzer import EmotionAnalyzer
from conversation.intelligence.context_tracker import ContextTracker
from conversation.intelligence.response_strategy import ResponseStrategyEngine

class TestConversationIntelligence(unittest.TestCase):

    def setUp(self):
        ConversationState().reset()
        self.analyzer = ConversationAnalyzer()

    def test_1_normal_question(self):
        res = self.analyzer.analyze_input("What is the capital of France?")
        self.assertEqual(res["intent"], "question_factual")
        self.assertFalse(res["requires_clarification"])
        self.assertFalse(res["requires_follow_up"])
        self.assertEqual(res["action_type"], "answer_directly")

    def test_2_follow_up_question_request(self):
        res = self.analyzer.analyze_input("I want to build an app.")
        self.assertEqual(res["intent"], "vague_building_request")
        self.assertTrue(res["requires_follow_up"])
        self.assertEqual(res["action_type"], "ask_follow_up")
        self.assertEqual(res["response_style"], "curious_probing")

    def test_3_ambiguous_request(self):
        res = self.analyzer.analyze_input("Make this better.")
        self.assertEqual(res["intent"], "ambiguous_request")
        self.assertTrue(res["requires_clarification"])
        self.assertEqual(res["action_type"], "ask_clarification")

    def test_4_happy_user(self):
        res = self.analyzer.analyze_input("I am so happy with this result!")
        self.assertEqual(res["emotion"], "happy")
        self.assertIn(res["action_type"], ["celebrate_success", "answer_directly", "acknowledge_emotion"])

    def test_5_frustrated_user(self):
        res = self.analyzer.analyze_input("I'm frustrated because this code isn't working.")
        self.assertEqual(res["emotion"], "frustrated")
        self.assertEqual(res["action_type"], "acknowledge_emotion")
        self.assertEqual(res["response_style"], "empathic_helpful")

    def test_6_sad_user(self):
        res = self.analyzer.analyze_input("I feel so sad and down today.")
        self.assertEqual(res["emotion"], "sad")
        self.assertEqual(res["action_type"], "acknowledge_emotion")

    def test_7_excited_user(self):
        res = self.analyzer.analyze_input("I finally fixed it!")
        self.assertEqual(res["emotion"], "excited")
        self.assertEqual(res["action_type"], "celebrate_success")
        self.assertEqual(res["response_style"], "celebratory")

    def test_8_topic_continuation(self):
        # First turn sets topic
        self.analyzer.analyze_input("I want to build a Flutter app.")
        # Second turn uses continuation pronoun
        res = self.analyzer.analyze_input("What features should it have?")
        self.assertEqual(res["topic"], "app development")

    def test_9_topic_change(self):
        # First turn sets app topic
        self.analyzer.analyze_input("I want to build a Flutter app.")
        # Second turn changes topic to France
        res = self.analyzer.analyze_input("What is the capital of France?")
        self.assertEqual(res["topic"], "geography & world capitals")

    def test_10_suggestion_required_request(self):
        res = self.analyzer.analyze_input("What do you think about my architecture?")
        self.assertEqual(res["intent"], "opinion_request")
        self.assertTrue(res["requires_suggestion"])
        self.assertEqual(res["action_type"], "provide_suggestions")

    def test_11_clarification_required_request(self):
        res = self.analyzer.analyze_input("Fix this.")
        self.assertTrue(res["requires_clarification"])
        self.assertEqual(res["action_type"], "ask_clarification")

    def test_12_casual_conversation(self):
        res = self.analyzer.analyze_input("Hey Jarvis, how are you?")
        self.assertEqual(res["intent"], "casual_chat")
        self.assertEqual(res["action_type"], "answer_directly")
        self.assertEqual(res["response_style"], "concise")

    def test_13_followup_simple_expense_tracker(self):
        from conversation.conversation_manager import ConversationManager
        mgr = ConversationManager.get_instance()
        mgr.reset_context()

        # Turn 1
        res1 = mgr.process_and_resolve_input("Ek expense tracker app bana do.")
        self.assertEqual(mgr.active_entity, "expense tracker app")

        # Turn 2: Follow up reference "isme"
        res2 = mgr.process_and_resolve_input("Isme dark theme rakhna.")
        self.assertTrue(res2["has_followup"])
        self.assertEqual(res2["pronoun"], "isme")
        self.assertIn("expense tracker app", res2["resolved_text"])

    def test_14_followup_multi_turn_calculator(self):
        from conversation.conversation_manager import ConversationManager
        mgr = ConversationManager.get_instance()
        mgr.reset_context()

        # Turn 1
        res1 = mgr.process_and_resolve_input("Python me ek calculator bana do.")
        self.assertIn("calculator", mgr.active_entity.lower())

        # Turn 2
        res2 = mgr.process_and_resolve_input("Isme history bhi add karo.")
        self.assertTrue(res2["has_followup"])
        self.assertEqual(res2["pronoun"], "isme")
        self.assertIn("calculator", res2["resolved_text"].lower())

    def test_15_context_reset(self):
        from conversation.conversation_manager import ConversationManager
        mgr = ConversationManager.get_instance()
        mgr.reset_context()

        # Turn 1
        mgr.process_and_resolve_input("Main ek weather app bana raha hoon.")
        self.assertEqual(mgr.active_entity, "weather app")

        # Turn 2: Reset context
        mgr.reset_context()
        self.assertIsNone(mgr.active_entity)
        self.assertEqual(len(mgr.history), 0)

        # Turn 3: Follow up without active context should NOT point to weather app
        res3 = mgr.process_and_resolve_input("Isme login add karo.")
        self.assertNotIn("weather app", res3.get("resolved_text", ""))

    def test_16_unrelated_request_date_filtering(self):
        from conversation.conversation_manager import ConversationManager
        mgr = ConversationManager.get_instance()
        mgr.reset_context()

        # Turn 1: Date question
        mgr.add_to_history("user", "What is the current date?")
        mgr.add_to_history("assistant", "Today is September 08, 2026, Boss.")

        # Turn 2: Flutter question
        filtered_hist = mgr.get_history_context(current_query="Flutter me Riverpod kya hai?")
        # Date turn should be excluded from filtered history
        for msg in filtered_hist:
            self.assertNotIn("current date", msg.get("content", "").lower())


if __name__ == "__main__":
    unittest.main()

