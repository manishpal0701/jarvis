import re

class EmotionAnalyzer:
    """
    Analyzes sentiment, tone, and emotional cues in user input.
    Maps input to discrete emotional states (happy, excited, frustrated, sad, angry, neutral)
    along with confidence metrics.
    """
    
    EXCITED_PATTERNS = [
        (r"\b(finally\s+fixed|fixed\s+it|worked|we\s+did\s+it|woohoo|awesome|amazing|yay|nailed\s+it|chal\s+gaya|complete\s+ho\s+gaya|hogaya)\b", 0.95),
        (r"!{2,}", 0.80)
    ]

    HAPPY_PATTERNS = [
        (r"\b(happy|great|good|thank|thanks|love|cool|nice|pleased|glad|enjoy)\b", 0.85),
        (r"(:-\)|:\)|;\)|😊|😄|🎉|👍|🔥)", 0.90)
    ]

    FRUSTRATED_PATTERNS = [
        (r"\b(frustration|frustrated|annoyed|stuck|not\s+working|error|broken|bug|issue|headache|sucks|fail|failed|ugh|chal\s+nahi\s+raha|kaam\s+nahi\s+kar\s+raha)\b", 0.90),
        (r"\bwhy\s+(is|isn'?t)\s+this\s+(working|broken)\b", 0.85)
    ]

    SAD_PATTERNS = [
        (r"\b(sad|depressed|down|disappointed|upset|unhappy|tired|exhausted|hopeless|mood\s+off)\b", 0.90),
        (r"(:-\(|:\(|😢|😭|😞)", 0.90)
    ]

    ANGRY_PATTERNS = [
        (r"\b(angry|furious|mad|horrible|terrible|hate|stop\s+doing|useless)\b", 0.90),
        (r"\b(wtf|damn|crap|shit)\b", 0.85)
    ]

    def analyze(self, user_input: str) -> dict:
        """
        Analyzes user input text and returns detected emotional state and confidence.
        """
        if not user_input or not user_input.strip():
            return {"emotion": "neutral", "confidence": 1.0, "cues": []}

        text = user_input.strip().lower()
        cues = []

        # 1. Check Excited
        for pat, score in self.EXCITED_PATTERNS:
            if re.search(pat, text):
                cues.append("excited_cue")
                return {"emotion": "excited", "confidence": score, "cues": cues}

        # 2. Check Frustrated
        for pat, score in self.FRUSTRATED_PATTERNS:
            if re.search(pat, text):
                cues.append("frustrated_cue")
                return {"emotion": "frustrated", "confidence": score, "cues": cues}

        # 3. Check Sad
        for pat, score in self.SAD_PATTERNS:
            if re.search(pat, text):
                cues.append("sad_cue")
                return {"emotion": "sad", "confidence": score, "cues": cues}

        # 4. Check Angry
        for pat, score in self.ANGRY_PATTERNS:
            if re.search(pat, text):
                cues.append("angry_cue")
                return {"emotion": "angry", "confidence": score, "cues": cues}

        # 5. Check Happy
        for pat, score in self.HAPPY_PATTERNS:
            if re.search(pat, text):
                cues.append("happy_cue")
                return {"emotion": "happy", "confidence": score, "cues": cues}

        # Default Neutral
        return {"emotion": "neutral", "confidence": 0.90, "cues": ["neutral_baseline"]}
