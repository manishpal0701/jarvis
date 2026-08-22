import re

class PauseEngine:
    # Base pause durations in milliseconds
    BASE_PAUSES = {
        "comma": 250,
        "sentence": 500,
        "ellipsis": 800,
    }

    # Emotion-based pause multipliers
    EMOTION_MULTIPLIERS = {
        "excited": 0.6,
        "happy": 0.8,
        "funny": 0.9,
        "calm": 1.3,
        "serious": 1.5,
        "warning": 1.2,
        "thinking": 1.6,
        "sad": 1.5,
        "professional": 1.0,
        "friendly": 1.0,
        "confident": 0.9,
    }

    @classmethod
    def get_pause_duration(cls, pause_type: str, emotion: str) -> int:
        """Calculates the pause duration in milliseconds based on type and emotion."""
        base = cls.BASE_PAUSES.get(pause_type, 300)
        multiplier = cls.EMOTION_MULTIPLIERS.get(emotion, 1.0)
        return int(base * multiplier)

    @classmethod
    def insert_pauses_ssml(cls, text: str, emotion: str) -> str:
        """Analyzes text and inserts SSML break tags for natural pauses."""
        if not text:
            return ""
            
        # 1. Handle ellipsis (...) first
        def replace_ellipsis(match):
            duration = cls.get_pause_duration("ellipsis", emotion)
            return f'<break time="{duration}ms"/>'
            
        processed = re.sub(r'\.\.\.', replace_ellipsis, text)
        
        # 2. Handle sentence endings (. ! ?)
        def replace_sentence(match):
            punctuation = match.group(1)
            duration = cls.get_pause_duration("sentence", emotion)
            return f'{punctuation}<break time="{duration}ms"/>'
            
        processed = re.sub(r'([\.!\?])\s*', replace_sentence, processed)
        
        # 3. Handle commas (,)
        def replace_comma(match):
            duration = cls.get_pause_duration("comma", emotion)
            return f',<break time="{duration}ms"/>'
            
        processed = re.sub(r',\s*', replace_comma, processed)
        
        return processed
