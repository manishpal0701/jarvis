"""
tests/test_sentence_streaming_repair.py
Automated quality test suite verifying sentence boundary detection and buffering
in the conversational LLM streaming TTS pipeline. Covers all 10 mandatory test cases.
"""

import unittest
from ai.sentence_buffer import StreamingSentenceBuffer

class TestSentenceStreamingRepair(unittest.TestCase):

    def setUp(self):
        self.buffer = StreamingSentenceBuffer()

    def test_case_1_single_sentence_multi_token_stream(self):
        """
        TEST 1: 25-token fragment stream yielding exactly 1 complete sentence.
        Must NOT split on commas or character length threshold.
        """
        tokens = [
            "Main", " dekh", " rahi", " hoon", " Boss,", " background", " me",
            " ek", " soft", " instrumental", " track", " hai,", " jaise", " koi",
            " piano", " ya", " acoustic", " guitar", " ke", " saath", " slow", " vibe."
        ]
        extracted = []
        for t in tokens:
            extracted.extend(self.buffer.append(t, request_id="test_req_1"))
        extracted.extend(self.buffer.flush_remaining(request_id="test_req_1"))

        expected_sentence = (
            "Main dekh rahi hoon Boss, background me ek soft instrumental track hai, "
            "jaise koi piano ya acoustic guitar ke saath slow vibe."
        )

        self.assertEqual(len(extracted), 1, f"Expected 1 sentence chunk, got {len(extracted)}: {extracted}")
        self.assertEqual(extracted[0], expected_sentence)

    def test_case_2_two_distinct_sentences_in_token_stream(self):
        """
        TEST 2: Input stream with 2 complete sentences.
        Expected: Chunk 1 = "Bilkul Boss, main check kar leti hoon."
                  Chunk 2 = "Phir tumhe bata dungi."
        """
        tokens = [
            "Bilkul Boss,", " main", " check", " kar", " leti", " hoon.",
            " Phir", " tumhe", " bata", " dungi."
        ]
        extracted = []
        for t in tokens:
            extracted.extend(self.buffer.append(t, request_id="test_req_2"))
        extracted.extend(self.buffer.flush_remaining(request_id="test_req_2"))

        self.assertEqual(len(extracted), 2, f"Expected 2 chunks, got {len(extracted)}: {extracted}")
        self.assertEqual(extracted[0], "Bilkul Boss, main check kar leti hoon.")
        self.assertEqual(extracted[1], "Phir tumhe bata dungi.")

    def test_case_3_standard_hinglish_two_sentences(self):
        """
        TEST 3: "Samajh gayi Boss." + " Ye streaming issue tha." -> 2 chunks.
        """
        tokens = ["Samajh gayi Boss.", " Ye", " streaming", " issue", " tha."]
        extracted = []
        for t in tokens:
            extracted.extend(self.buffer.append(t, request_id="test_req_3"))
        extracted.extend(self.buffer.flush_remaining(request_id="test_req_3"))

        self.assertEqual(len(extracted), 2)
        self.assertEqual(extracted[0], "Samajh gayi Boss.")
        self.assertEqual(extracted[1], "Ye streaming issue tha.")

    def test_case_4_single_exclamation_sentence(self):
        """
        TEST 4: "Ho gaya Boss!" -> 1 chunk.
        """
        tokens = ["Ho gaya Boss!"]
        extracted = []
        for t in tokens:
            extracted.extend(self.buffer.append(t, request_id="test_req_4"))
        extracted.extend(self.buffer.flush_remaining(request_id="test_req_4"))

        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0], "Ho gaya Boss!")

    def test_case_5_single_question_sentence(self):
        """
        TEST 5: "Accha?" -> 1 chunk.
        """
        tokens = ["Accha?"]
        extracted = []
        for t in tokens:
            extracted.extend(self.buffer.append(t, request_id="test_req_5"))
        extracted.extend(self.buffer.flush_remaining(request_id="test_req_5"))

        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0], "Accha?")

    def test_case_6_unpunctuated_stream_flushed_at_end(self):
        """
        TEST 6: "Main" " check" " kar" " rahi" " hoon" (No trailing punctuation)
        At stream end: expected 1 final chunk "Main check kar rahi hoon".
        """
        tokens = ["Main", " check", " kar", " rahi", " hoon"]
        extracted = []
        for t in tokens:
            extracted.extend(self.buffer.append(t, request_id="test_req_6"))
        extracted.extend(self.buffer.flush_remaining(request_id="test_req_6"))

        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0], "Main check kar rahi hoon")

    def test_case_7_comma_heavy_hinglish_sentence(self):
        """
        TEST 7: "Bilkul Boss, tension mat lo, main handle kar leti hoon."
        Expected: 1 chunk only. NOT three chunks.
        """
        tokens = ["Bilkul Boss, tension mat lo, main handle kar leti hoon."]
        extracted = []
        for t in tokens:
            extracted.extend(self.buffer.append(t, request_id="test_req_7"))
        extracted.extend(self.buffer.flush_remaining(request_id="test_req_7"))

        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0], "Bilkul Boss, tension mat lo, main handle kar leti hoon.")

    def test_case_8_question_prompt(self):
        """
        TEST 8: "Boss, kya tum chahte ho ki main ise abhi run karun?"
        Expected: 1 chunk.
        """
        tokens = ["Boss, kya tum chahte ho ki main ise abhi run karun?"]
        extracted = []
        for t in tokens:
            extracted.extend(self.buffer.append(t, request_id="test_req_8"))
        extracted.extend(self.buffer.flush_remaining(request_id="test_req_8"))

        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0], "Boss, kya tum chahte ho ki main ise abhi run karun?")

    def test_case_9_multiple_sentences_in_single_token(self):
        """
        TEST 9: "Bilkul Boss. Main abhi check karti hoon." in 1 Ollama token chunk.
        Expected: 2 chunks.
        """
        tokens = ["Bilkul Boss. Main abhi check karti hoon."]
        extracted = []
        for t in tokens:
            extracted.extend(self.buffer.append(t, request_id="test_req_9"))
        extracted.extend(self.buffer.flush_remaining(request_id="test_req_9"))

        self.assertEqual(len(extracted), 2)
        self.assertEqual(extracted[0], "Bilkul Boss.")
        self.assertEqual(extracted[1], "Main abhi check karti hoon.")

    def test_case_10_never_produce_empty_chunks(self):
        """
        TEST 10: Ensure empty strings, whitespace-only tokens, or empty buffer flushes
        never produce empty chunks.
        """
        tokens = ["  ", "", "\n", "\t"]
        extracted = []
        for t in tokens:
            extracted.extend(self.buffer.append(t, request_id="test_req_10"))
        extracted.extend(self.buffer.flush_remaining(request_id="test_req_10"))

        self.assertEqual(len(extracted), 0, "No chunks should be generated for empty/whitespace input")
        for chunk in extracted:
            self.assertTrue(bool(chunk.strip()), "Chunk must not be empty or whitespace-only")


if __name__ == "__main__":
    unittest.main()
