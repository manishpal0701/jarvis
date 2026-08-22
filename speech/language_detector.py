import re

# Common Hindi words written in Roman script to detect Hinglish/Roman Hindi
ROMAN_HINDI_KEYWORDS = {
    "hai", "haan", "na", "ho", "gaya", "gayi", "gaye", "kar", "raha", "rahi", "rahe",
    "hu", "hoon", "ek", "se", "ko", "ki", "ka", "ke", "me", "mein", "bhi", "toh", "to",
    "aur", "kya", "kyun", "kyu", "kab", "kahan", "kaha", "kaise", "kon", "kaun", "yeh",
    "ye", "wo", "woh", "tha", "thi", "the", "par", "pe", "se", "ne", "ko", "hi", "he",
    "achha", "acha", "thik", "theek", "kuch", "kuchh", "ab", "tab", "jab", "sab", "hum",
    "tum", "aap", "mera", "meri", "mere", "apna", "apni", "apne", "karna", "karne",
    "karunga", "karungi", "karta", "karti", "karte", "diya", "liya", "kiya", "chahiye",
    "hoga", "hogi", "hoge", "rha", "rhi", "rhe", "kr", "kya", "bhai", "yaar", "boss"
}

class LanguageDetector:
    @staticmethod
    def is_devanagari(text: str) -> bool:
        """Checks if the text contains Devanagari characters."""
        return bool(re.search(r'[\u0900-\u097F]', text))

    @staticmethod
    def detect(text: str) -> str:
        """Detects the language of the text.
        Returns 'hi-IN' (Devanagari Hindi), 'hinglish' (Roman Hindi/Hinglish), or 'en-US' (English).
        """
        if LanguageDetector.is_devanagari(text):
            return "hi-IN"
            
        # Tokenize and check for Roman Hindi keywords
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        if not words:
            return "en-US"
            
        hindi_word_count = sum(1 for w in words if w in ROMAN_HINDI_KEYWORDS)
        ratio = hindi_word_count / len(words)
        
        # If more than 15% of the words are Roman Hindi keywords, classify as Hinglish
        if ratio > 0.15:
            return "hinglish"
            
        return "en-US"
