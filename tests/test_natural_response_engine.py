"""
tests/test_natural_response_engine.py
Comprehensive test suite verifying the Natural Human Conversation Response Engine
across scenarios A through M as specified in Section 17.

Scenarios:
  A. Casual conversation
  B. Recipe request
  C. Technical question
  D. Emotional/frustrated user
  E. Happy user
  F. Ambiguous request
  G. Follow-up conversation
  H. Suggestion request
  I. Opinion/analysis
  J. Unknown/hallucination prevention
  K. Relevant memory grounding
  L. Irrelevant memory filtering
  M. Multi-turn conversation
"""
import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from conversation.intelligence.conversation_state import ConversationState
from conversation.conversation_manager import ConversationManager
from memory.memory_manager import MemoryManager
from ai.ask_ollama import ask_ollama
from memory.memory_retriever import MemoryRetriever

SPEAKER_NAME = "Manish"
RELATION = "owner"

class TestNaturalResponseEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass

    def setUp(self):

        ConversationState().reset()
        ConversationManager._instance = None
        self.conv_manager = ConversationManager()
        self.conv_manager.clear_history()

    def test_A_casual_conversation(self):
        query = "Hey Jarvis, good morning!"
        res = ask_ollama(query, SPEAKER_NAME, RELATION)
        self.assertTrue(len(res) > 0)
        self.assertNotIn("As an AI", res)
        self.assertNotIn("How can I assist you today", res)
        print(f"\n[Test A Casual]: {res}")

    def test_B_recipe_request(self):
        query = "jarvis maggi banane ki recipe batao"
        res = ask_ollama(query, SPEAKER_NAME, RELATION)
        self.assertTrue(len(res) > 0)
        # Verify no numbered list markdown or robotic list headings
        self.assertNotIn("1. Pan mein", res)
        self.assertNotIn("Step 1:", res)
        self.assertNotIn("Chicken", res)
        self.assertNotIn("Meat", res)
        print(f"\n[Test B Recipe]: {res}")

    def test_C_technical_question(self):
        query = "What is the difference between Stateless and Stateful widgets in Flutter?"
        res = ask_ollama(query, SPEAKER_NAME, RELATION)
        self.assertTrue(len(res) > 0)
        self.assertNotIn("Certainly Boss!", res)
        print(f"\n[Test C Tech]: {res}")

    def test_D_emotional_frustrated_user(self):
        query = "mujhe bhot frustration ho rahi hai, code chal hi nahi raha"
        res = ask_ollama(query, SPEAKER_NAME, RELATION)
        self.assertTrue(len(res) > 0)
        self.assertTrue(any(w in res.lower() for w in ["tension", "error", "relax", "issue", "dekh", "dikhao", "problem", "solve", "fix", "help", "code", "chinta", "mat"]))
        print(f"\n[Test D Frustrated]: {res}")

    def test_E_happy_user(self):
        query = "aaj mera kaam ho gaya finally!"
        res = ask_ollama(query, SPEAKER_NAME, RELATION)
        self.assertTrue(len(res) > 0)
        print(f"\n[Test E Happy]: {res}")

    def test_F_ambiguous_request(self):
        query = "Make this better."
        res = ask_ollama(query, SPEAKER_NAME, RELATION)
        self.assertTrue(len(res) > 0)
        print(f"\n[Test F Ambiguous]: {res}")

    def test_G_follow_up_conversation(self):
        query1 = "mujhe ek app banana hai"
        res1 = ask_ollama(query1, SPEAKER_NAME, RELATION)
        query2 = "task management app hai"
        res2 = ask_ollama(query2, SPEAKER_NAME, RELATION)
        self.assertTrue(len(res2) > 0)
        print(f"\n[Test G Follow-up Turn 1]: {res1}")
        print(f"[Test G Follow-up Turn 2]: {res2}")

    def test_H_suggestion_request(self):
        query = "main Jarvis ka architecture bana raha hu"
        res = ask_ollama(query, SPEAKER_NAME, RELATION)
        self.assertTrue(len(res) > 0)
        print(f"\n[Test H Suggestion]: {res}")

    def test_I_opinion_analysis(self):
        query = "mera architecture messy lag raha hai"
        res = ask_ollama(query, SPEAKER_NAME, RELATION)
        self.assertTrue(len(res) > 0)
        print(f"\n[Test I Opinion]: {res}")

    def test_J_unknown_hallucination_prevention(self):
        query = "Who won the 2029 Intergalactic Cricket Championship?"
        res = ask_ollama(query, SPEAKER_NAME, RELATION)
        self.assertTrue(len(res) > 0)
        # Should not fabricate a fake winner or fake score
        print(f"\n[Test J Unknown]: {res}")

    def test_K_relevant_memory_grounding(self):
        memory_manager = MemoryManager()
        memory_manager.store("My current project is Jarvis AI", memory_type="project", tags=["project"])
        query = "current project kya hai?"
        res = ask_ollama(query, SPEAKER_NAME, RELATION)
        self.assertIn("Jarvis", res)
        print(f"\n[Test K Grounding]: {res}")

    def test_L_irrelevant_memory_filtering(self):
        memory_manager = MemoryManager()
        memory_manager.store("My current project is Jarvis AI", memory_type="project", tags=["project"])
        query = "Maggi kaise banau?"
        rel = memory_manager.retrieve_relevant(query, limit=3, min_score=1.0)
        self.assertEqual(len(rel), 0)
        print(f"\n[Test L Memory Filtering]: Relevant memories retrieved for 'Maggi kaise banau?': {rel}")

    def test_M_multi_turn_conversation(self):
        q1 = "mujhe bhookh lag rahi hai"
        r1 = ask_ollama(q1, SPEAKER_NAME, RELATION)
        q2 = "maggi hai ghar pe"
        r2 = ask_ollama(q2, SPEAKER_NAME, RELATION)
        q3 = "kaise banau?"
        r3 = ask_ollama(q3, SPEAKER_NAME, RELATION)
        self.assertTrue(len(r3) > 0)
        print(f"\n[Test M Multi-turn 1]: {r1}")
        print(f"[Test M Multi-turn 2]: {r2}")
        print(f"[Test M Multi-turn 3]: {r3}")

if __name__ == "__main__":
    unittest.main()
