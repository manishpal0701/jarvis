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
    "than", "too", "very", "can", "will", "just", "dont", "should", "now", "boss", "jarvis",
    "doing", "going", "saying", "talking", "showing", "telling", "asking", "making",
    "having", "getting", "looking", "working", "running", "seeing", "helping", "feeling",
    "thinking", "say", "said", "talk", "ask", "tell", "show", "look", "feel", "make",
    "give", "get", "go", "come", "help", "know", "think", "could", "would", "shall", "may", "might"
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
        if re.search(r"\b(hi|hello|hey|greetings|good\s+morning|good\s+evening|how\s+are\s+you|what\s+are\s+you\s+doing)\b", text):
            return "casual greeting"
        if "app" in text or "application" in text:
            return "app development"
        if "architecture" in text or "design" in text:
            return "system architecture"
        if "code" in text or "bug" in text or "fixed" in text or "error" in text:
            return "code debugging"
        if "france" in text or "capital" in text or "paris" in text:
            return "geography & world capitals"
        if "jarvis project" in text or "the project" in text or "this project" in text:
            return "jarvis project"

        # Extract non-stopword Nouns/Keywords
        words = [w for w in re.findall(r"\b[a-z]{3,}\b", text) if w not in STOPWORDS]
        if words:
            return " ".join(words[:2])
        return "general conversation"

    def extract_target_entity(self, user_input: str) -> str | None:
        """Extracts target app, project, tool, or subject entity from user input."""
        if not user_input or not user_input.strip():
            return None

        text = user_input.strip().lower()

        # Casual talk, greetings, compliments, and feelings must NOT create target entities
        casual_patterns = [
            r"\b(hi|hello|hey|greetings|good\s+morning|good\s+evening|good\s+night|how\s+are\s+you)\b",
            r"\b(sundar|beautiful|pretty|nice|awesome|cool|cute|lookin|looking)\b",
            r"\b(mood|off|sad|happy|lonely|funny|joke|thank|thanks|welcome)\b",
            r"\b(what\s+are\s+you\s+doing|what\s+can\s+you\s+do|what\s+do\s+you\s+do|feeling|tell\s+me)\b"
        ]
        if any(re.search(pat, text) for pat in casual_patterns):
            return None

        # Explicit app/project creation patterns
        app_patterns = [
            r"(?:bana\s*(?:do|banao)|create|build|make)\s+(?:an?\s+)?([a-zA-Z0-9_\-\s]+?\s+(?:app|website|system|tool|calculator|tracker|project|bot))",
            r"([a-zA-Z0-9_\-\s]+?\s+(?:app|website|system|tool|calculator|tracker))\s+(?:bana|banaa|create|build|make)",
            r"(?:bana\s+raha\s+hoon|working\s+on)\s+(?:an?\s+)?([a-zA-Z0-9_\-\s]+?\s+(?:app|website|system|tool|project))",
            r"(?:main\s+)?(?:ek\s+)?([a-zA-Z0-9_\-\s]+?\s+(?:app|website|system|tool|project))\s+(?:bana\s+raha\s+hoon|working\s+on)"
        ]

        for pat in app_patterns:
            m = re.search(pat, text)
            if m:
                entity = m.group(1).strip()
                # Clean filler words
                entity = re.sub(r"^(?:main\s+|ek\s+|a\s+|an\s+|the\s+|new\s+|my\s+)+", "", entity).strip()
                if len(entity) >= 3:
                    return entity

        # Keyword matching fallback
        if "expense tracker" in text:
            return "expense tracker app"
        if "calculator" in text:
            return "calculator"
        if "weather app" in text:
            return "weather app"
        if "website" in text:
            return "website project"

        topic = self.extract_topic(user_input)
        if topic and topic not in {"casual greeting", "general conversation", "jarvis project"}:
            return topic

        return None

    def resolve_followup_references(self, user_input: str, active_entity: str = None) -> dict:
        """
        Detects Hinglish/English follow-up pronouns ('isko', 'isme', 'usme', 'ye wala', etc.)
        and resolves them to the active context entity.
        """
        if not user_input or not user_input.strip():
            return {"has_followup": False, "pronoun": None, "active_entity": active_entity, "resolved_text": user_input}

        text = user_input.strip()
        text_lower = text.lower()

        # Follow-up pronoun patterns
        pronoun_patterns = [
            r"\b(isko|isme|usme|ye\s+wala|woh\s+wala|voh\s+wala|same\s+wala|pehle\s+wala|pehley\s+wala)\b",
            r"\b(ab\s+isko|isme\s+bhi|isko\s+bhi|is\s+me|us\s+me)\b",
            r"\b(in\s+this|for\s+this|to\s+this|in\s+it|add\s+to\s+this|this\s+one|that\s+one|previous\s+one)\b"
        ]

        matched_pronoun = None
        for pat in pronoun_patterns:
            m = re.search(pat, text_lower)
            if m:
                matched_pronoun = m.group(1)
                break

        if not matched_pronoun or not active_entity:
            return {
                "has_followup": bool(matched_pronoun),
                "pronoun": matched_pronoun,
                "active_entity": active_entity,
                "resolved_text": text
            }

        # Format resolved hint for LLM prompt context
        resolved_text = f"{text} (Note: '{matched_pronoun}' refers to the active context: '{active_entity}')"

        return {
            "has_followup": True,
            "pronoun": matched_pronoun,
            "active_entity": active_entity,
            "resolved_text": resolved_text
        }

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
            r"\b(it|this|that|the project|the code|what about it|tell me more|isko|isme|usme|ye wala|woh wala)\b"
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

