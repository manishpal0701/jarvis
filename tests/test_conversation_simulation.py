import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from conversation.intelligence.conversation_analyzer import ConversationAnalyzer
from conversation.intelligence.conversation_state import ConversationState


class TestConversationSimulation(unittest.TestCase):
    """
    Automated 10-turn multi-turn simulation test verifying real-time session state transitions,
    topic tracking, emotion detection, intent classification, and response strategy execution.
    """

    def setUp(self):
        ConversationState().reset()
        self.analyzer = ConversationAnalyzer()

    def test_10_turn_conversation_flow(self):
        turns = [
            {
                "turn": 1,
                "input": "Hey Jarvis, good morning!",
                "expected_intent": "casual_chat",
                "expected_action": "answer_directly",
                "expected_topic": "casual greeting"
            },
            {
                "turn": 2,
                "input": "I want to build an app.",
                "expected_intent": "vague_building_request",
                "expected_action": "ask_follow_up",
                "expected_topic": "app development"
            },
            {
                "turn": 3,
                "input": "What features should it have?",
                "expected_intent": "suggestion_request",
                "expected_action": "provide_suggestions",
                "expected_topic": "app development"  # Topic continuation
            },
            {
                "turn": 4,
                "input": "I'm frustrated because this code isn't working.",
                "expected_emotion": "frustrated",
                "expected_action": "acknowledge_emotion"
            },
            {
                "turn": 5,
                "input": "Make this better.",
                "expected_intent": "ambiguous_request",
                "expected_action": "ask_clarification"
            },
            {
                "turn": 6,
                "input": "What do you think about my architecture?",
                "expected_intent": "opinion_request",
                "expected_action": "provide_suggestions",
                "expected_topic": "system architecture"
            },
            {
                "turn": 7,
                "input": "I finally fixed it!",
                "expected_emotion": "excited",
                "expected_action": "celebrate_success"
            },
            {
                "turn": 8,
                "input": "I feel so sad and down today.",
                "expected_emotion": "sad",
                "expected_action": "acknowledge_emotion"
            },
            {
                "turn": 9,
                "input": "What is the capital of France?",
                "expected_intent": "question_factual",
                "expected_action": "answer_directly",
                "expected_topic": "geography & world capitals"
            },
            {
                "turn": 10,
                "input": "Tell me more about it.",
                "expected_action": "answer_directly",
                "expected_topic": "geography & world capitals"  # Topic continuation
            }
        ]

        print("\n=================== 10-TURN CONVERSATION SIMULATION ===================")
        for t in turns:
            turn_num = t["turn"]
            user_msg = t["input"]
            res = self.analyzer.analyze_input(user_msg)

            print(f"\n--- Turn {turn_num} ---")
            print(f"User: '{user_msg}'")
            print(f"  [Intent]: {res['intent']} (confidence: {res['confidence']})")
            print(f"  [Emotion]: {res['emotion']}")
            print(f"  [Topic]: {res['topic']}")
            print(f"  [Action Strategy]: {res['action_type']}")
            print(f"  [Style]: {res['response_style']}")
            print(f"  [Goal]: {res['conversation_goal']}")

            if "expected_intent" in t:
                self.assertEqual(res["intent"], t["expected_intent"], f"Turn {turn_num} intent mismatch")
            if "expected_emotion" in t:
                self.assertEqual(res["emotion"], t["expected_emotion"], f"Turn {turn_num} emotion mismatch")
            if "expected_action" in t:
                self.assertEqual(res["action_type"], t["expected_action"], f"Turn {turn_num} action mismatch")
            if "expected_topic" in t:
                self.assertEqual(res["topic"], t["expected_topic"], f"Turn {turn_num} topic mismatch")

        # Snapshot check post 10 turns
        state_snap = ConversationState().get_snapshot()
        self.assertEqual(state_snap["turn_count"], 10)
        self.assertEqual(state_snap["current_topic"], "geography & world capitals")
        print("\nFinal Session State Snapshot:")
        print(state_snap)
        print("=======================================================================")


if __name__ == "__main__":
    unittest.main()
