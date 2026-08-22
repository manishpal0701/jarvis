import re
from typing import Dict, Any, Tuple

class EmotionEngine:
    # Emotion parameters: (rate, pitch, volume)
    # rate: edge-tts format (e.g. +10%, -5%)
    # pitch: edge-tts format (e.g. +5Hz, -3Hz)
    # volume: edge-tts format (e.g. +0%, -10%)
    EMOTION_PARAMS = {
        "happy": ("+5%", "+3Hz", "+0%"),
        "funny": ("+10%", "+5Hz", "+0%"),
        "excited": ("+15%", "+8Hz", "+5%"),
        "calm": ("-5%", "-2Hz", "-5%"),
        "serious": ("-10%", "-4Hz", "+0%"),
        "warning": ("-5%", "+2Hz", "+10%"),
        "motivational": ("+5%", "+3Hz", "+5%"),
        "celebration": ("+12%", "+6Hz", "+8%"),
        "thinking": ("-15%", "-3Hz", "-5%"),
        "friendly": ("+0%", "+2Hz", "+0%"),
        "professional": ("+0%", "+0Hz", "+0%"),
        "confident": ("+2%", "+1Hz", "+5%"),
        "sad": ("-15%", "-5Hz", "-10%"),
    }

    # Keyword mappings for classification
    EMOTION_KEYWORDS = {
        "excited": [r"\bawesome\b", r"\bgreat\b", r"\bwonderful\b", r"\bamazing\b", r"\bincredible\b", r"\bexcited\b", r"\bwow\b", r"\bcomplete\b", r"\bcompleted\b"],
        "happy": [r"\bhappy\b", r"\bglad\b", r"\bgood\b", r"\bnice\b", r"\bpleasure\b", r"\bjoy\b", r"\bkhushi\b", r"\bwelcome\b"],
        "funny": [r"\bjoke\b", r"\bfunny\b", r"\bhaha\b", r"\bhehe\b", r"\blol\b"],
        "warning": [r"\bwarning\b", r"\bdanger\b", r"\brisk\b", r"\bcritical\b", r"\bfailed\b", r"\berror\b", r"\balert\b", r"\bcareful\b"],
        "serious": [r"\bserious\b", r"\bimportant\b", r"\burgent\b", r"\battention\b", r"\bsecurity\b", r"\bverify\b", r"\bpassword\b"],
        "motivational": [r"\bmotivate\b", r"\binspire\b", r"\bsuccess\b", r"\bachieve\b", r"\bwin\b", r"\bfocus\b", r"\bkeep going\b"],
        "celebration": [r"\bcongratulations\b", r"\bcongrats\b", r"\bcelebrate\b", r"\bhooray\b", r"\bhurrah\b"],
        "thinking": [r"\bhmm\b", r"\bthinking\b", r"\banalyze\b", r"\bsearching\b", r"\bscanning\b", r"\bone second\b", r"\bek second\b"],
        "sad": [r"\bsad\b", r"\bsorry\b", r"\bapologize\b", r"\bunfortunately\b", r"\bbad\b", r"\bunhappy\b"],
        "confident": [r"\bsure\b", r"\bconfident\b", r"\bdefinitely\b", r"\babsolutely\b", r"\bcertainly\b"],
        "calm": [r"\bcalm\b", r"\brelax\b", r"\bpeace\b", r"\bsleep\b", r"\bquiet\b"],
        "friendly": [r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bfriend\b", r"\bhow are you\b"],
    }

    @classmethod
    def classify(cls, text: str) -> str:
        """Classifies the emotion of the text based on keyword matching."""
        text_lower = text.lower()
        
        # Check each emotion's keywords
        for emotion, patterns in cls.EMOTION_KEYWORDS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return emotion
                    
        return "professional"  # Default emotion

    @classmethod
    def get_params(cls, emotion: str) -> Tuple[str, str, str]:
        """Returns (rate, pitch, volume) for the given emotion."""
        return cls.EMOTION_PARAMS.get(emotion, cls.EMOTION_PARAMS["professional"])
