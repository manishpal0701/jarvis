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

    EMOJI_PATTERN = re.compile(
        r'[\U00010000-\U0010ffff]'  # All Emojis / Pictographs in Supplementary Planes
        r'|[\u2600-\u27BF]'          # Misc Symbols & Dingbats
        r'|[\u2300-\u23FF]'          # Technical symbols
        r'|[\u2B00-\u2BFF]'          # Arrows & misc symbols
        r'|[\u200D\uFE0F\uFE0E]'     # ZWJ & Variation Selectors
        r'|[\uD800-\uDBFF][\uDC00-\uDFFF]' # Surrogate pairs
    )

    def strip_emojis_for_tts(self, text: str) -> str:
        """
        Removes all emojis, variation selectors, skin tone modifiers, and decorative
        pictographs strictly for TTS speech input so emoji names are never spoken.
        """
        if not text:
            return ""
        no_emoji = self.EMOJI_PATTERN.sub("", text)
        return re.sub(r"\s{2,}", " ", no_emoji).strip()

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

        # 7. Strip Emojis strictly for TTS delivery
        cleaned = self.strip_emojis_for_tts(cleaned)

        # 8. Normalize spaces and line breaks
        cleaned = re.sub(r"\n+", " ", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned)

        # 9. Strip unauthorized trailing filler check questions (e.g. "Theek hai?", "theek hai?")
        cleaned = re.sub(r"\s+(?:theek\s+hai|samjhe|samajh\s+gaye)\s*[\?\.]?$", "", cleaned, flags=re.IGNORECASE)

        return cleaned.strip()
