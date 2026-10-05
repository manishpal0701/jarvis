import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ai.ask_ollama import ask_ollama, clean_response_for_tts, _build_pipeline
from memory.memory_manager import MemoryManager
from conversation.conversation_manager import ConversationManager

class TestPhase1AResponseQuality(unittest.TestCase):

    def setUp(self):
        ConversationManager().clear_history()

    def test_clean_response_for_tts(self):
        sample_raw = "Jarvis: ### Maggi Recipe\n1. Boiled water.\n2. Add noodles.\n**Enjoy!**"
        cleaned = clean_response_for_tts(sample_raw)
        self.assertNotIn("Jarvis:", cleaned)
        self.assertNotIn("###", cleaned)
        self.assertNotIn("1. ", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertTrue(len(cleaned) > 0)

    def test_1_maggi_recipe_formatting(self):
        resp = ask_ollama("mujhe bhookh lagi hai maggi ki recipe batao", "Manish", "owner")
        self.assertNotIn("###", resp)
        self.assertNotIn("1. ", resp)
        self.assertNotIn("Jarvis:", resp)
        self.assertTrue(len(resp.split(".")) <= 6)

    def test_2_vague_app_building_follow_up(self):
        messages, intel, _ = _build_pipeline("mujhe ek app banana hai", "Manish", "owner")
        self.assertEqual(intel.get("intent"), "vague_building_request")
        self.assertTrue(intel.get("requires_follow_up"))

        resp = ask_ollama("mujhe ek app banana hai", "Manish", "owner")
        self.assertIn("?", resp)

    def test_3_supportive_frustration_response(self):
        messages, intel, _ = _build_pipeline("yaar mera code chal nahi raha", "Manish", "owner")
        self.assertEqual(intel.get("emotion"), "frustrated")

        resp = ask_ollama("yaar mera code chal nahi raha", "Manish", "owner")
        self.assertTrue(any(w in resp.lower() for w in ["boss", "tension", "code", "error", "dekh", "issue", "help"]))

    def test_4_celebratory_response(self):
        messages, intel, _ = _build_pipeline("finally project complete ho gaya", "Manish", "owner")
        self.assertIn(intel.get("emotion"), ["excited", "happy"])

        resp = ask_ollama("finally project complete ho gaya", "Manish", "owner")
        self.assertTrue(len(resp) > 0)

    def test_5_memory_retrieval_when_relevant(self):
        mem_mgr = MemoryManager()
        mem_mgr.store("My current project is Jarvis AI", memory_type="project", project="Jarvis AI", tags=["project"])

        rel = mem_mgr.retrieve_relevant("mera current project kya hai", limit=3, min_score=1.0)
        self.assertTrue(len(rel) > 0)
        self.assertIn("Jarvis AI", rel[0]["content"])

        resp = ask_ollama("mera current project kya hai", "Manish", "owner")
        self.assertTrue(any(w in resp.lower() for w in ["jarvis", "ai", "project"]))

    def test_6_memory_relevance_filtering_when_irrelevant(self):
        mem_mgr = MemoryManager()
        rel = mem_mgr.retrieve_relevant("maggi ki recipe batao", limit=3, min_score=1.0)
        self.assertEqual(len(rel), 0)

        resp = ask_ollama("maggi ki recipe batao", "Manish", "owner")
        self.assertNotIn("Jarvis AI", resp)

    def test_7_hallucination_protection(self):
        resp = ask_ollama("Who won today's local city election in Metropolis 2026?", "Manish", "owner")
        self.assertTrue(any(phrase in resp.lower() for phrase in [
            "not sure", "don't know", "no verified", "verified", "information", "guess", "sure about that", "don't have"
        ]))


    def test_section_15_all_8_scenarios(self):
        """Validates all 8 required test queries from Section 15 of the Phase 1A spec."""
        # 1. Recipe request
        r1 = ask_ollama("mujhe bhookh lagi hai maggi ki recipe bata", "Manish", "owner")
        self.assertNotIn("1.", r1)
        self.assertNotIn("###", r1)
        self.assertNotIn("saamagri", r1.lower())

        # 2. Error support
        r2 = ask_ollama("yaar mera code baar baar error de raha hai", "Manish", "owner")
        self.assertTrue(len(r2) > 0)
        self.assertNotIn("Waiting for next command", r2)

        # 3. Emotional mood off
        r3 = ask_ollama("aaj mood off hai", "Manish", "owner")
        self.assertTrue(len(r3) > 0)
        self.assertNotIn("As an AI", r3)

        # 4. Memory grounding
        mem_mgr = MemoryManager()
        mem_mgr.store("My current project is Jarvis AI", memory_type="project", project="Jarvis AI", tags=["project"])
        r4 = ask_ollama("mera current project kya hai", "Manish", "owner")
        self.assertIn("Jarvis", r4)

        # 5. Planning / context reasoning without hallucination
        r5 = ask_ollama("kal mujhe kya karna chahiye", "Manish", "owner")
        self.assertTrue(len(r5) > 0)
        self.assertNotIn("Waiting for next command", r5)

        # 6. Short natural greeting
        r6 = ask_ollama("hello jarvis", "Manish", "owner")
        self.assertTrue(len(r6) > 0)

        # 7. Natural English tech question
        r7 = ask_ollama("what is python", "Manish", "owner")
        self.assertTrue(len(r7) > 0)

        # 8. Natural Hinglish casual query
        r8 = ask_ollama("bhai tu kya kar raha hai", "Manish", "owner")
        self.assertTrue(len(r8) > 0)


if __name__ == "__main__":
    unittest.main()

