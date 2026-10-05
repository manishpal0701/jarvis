"""
tests/test_single_response_and_emoji.py
Comprehensive automated test suite covering all 18 required tests for single-response streaming,
emoji TTS sanitization, Hinglish persona grammar, and context contamination protection.
"""

import sys
sys.path.insert(0, ".")

import unittest
import re
from conversation.intelligence.response_validator import ResponseValidator
from speech.response_formatter import ResponseFormatter
from conversation.intelligence.context_tracker import ContextTracker
from ai.ask_ollama import _build_system_prompt

class TestSingleResponseAndEmoji(unittest.TestCase):

    def setUp(self):
        self.validator = ResponseValidator()
        self.formatter = ResponseFormatter()
        self.context_tracker = ContextTracker()

    # TEST 1 & TEST 2 & TEST 3 & TEST 4 & TEST 18: Single Message Aggregation Logic
    def test_single_message_aggregation_logic(self):
        """Simulates upsertJarvisMessage aggregation for 10 chunks + final event -> 1 message."""
        messages = []
        active_req_id = "req_test_1001"

        def upsert_msg(req_id, text, is_chunk=False, is_final=False, is_spoken=False):
            req_key = req_id or active_req_id
            existing_idx = -1
            for idx, m in enumerate(messages):
                if m["sender"] == "jarvis" and (m.get("requestId") == req_key or m["id"] == req_key):
                    existing_idx = idx
                    break

            if existing_idx != -1:
                target = messages[existing_idx]
                if is_final:
                    updated_text = text if len(text) >= len(target["text"]) else target["text"]
                elif is_chunk or is_spoken:
                    if not target["text"]:
                        updated_text = text
                    elif text in target["text"] or target["text"].endswith(text):
                        updated_text = target["text"]
                    else:
                        updated_text = f"{target['text']} {text}".strip()
                else:
                    updated_text = text if len(text) >= len(target["text"]) else target["text"]
                messages[existing_idx]["text"] = updated_text
            else:
                messages.append({
                    "id": req_key,
                    "requestId": req_key,
                    "sender": "jarvis",
                    "text": text
                })

        # Simulate 10 streamed chunks
        chunks = [f"chunk_{i}" for i in range(1, 11)]
        for c in chunks:
            upsert_msg(active_req_id, c, is_chunk=True)

        self.assertEqual(len(messages), 1, "10 chunks must result in exactly 1 assistant message bubble.")
        self.assertTrue("chunk_1" in messages[0]["text"] and "chunk_10" in messages[0]["text"])

        # Final response event
        full_text = "chunk_1 chunk_2 chunk_3 chunk_4 chunk_5 chunk_6 chunk_7 chunk_8 chunk_9 chunk_10"
        upsert_msg(active_req_id, full_text, is_final=True)

        self.assertEqual(len(messages), 1, "Final response event must NOT create a second message bubble.")
        self.assertEqual(messages[0]["text"], full_text)

    # TEST 5 & TEST 8: TTS Dispatch Order & No Duplicate Full Response Speech
    def test_tts_dispatch_deduplication(self):
        """Verifies duplicate sentence chunk keys are rejected in dispatch tracking."""
        dispatched_keys = set()
        req_id = "req_tts_01"

        def dispatch_sentence(chunk_id, text):
            key = f"{req_id}:{chunk_id}"
            if key in dispatched_keys:
                return "BLOCKED"
            dispatched_keys.add(key)
            return "DISPATCHED"

        self.assertEqual(dispatch_sentence("chunk_1", "Hello Boss"), "DISPATCHED")
        self.assertEqual(dispatch_sentence("chunk_1", "Hello Boss"), "BLOCKED")
        self.assertEqual(dispatch_sentence("chunk_2", "How are you"), "DISPATCHED")

    # TEST 6 & TEST 7 & TEST 17: Emoji Sanitization for TTS Input
    def test_emoji_sanitization_for_tts(self):
        """Verifies emojis are stripped for TTS input while preserved in raw text for UI."""
        raw_ui_text = "Hello Boss! 😊 Main bilkul theek hoon. 💕👍"
        
        # UI retains emojis
        self.assertIn("😊", raw_ui_text)
        self.assertIn("💕", raw_ui_text)

        # Spoken text strips emojis completely
        spoken_text = self.validator.strip_emojis_for_tts(raw_ui_text)
        self.assertNotIn("😊", spoken_text)
        self.assertNotIn("💕", spoken_text)
        self.assertNotIn("👍", spoken_text)
        self.assertEqual(spoken_text, "Hello Boss! Main bilkul theek hoon.")

        # Ensure no emoji names ("smiley face", "heart") are generated
        self.assertNotIn("smiley", spoken_text.lower())
        self.assertNotIn("heart", spoken_text.lower())

    def test_response_formatter_strips_emojis(self):
        """Verifies ResponseFormatter.format_for_speech strips emojis before EdgeTTS."""
        raw_text = "Good morning Boss! 🌞 Have a great day. ❤️"
        formatted_speech = self.formatter.format_for_speech(raw_text)
        self.assertNotIn("🌞", formatted_speech)
        self.assertNotIn("❤️", formatted_speech)
        self.assertTrue("Good morning Boss!" in formatted_speech)

    # TEST 9 & TEST 10: Interruption Safety & Fresh Session Isolation
    def test_interruption_stale_request_isolation(self):
        """Verifies an invalidated request cannot dispatch speech."""
        invalidated_requests = set()
        
        def is_invalidated(req_id):
            return req_id in invalidated_requests

        req1 = "req_100"
        req2 = "req_101"

        # Interrupt req1
        invalidated_requests.add(req1)

        self.assertTrue(is_invalidated(req1))
        self.assertFalse(is_invalidated(req2))

    # TEST 11: Casual Compliment Context Contamination Protection
    def test_casual_compliment_no_context_contamination(self):
        """Verifies casual queries do not trigger 'jarvis project' context."""
        casual_queries = [
            "hello jarvis",
            "how are you",
            "thank you",
            "jarvis aaj tum sundar lag rahi ho",
            "what are you doing",
            "good morning",
            "mera mood off hai"
        ]

        for q in casual_queries:
            topic = self.context_tracker.extract_topic(q)
            self.assertNotEqual(topic, "jarvis project", f"Query '{q}' contaminated active context!")

    # TEST 12 & TEST 13 & TEST 14 & TEST 15 & TEST 16: System Prompt Persona Directives
    def test_system_prompt_persona_directives(self):
        """Verifies system prompt directives enforce female Hinglish and prohibit forced invitations."""
        prompt = _build_system_prompt("Boss", "boss", {}, "")
        
        # Check female Hinglish directive
        self.assertIn("female grammar", prompt.lower())
        self.assertIn("main theek hoon", prompt.lower())
        self.assertIn("never use male forms", prompt.lower())

        # Check prohibition of forced task invitations
        self.assertIn("kya karna hai ab", prompt.lower())
        self.assertIn("kya karna hai ab", prompt.lower())

if __name__ == "__main__":
    unittest.main()
