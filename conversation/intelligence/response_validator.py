import re

class ResponseValidator:
    """
    Lightweight post-generation validation and sanitation layer.
    Ensures LLM output is formatted strictly for natural spoken TTS delivery.
    """

    SYSTEM_STATE_PATTERNS = [
        r"\bwaiting\s+for\s+next\s+command(?:\.\.\.|\.)?\b",
        r"\bthinking(?:\.\.\.|\.)?\b",
        r"\blistening(?:\.\.\.|\.)?\b",
        r"\bspeaking(?:\.\.\.|\.)?\b",
        r"\bactive_session\b",
        r"\bwake_mode\b",
        r"\bprocessing(?:\.\.\.|\.)?\b"
    ]

    PREFIX_PATTERNS = [
        r"^(?:Jarvis|Assistant|AI|Response|System)\s*:\s*"
    ]

    def validate_and_clean(self, text: str) -> str:
        """
        Cleans and sanitizes response text for TTS and history logging.
        Returns a clean spoken text string.
        """
        if not text:
            return ""

        cleaned = text.strip()

        # 1. Remove speaker/role prefixes
        for pat in self.PREFIX_PATTERNS:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

        # 2. Remove leaked internal system state phrases
        for sys_pat in self.SYSTEM_STATE_PATTERNS:
            cleaned = re.sub(sys_pat, "", cleaned, flags=re.IGNORECASE)

        # 3. Remove markdown headers (e.g. ### Header -> Header)
        cleaned = re.sub(r"^\s*#{1,6}\s*", "", cleaned, flags=re.MULTILINE)

        # 4. Remove markdown bold/italics formatting
        cleaned = re.sub(r"\*{1,2}(.*?)\*{1,2}", r"\1", cleaned)
        cleaned = re.sub(r"_{1,2}(.*?)_{1,2}", r"\1", cleaned)

        # 5. Remove list markers at start of lines (e.g., "1. ", "2. ", "- ", "* ", "• ")
        cleaned = re.sub(r"^\s*(?:\d+[\.\)]|[-*•])\s+", "", cleaned, flags=re.MULTILINE)

        # 6. Strip JSON code blocks
        cleaned = re.sub(r"```(?:json|python)?[\s\S]*?```", "", cleaned)

        # 7. Normalize spaces and line breaks
        cleaned = re.sub(r"\n+", " ", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned)

        return cleaned.strip()
