"""
ai/sentence_buffer.py
Deterministic sentence boundary buffer for streaming LLM responses.
Accumulates Ollama tokens into natural complete sentences before dispatch to TTS.
"""

import re

# Known common abbreviations (case-insensitive) that do not end a sentence
KNOWN_ABBREVIATIONS = {
    "e.g", "i.e", "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs",
    "etc", "approx", "no", "jan", "feb", "mar", "apr", "jun", "jul", "aug",
    "sept", "sep", "oct", "nov", "dec", "sq", "ft", "ltd", "inc", "co", "corp",
    "min", "sec", "hr", "hrs", "temp", "vol", "qty", "info", "config", "err", "msg"
}

# Match terminators: '...', '?!', '!?', '.', '?', '!', '।', '॥'
# Optionally followed by closing quotes or brackets: ", ', ), ], }, ”, ’
_TERMINATOR_PATTERN = re.compile(
    r'(\.\.\.|\?\!|\!\?|[\.\?\!\।\॥])(["\'\)\]\}\”\’]*)'
)

class StreamingSentenceBuffer:
    """
    Buffers streaming token chunks from LLM and yields complete natural sentences.
    Ensures partial phrases, commas, and arbitrary length bounds never trigger premature TTS dispatch.
    """

    def __init__(self):
        self._buffer = ""
        self._sentence_counter = 0

    def append(self, token: str, request_id: str = "") -> list[str]:
        """
        Appends a token chunk to the internal buffer and extracts any complete sentences.
        """
        if not token:
            return []

        self._buffer += token
        if request_id:
            print(f"[SENTENCE_BUFFER_APPEND] request_id={request_id} chars={len(token)}", flush=True)

        return self._extract_sentences(request_id=request_id)

    def _is_abbreviation_or_number(self, text_before_punct: str, punct: str, text_after_punct: str) -> bool:
        """
        Checks if a period '.' is part of an abbreviation or decimal number rather than a sentence end.
        """
        if not punct.startswith("."):
            return False

        # Decimal number check: e.g. "3.14" -> preceding char digit, following char digit
        if text_before_punct and text_after_punct:
            if text_before_punct[-1].isdigit() and text_after_punct[0].isdigit():
                return True

        # Extract last word before dot
        match = re.search(r'([a-zA-Z0-9]+)$', text_before_punct)
        if not match:
            return False

        word = match.group(1).lower()

        # Check known abbreviations
        if word in KNOWN_ABBREVIATIONS:
            return True

        # Single letter abbreviation (e.g., "U.S.", "A.", "B.")
        if len(word) == 1 and word.isalpha():
            return True

        return False

    def _extract_sentences(self, request_id: str = "") -> list[str]:
        """
        Scans the buffer for complete sentence boundaries.
        Returns a list of extracted complete sentence strings.
        """
        extracted = []
        pos = 0

        while True:
            match = _TERMINATOR_PATTERN.search(self._buffer, pos=pos)
            if not match:
                break

            term_start = match.start()
            term_end = match.end()
            punct = match.group(1)

            text_after = self._buffer[term_end:]

            # If nothing after terminator yet, wait for next token (stream active)
            if not text_after:
                break

            # Check if followed by whitespace
            first_char_after = text_after[0]
            if not first_char_after.isspace():
                pos = term_end
                continue

            # Check abbreviation / decimal number protection
            text_before = self._buffer[:term_start]
            if self._is_abbreviation_or_number(text_before, punct, text_after):
                pos = term_end
                continue

            # Valid sentence boundary!
            sentence = self._buffer[:term_end].strip()
            self._buffer = self._buffer[term_end:].lstrip()
            pos = 0

            if sentence:
                self._sentence_counter += 1
                if request_id:
                    print(
                        f"[SENTENCE_BOUNDARY_DETECTED] request_id={request_id} "
                        f"sentence_id={self._sentence_counter} text=\"{sentence}\"",
                        flush=True
                    )
                extracted.append(sentence)

        return extracted

    def flush_remaining(self, request_id: str = "") -> list[str]:
        """
        Flushes any remaining text in buffer at stream end as the final chunk.
        """
        remaining = self._buffer.strip()
        self._buffer = ""

        if not remaining:
            return []

        if request_id:
            print(f"[STREAM_FINAL_BUFFER] request_id={request_id} text=\"{remaining}\"", flush=True)

        self._sentence_counter += 1
        if request_id:
            print(
                f"[SENTENCE_BOUNDARY_DETECTED] request_id={request_id} "
                f"sentence_id={self._sentence_counter} text=\"{remaining}\"",
                flush=True
            )

        return [remaining]
