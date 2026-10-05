import re

class IntentAnalyzer:
    """
    Analyzes user utterances to classify intent, ambiguity, requirement for clarification,
    and necessity of follow-up questions.
    """
    
    AMBIGUOUS_PATTERNS = [
        r"^make\s+this\s+better\b",
        r"^fix\s+this\b",
        r"^do\s+it\b",
        r"^improve\s+this\b",
        r"^check\s+this\b",
        r"^change\s+it\b",
        r"^what\s+do\s+you\s+think\?$"
    ]

    HOSTING_PATTERNS = [
        r"\b(isko|is\s+website\s+ko|this\s+website|project)\s+(host|deploy)\b",
        r"\b(host|deploy)\s+(this|the)\s+(website|app|project)\b",
        r"\b(website|app)\s+(permanently\s+deploy|permanently\s+host|live\s+kar\s+do|live\s+krdo)\b",
        r"\bhost\s+(karo|krdo|kar\s+do)\b"
    ]

    VAGUE_BUILDING_PATTERNS = [
        r"\bi\s+(want|would\s+like)\s+to\s+(build|create|make|develop)\s+an?\s+(app|website|system|project|tool)\b",
        r"\bi\s+need\s+an?\s+(app|website|system|tool)\b",
        r"\bplanning\s+to\s+(build|make)\s+something\b",
        r"\bmujhe\s+ek\s+(app|website|system|project)\s+(banana|banaani|banana\s+hai)\b"
    ]

    OPINION_PATTERNS = [
        r"\bwhat\s+do\s+you\s+think\b",
        r"\bwhat\s+is\s+your\s+opinion\b",
        r"\bhow\s+does\s+this\s+look\b",
        r"\bis\s+this\s+architecture\s+good\b",
        r"\bdo\s+you\s+like\b",
        r"\bmessy\s+lag\s+raha\s+hai\b",
        r"\bkaisa\s+lag\s+raha\s+hai\b",
        r"\bkya\s+lagta\s+hai\b"
    ]

    EMOTIONAL_PATTERNS = [
        r"\b(frustrated|annoyed|stuck|angry|upset|hate|sucks|broken|baar\s+baar|error|issue)\b",
        r"\b(finally\s+fixed|fixed\s+it|yay|awesome|super\s+happy|worked|success|complete\s+ho\s+gaya)\b",
        r"\b(sad|depressed|down|tired|exhausted|mood\s+off|thak\s+gaya)\b"
    ]

    CASUAL_PATTERNS = [
        r"^(hi|hello|hey|greetings|good\s+morning|good\s+evening|what'?s\s+up|howdy)\b",
        r"^how\s+are\s+you\b",
        r"\b(bhai|tu|kya\s+kar\s+raha|kya\s+chala\s+raha|what\s+are\s+you\s+doing)\b"
    ]

    SUGGESTION_PATTERNS = [
        r"\b(suggest|recommend|ideas|best\s+way|options|alternatives|what\s+should\s+i|kya\s+karna\s+chahiye|what\s+features)\b",
        r"\bhow\s+can\s+i\s+improve\b",
        r"\b(what|which)\s+(features|options|technologies|tools|stack|approach)\b"
    ]


    def analyze(self, user_input: str, last_response_type: str = None) -> dict:
        """
        Analyzes user input string and returns intent classification details.
        """
        if not user_input or not user_input.strip():
            return {
                "intent": "empty",
                "requires_clarification": False,
                "requires_follow_up": False,
                "requires_suggestion": False,
                "confidence": 1.0
            }

        text = user_input.strip().lower()
        
        # 0. Hosting Request Check
        for pat in self.HOSTING_PATTERNS:
            if re.search(pat, text):
                return {
                    "intent": "website_host",
                    "requires_clarification": False,
                    "requires_follow_up": False,
                    "requires_suggestion": False,
                    "confidence": 0.98
                }

        # 1. Ambiguous Request Check
        for pat in self.AMBIGUOUS_PATTERNS:
            if re.search(pat, text):
                return {
                    "intent": "ambiguous_request",
                    "requires_clarification": True,
                    "requires_follow_up": False,
                    "requires_suggestion": False,
                    "confidence": 0.95
                }

        # 2. Vague High-Level Goal / Building Request Check
        for pat in self.VAGUE_BUILDING_PATTERNS:
            if re.search(pat, text):
                return {
                    "intent": "vague_building_request",
                    "requires_clarification": False,
                    "requires_follow_up": True,
                    "requires_suggestion": True,
                    "confidence": 0.95
                }

        # 3. Opinion Request Check
        for pat in self.OPINION_PATTERNS:
            if re.search(pat, text):
                return {
                    "intent": "opinion_request",
                    "requires_clarification": False,
                    "requires_follow_up": False,
                    "requires_suggestion": True,
                    "confidence": 0.90
                }

        # 4. Emotional Expression Check
        for pat in self.EMOTIONAL_PATTERNS:
            if re.search(pat, text):
                return {
                    "intent": "emotional_expression",
                    "requires_clarification": False,
                    "requires_follow_up": False,
                    "requires_suggestion": False,
                    "confidence": 0.90
                }

        # 5. Suggestion Seeking Request
        for pat in self.SUGGESTION_PATTERNS:
            if re.search(pat, text):
                return {
                    "intent": "suggestion_request",
                    "requires_clarification": False,
                    "requires_follow_up": True,
                    "requires_suggestion": True,
                    "confidence": 0.88
                }

        # 6. Casual Greeting / Chat
        for pat in self.CASUAL_PATTERNS:
            if re.search(pat, text):
                return {
                    "intent": "casual_chat",
                    "requires_clarification": False,
                    "requires_follow_up": False,
                    "requires_suggestion": False,
                    "confidence": 0.95
                }

        # 7. Standard Factual Question
        if "?" in user_input or text.startswith(("what", "how", "why", "where", "who", "when", "can you", "could you", "can i", "is it", "explain")):
            return {
                "intent": "question_factual",
                "requires_clarification": False,
                "requires_follow_up": False,
                "requires_suggestion": False,
                "confidence": 0.85
            }

        # 8. Default Task / Statement Intent
        return {
            "intent": "statement_task",
            "requires_clarification": False,
            "requires_follow_up": False,
            "requires_suggestion": False,
            "confidence": 0.75
        }
