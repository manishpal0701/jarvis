import re

SECRET_PATTERNS = [
    r"(?i)\bpasswords?\b",
    r"(?i)\bapi[_\s]?keys?\b",
    r"(?i)\bsecret[_\s]?keys?\b",
    r"(?i)\bbearer\s+[a-zA-Z0-9_\-\.]{10,}",
    r"(?i)\btoken\b\s*(?:[:=]|is)?\s*[a-zA-Z0-9_\-\.]{10,}",
    r"(?i)\baws[_\s]?secret\b",
    r"(?i)\bprivate[_\s]?key\b",
]

ALLOWED_TYPES = {"working", "episodic", "semantic", "user", "project", "task"}

class MemoryPolicy:
    """
    Policy engine for determining whether information should be remembered,
    filtering sensitive secrets/credentials, preventing duplicate storage,
    and evaluating memory importance.
    """
    def __init__(self, secret_patterns: list[str] = None):
        self.secret_patterns = secret_patterns or SECRET_PATTERNS

    def contains_secret(self, text: str) -> bool:
        """Returns True if the content appears to contain sensitive credentials/secrets."""
        if not text or not isinstance(text, str):
            return False
        for pattern in self.secret_patterns:
            if re.search(pattern, text):
                return True
        return False

    def evaluate_importance(self, content: str, memory_type: str, user_importance: float = None) -> float:
        """Calculates or normalizes the importance score (0.0 to 1.0)."""
        if user_importance is not None:
            return max(0.0, min(1.0, float(user_importance)))
        
        type_defaults = {
            "user": 0.9,
            "project": 0.8,
            "semantic": 0.7,
            "task": 0.7,
            "episodic": 0.5,
            "working": 0.3,
        }
        base = type_defaults.get(memory_type, 0.5)

        content_lower = content.lower() if content else ""
        if any(w in content_lower for w in ["critical", "important", "always", "never", "must", "rule"]):
            base = min(1.0, base + 0.2)
        elif any(w in content_lower for w in ["minor", "temp", "maybe"]):
            base = max(0.1, base - 0.2)

        return round(base, 2)

    def should_remember(self, content: str, memory_type: str = "semantic", existing_records: list[dict] = None) -> tuple[bool, str]:
        """
        Evaluates whether a piece of content should be saved into long-term memory.
        Returns (should_store: bool, reason: str).
        """
        if not content or not isinstance(content, str) or not content.strip():
            print("\n[MEMORY POLICY]")
            print("Decision: REJECT (Content is empty)")
            return False, "Content is empty."

        if memory_type not in ALLOWED_TYPES:
            print("\n[MEMORY POLICY]")
            print(f"Decision: REJECT (Invalid memory type '{memory_type}')")
            return False, f"Invalid memory type '{memory_type}'. Must be one of {ALLOWED_TYPES}."

        # Privacy & Secret check
        if self.contains_secret(content):
            print("\n[MEMORY POLICY]")
            print("Decision: REJECT (Contains sensitive credentials/secrets)")
            return False, "Privacy violation: Content contains sensitive credentials/secrets."

        # Deduplication check against existing records of the same type
        if existing_records:
            cleaned_target = content.strip().lower()
            for rec in existing_records:
                if rec.get("type") == memory_type:
                    rec_content = rec.get("content", "").strip().lower()
                    if rec_content == cleaned_target:
                        print("\n[MEMORY POLICY]")
                        print("Decision: REJECT (Duplicate content already exists)")
                        return False, "Duplicate content already exists in memory."

        print("\n[MEMORY POLICY]")
        print("Decision: STORE")
        return True, "Passed memory policy evaluation."
