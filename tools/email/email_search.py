"""
tools/email/email_search.py
Natural Language to Gmail Query Translator for JARVIS Email Agent.
"""

import re
from typing import Tuple

class EmailSearchQueryTranslator:
    @staticmethod
    def translate_nl_request(nl_query: str) -> Tuple[str, int]:
        q_lower = nl_query.lower().strip()
        max_results = 5

        count_match = re.search(r"\b(?:last|top|recent)\s+(\d+)\s+emails?", q_lower)
        if count_match:
            max_results = int(count_match.group(1))

        query_parts = []

        if any(w in q_lower for w in ["unread", "nayi mail", "new email", "bin padhi"]):
            query_parts.append("is:unread")

        if any(w in q_lower for w in ["important", "khas", "starred", "priority"]):
            query_parts.append("is:important")

        if any(w in q_lower for w in ["aaj", "today"]):
            query_parts.append("newer_than:1d")
        elif any(w in q_lower for w in ["yesterday", "kal"]):
            query_parts.append("newer_than:2d")

        from_match = re.search(r"\b([a-zA-Z0-9_\-\.]+)\s+ka\s+(?:[a-zA-Z0-9_\-\.]+\s+)*email", q_lower)
        if not from_match:
            from_match = re.search(r"\bfrom\s+([a-zA-Z0-9_\-\.]+)", q_lower)

        if from_match:
            sender_name = from_match.group(1).strip()
            if sender_name not in ["last", "first", "nayi", "unread", "important"]:
                query_parts.append(f"from:{sender_name}")

        if not query_parts:
            cleaned = re.sub(r"(?i)^(?:jarvis,?\s*)?(?:show|search|fetch|dikhao|batao|find|check)\s*(?:my|me)?\s*", "", q_lower).strip()
            cleaned = re.sub(r"(?i)\s*(?:emails?|mails?|search karo|dikhao|batao)\s*$", "", cleaned).strip()
            if cleaned:
                query_parts.append(cleaned)

        final_query = " ".join(query_parts) if query_parts else "category:primary"
        return final_query, max_results
