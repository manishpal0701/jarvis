from typing import Optional
from speech.config import VOICE_PERSONALITY, DEFAULT_LANGUAGE
from speech.voices import VOICES, PERSONALITY_VOICES
from speech.logger import get_logger

logger = get_logger("VoiceManager")

class VoiceManager:
    def __init__(self):
        self.personality = VOICE_PERSONALITY
        self.default_lang = DEFAULT_LANGUAGE

    def set_personality(self, personality: str) -> None:
        """Sets the active voice personality."""
        if personality in PERSONALITY_VOICES:
            self.personality = personality
            logger.info(f"Voice personality set to: {personality}")
        else:
            logger.warning(f"Unknown personality: {personality}. Using default.")

    def get_voice(self, language: str, gender: str = "female") -> str:
        """Gets the voice ID for the given language and gender based on personality."""
        # Normalize language code (e.g. en-US, hi-IN, hinglish)
        lang_code = language
        if language == "hinglish":
            lang_code = "en-IN"  # Hinglish uses Indian English neural voice for natural Roman Hinglish text delivery
            
        # Try to find voice by personality first
        if self.personality in PERSONALITY_VOICES:
            p_voices = PERSONALITY_VOICES[self.personality]
            if lang_code in p_voices:
                return p_voices[lang_code]
                
        # Fallback to default voices mapping
        if lang_code in VOICES:
            gender_voices = VOICES[lang_code]
            if gender in gender_voices:
                return gender_voices[gender]
                
        # Ultimate fallback
        logger.warning(f"Voice not found for lang={language}, gender={gender}. Falling back to default en-IN female voice.")
        return VOICES["en-IN"]["female"]
