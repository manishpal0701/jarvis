import re

STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "you", "your", "he", "she", "it", "they",
    "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while",
    "of", "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "down", "in",
    "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "can", "will", "just", "dont", "should", "now", "boss", "jarvis"
}

class ContextTracker:
    """
    Tracks topic evolution, identifies current conversational topic,
    and detects topic continuation versus topic shifts across turns.
    """
    
    def extract_topic(self, user_input: str) -> str | None:
        """Extracts the dominant subject/topic keyword phrase from user input."""
        if not user_input or not user_input.strip():
            return None

        text = user_input.strip().lower()
        
        # Domain specific overrides
        if re.search(r"\b(hi|hello|hey|greetings|good\s+morning|good\s+evening|how\s+are\s+you)\b", text):
            return "casual greeting"
        if "app" in text or "application" in text:
            return "app development"
        if "architecture" in text or "design" in text:
            return "system architecture"
        if "code" in text or "bug" in text or "fixed" in text or "error" in text:
            return "code debugging"
        if "france" in text or "capital" in text or "paris" in text:
            return "geography & world capitals"
        if "project" in text or "jarvis" in text:
            return "jarvis project"

        # Extract non-stopword Nouns/Keywords
        words = [w for w in re.findall(r"\b[a-z]{3,}\b", text) if w not in STOPWORDS]
        if words:
            return " ".join(words[:2])
        return "general conversation"

    def analyze_topic_flow(self, user_input: str, current_topic: str = None) -> dict:
        """
        Analyzes whether the user is continuing the existing topic or shifting to a new topic.
        """
        new_topic = self.extract_topic(user_input)

        if not current_topic:
            return {
                "topic": new_topic or "general conversation",
                "topic_changed": False,
                "continuation": False
            }

        # Check for topic continuation signals using strict word boundaries
        text_lower = user_input.lower()
        continuation_patterns = [
            r"\b(it|this|that|the project|the code|what about it|tell me more)\b"
        ]
        
        is_continuation = any(re.search(pat, text_lower) for pat in continuation_patterns)
        
        if is_continuation:
            return {
                "topic": current_topic,
                "topic_changed": False,
                "continuation": True
            }

        # Check if new extracted topic matches current topic
        if new_topic and new_topic != current_topic and new_topic != "general conversation":
            return {
                "topic": new_topic,
                "topic_changed": True,
                "continuation": False
            }

        return {
            "topic": current_topic,
            "topic_changed": False,
            "continuation": True
        }
