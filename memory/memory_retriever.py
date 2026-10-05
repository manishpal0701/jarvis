"""
memory/memory_retriever.py
Retrieval & Ranking Engine for searching and fetching relevant memories.
Scores memories using keyword overlap, tag matching, importance score, and recency.
Applies a strict relevance threshold to prevent injecting unrelated memories.
"""
import re
from memory.memory_store import MemoryStore

COMMON_STOPWORDS = {
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
    "kaise", "kya", "hai", "ko", "se", "mein", "par", "batao", "do", "na", "rahi"
}

class MemoryRetriever:
    """
    Retrieval & Ranking Engine for searching and fetching relevant memories.
    Scores memories using keyword overlap, tag matching, importance score, and recency.
    """
    def __init__(self, store: MemoryStore):
        self.store = store

    def score_record(self, record: dict, query_terms: list[str]) -> float:
        """Calculates relevance score for a record against query terms."""
        content = record.get("content", "").lower()
        tags = [t.lower() for t in record.get("tags", [])]
        importance = record.get("importance", 0.5)

        if not query_terms:
            return 0.0

        matches = 0
        for term in query_terms:
            if term in content:
                matches += 1.5
            if any(term == tag or term in tag for tag in tags):
                matches += 2.0

        if matches == 0:
            return 0.0

        score = (matches * 0.6) + (importance * 0.4)
        return round(score, 3)

    def retrieve_relevant(self, query: str, limit: int = 5, min_score: float = 1.0, memory_type: str = None) -> list[dict]:
        """
        Retrieves top relevant memories matching a natural language query.
        Filters out records scoring below min_score threshold to avoid injecting unrelated context.
        """
        print("\n[MEMORY RETRIEVER]")
        print(f"Query: {query}")

        all_records = self.store.get_all_records()
        if memory_type:
            all_records = [r for r in all_records if r.get("type") == memory_type]

        if not query or not query.strip():
            if memory_type:
                return all_records[:limit]
            print("Matches: None")
            return []

        query_terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) >= 2 and t not in COMMON_STOPWORDS]
        if not query_terms:
            print("Matches: None")
            return []

        scored = []
        for rec in all_records:
            score = self.score_record(rec, query_terms)
            if score >= min_score:
                scored.append((score, rec))

        scored.sort(key=lambda x: (x[0], x[1].get("importance", 0)), reverse=True)
        results = [item[1] for item in scored[:limit]]
        matches_str = ", ".join([r.get("content", "") for r in results]) if results else "None"
        print(f"Matches: {matches_str}")
        return results

    def retrieve_by_type(self, memory_type: str, limit: int = 20) -> list[dict]:
        """Retrieves memories filtered strictly by category type."""
        records = self.store.query_records(lambda r: r.get("type") == memory_type)
        records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return records[:limit]

    def retrieve_project(self, project_name: str) -> list[dict]:
        """Retrieves memories associated with a specific project name."""
        if not project_name:
            return []
        p_lower = project_name.lower()
        records = self.store.query_records(
            lambda r: r.get("type") == "project" and (
                (r.get("project") and r.get("project").lower() == p_lower) or
                (r.get("metadata", {}).get("project_name", "").lower() == p_lower) or
                p_lower in r.get("content", "").lower()
            )
        )
        records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return records

    def retrieve_task(self, task_id: str) -> dict | None:
        """Retrieves task memory for a specific task ID."""
        if not task_id:
            return None
        records = self.store.query_records(
            lambda r: r.get("type") == "task" and r.get("task_id") == task_id
        )
        if records:
            records.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
            return records[0]
        return None

    def retrieve_user_memory(self) -> list[dict]:
        """Retrieves all user preference and user-related memories."""
        return self.retrieve_by_type("user", limit=50)

    def retrieve_recent_events(self, limit: int = 10) -> list[dict]:
        """Retrieves recent episodic event memories."""
        return self.retrieve_by_type("episodic", limit=limit)

    def search(self, query: str, memory_type: str = None) -> list[dict]:
        """Performs search with optional memory_type filter."""
        return self.retrieve_relevant(query, limit=20, memory_type=memory_type)
