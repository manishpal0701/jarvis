import re

class LanguageAnalyzer:
    """
    Analyzes user input to detect conversational language style:
    - Hinglish (Roman Hindi + English mix)
    - English (Standard English)
    - Hindi (Devanagari or formal Hindi)

    Provides guidelines for prompt assembly so Jarvis matches the user's natural language.
    """

    HINGLISH_KEYWORDS = [
        r"\b(bata|batao|kaise|kya|hai|haan|nahin|nahi|raha|rahi|rahe|rha|rhi|rhe|aaj|kal|yaar|bhai|bhookh|khana|khaun|lag|thak|gaya|hoon|mat|kar|karo|bana|banau|chalo|dekhte|hains|cheezein|zarurat|suno|karni|lagta|kaisa|sun|mera|meri|mere|bhi|toh|kuch)\b"
    ]

    DEVANAGARI_PATTERN = r"[\u0900-\u097F]"

    def analyze(self, user_input: str) -> dict:
        if not user_input or not user_input.strip():
            return {"language": "english", "style": "natural", "confidence": 1.0}

        text = user_input.strip()
        text_lower = text.lower()

        # 1. Check Devanagari script
        if re.search(self.DEVANAGARI_PATTERN, text):
            return {
                "language": "hindi",
                "style": "spoken_hindi",
                "confidence": 0.95,
                "instruction": "Respond in natural spoken Hindi. Use common daily Hindi words, NOT overly formal Sanskritized Hindi terms."
            }

        # 2. Check Hinglish patterns
        hinglish_hits = 0
        for pat in self.HINGLISH_KEYWORDS:
            matches = re.findall(pat, text_lower)
            hinglish_hits += len(matches)

        if hinglish_hits > 0 or any(w in text_lower for w in ["bhookh", "khana", "khaun", "maggi", "yaar", "kaise", "bana", "chalta", "chal", "kaam", "kya"]):
            return {
                "language": "hinglish",
                "style": "conversational_hinglish",
                "confidence": 0.90,
                "instruction": (
                    "Respond naturally in casual, conversational Hinglish matching the user's tone like a smart young personal assistant. "
                    "Use natural spoken words like 'cheezein', 'steps', 'zarurat', 'batao', 'dekhte hain', 'theek hai', 'chalo', 'try karo', 'bhookh', 'khaana', 'packet'. "
                    "STRICTLY AVOID unnatural formal Hindi words like 'saamagri', 'nirdesh', 'upayukt', 'avashyakta', 'prastut', 'umeed hai', 'vikalp', 'sevan', 'parosein', 'samiksha', 'kripya', 'tadanusar', 'bhojan', 'nimnalikhit'."
                )
            }

        # 3. Default to English
        return {
            "language": "english",
            "style": "conversational_english",
            "confidence": 0.85,
            "instruction": "Respond in clean, natural, friendly conversational English."
        }

