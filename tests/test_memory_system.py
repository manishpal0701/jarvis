import os
import sys
import unittest
import tempfile
import time
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from memory.memory_manager import MemoryManager, load_memory, save_memory
from memory.memory_store import MemoryStore
from memory.memory_policy import MemoryPolicy
from conversation.command_router import CommandRouter
from conversation.conversation_manager import ConversationManager

class TestMemorySystem(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.memory = MemoryManager(store_file=self.temp_file)
        self.memory._store_engine.clear_all()

    def tearDown(self):
        if os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except Exception:
                pass

    # --- 1. Basic CRUD: remember, recall, update, forget ---
    def test_01_basic_crud_operations(self):
        mem_id, msg = self.memory.remember("User prefers Flutter framework", category="user", key="preferred_framework", value="Flutter")
        self.assertIsNotNone(mem_id, "remember should return memory ID")

        recalls = self.memory.recall("Flutter")
        self.assertGreaterEqual(len(recalls), 1, "recall should find stored Flutter memory")
        self.assertIn("Flutter", recalls[0].get("content", ""))

        updated = self.memory.update(mem_id, content="User prefers Flutter for cross-platform apps")
        self.assertTrue(updated, "update should return True")

        deleted = self.memory.forget("preferred_framework")
        self.assertTrue(deleted, "forget should delete matching record")
        self.assertEqual(len(self.memory.recall("Flutter")), 0, "Flutter memory should be deleted")

    # --- 2. Explicit Memory Commands ---
    def test_02_explicit_memory_commands(self):
        router = CommandRouter()
        self.assertTrue(router.is_memory_command("Jarvis, remember that I prefer Flutter"))
        self.assertTrue(router.is_memory_command("Jarvis, forget that I prefer Flutter"))
        self.assertTrue(router.is_memory_command("What do you remember about my framework preference?"))
        self.assertTrue(router.is_memory_command("forget today's conversation"))

        with patch.object(router, '_speak') as mock_speak:
            router.handle_memory_command("Jarvis, remember that I prefer Flutter")
            mock_speak.assert_called_with("Memory stored successfully, Boss.")

        with patch.object(router, '_speak') as mock_speak:
            router.handle_memory_command("What framework do I prefer?")
            mock_speak.assert_called()
            output = mock_speak.call_args[0][0]
            self.assertIn("Flutter", output)

        with patch.object(router, '_speak') as mock_speak:
            router.handle_memory_command("Jarvis, forget that I prefer Flutter")
            mock_speak.assert_called_with("Matching memory removed, Boss.")

    # --- 3. Memory Retrieval & Scoring (<100ms) ---
    def test_03_relevance_retrieval_speed_and_threshold(self):
        self.memory.remember("User is learning AI Engineering", category="user", key="learning_goal", value="AI Engineering")
        self.memory.remember("User loves Italian pizza", category="user", key="favorite_food", value="Pizza")

        start = time.time()
        context = self.memory.get_memory_context_for_prompt("What AI topics am I studying?")
        duration_ms = (time.time() - start) * 1000

        self.assertLess(duration_ms, 100, f"Memory retrieval must take <100ms, took {duration_ms:.2f}ms")
        self.assertIn("AI Engineering", context)
        self.assertNotIn("Pizza", context, "Irrelevant memories must be excluded from context")

    # --- 4. Short-Term Context Bounding ---
    def test_04_short_term_context_bounding(self):
        conv = ConversationManager.get_instance()
        conv.clear_history()

        for i in range(15):
            conv.add_to_history("user", f"Turn {i} question")
            conv.add_to_history("assistant", f"Turn {i} answer")

        history = conv.get_history_context()
        self.assertLessEqual(len(history), 12, "Conversation history must be bounded (max 12 messages / 6 turns)")
        self.assertEqual(history[-1]["content"], "Turn 14 answer")

        conv.clear_history()
        self.assertEqual(len(conv.get_history_context()), 0, "clear_history must reset short-term context")

    # --- 5. Deduplication & Conflict Resolution ---
    def test_05_deduplication_and_conflict_resolution(self):
        mem_id1, _ = self.memory.remember("User prefers Python", category="user", key="preferred_language", value="Python")
        mem_id2, _ = self.memory.remember("User prefers Dart now", category="user", key="preferred_language", value="Dart")

        self.assertEqual(mem_id1, mem_id2, "Conflict resolution must update existing record instead of creating duplicate")

        recalls = self.memory.recall("language")
        self.assertEqual(len(recalls), 1, "Only 1 updated record should exist for preferred_language")
        self.assertIn("Dart", recalls[0].get("content", ""))

    # --- 6. Sensitive Data Protection ---
    def test_06_sensitive_data_protection(self):
        policy = MemoryPolicy()
        self.assertTrue(policy.contains_secret("my password is secret123"))
        self.assertTrue(policy.contains_secret("api_key = sk-proj-1234567890abcdef"))
        self.assertTrue(policy.contains_secret("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"))

        mem_id, msg = self.memory.remember("my password is 12345", category="user")
        self.assertIsNone(mem_id, "Sensitive password must be rejected from memory storage")
        self.assertIn("Privacy violation", msg)

    # --- 7. Project & Task Memory Isolation ---
    def test_07_project_and_task_memory_isolation(self):
        self.memory.store_project_info("Jarvis", "stack", "Python & Ollama")
        self.memory.store_project_info("InurumWebsite", "stack", "React & Vite")

        jarvis_mems = self.memory.retrieve_project("Jarvis")
        inurum_mems = self.memory.retrieve_project("InurumWebsite")

        self.assertGreaterEqual(len(jarvis_mems), 1)
        self.assertGreaterEqual(len(inurum_mems), 1)
        self.assertIn("Python & Ollama", jarvis_mems[0].get("content", ""))
        self.assertIn("React & Vite", inurum_mems[0].get("content", ""))

        self.memory.store_task("task_01", "Build website", status="completed")
        t = self.memory.retrieve_task("task_01")
        self.assertIsNotNone(t)
        self.assertEqual(t.get("task_id"), "task_01")

    # --- 8. Failure Handling & Non-Blocking Isolation ---
    def test_08_failure_handling_isolation(self):
        with patch.object(self.memory._store_engine, 'save_record', side_effect=RuntimeError("Disk write error")):
            mem_id, msg = self.memory.remember("Normal fact", category="user")
            self.assertIsNone(mem_id)

    # --- 9. Global Backward Compatibility (Rule 6) ---
    def test_09_backward_compatibility_functions(self):
        success = save_memory({"legacy_key": "legacy_value"})
        self.assertTrue(success)
        loaded = load_memory()
        self.assertIn("legacy_key", loaded)

    # --- 10. Website Builder Preservation ---
    def test_10_website_builder_preservation(self):
        protected_files = [
            os.path.join(BASE_DIR, "tools", "coding", "code_assistant.py"),
            os.path.join(BASE_DIR, "tools", "coding", "component_generation_pool.py"),
            os.path.join(BASE_DIR, "tools", "coding", "website_master_planner.py"),
            os.path.join(BASE_DIR, "tools", "coding", "website_planner.py"),
        ]
        for pf in protected_files:
            self.assertTrue(os.path.isfile(pf), f"Protected Website Builder file must exist: {pf}")

    # --- 11. Memory 2.0: Trivial Query Rejection ---
    def test_11_trivial_query_rejection(self):
        policy = MemoryPolicy()
        self.assertTrue(policy.is_trivial_content("what time is it?"))
        self.assertTrue(policy.is_trivial_content("what is 2+2?"))
        self.assertTrue(policy.is_trivial_content("thanks"))
        self.assertTrue(policy.is_trivial_content("ok"))

        should_store, reason = policy.should_remember("what time is it?", memory_type="semantic")
        self.assertFalse(should_store, "Trivial query must be rejected from semantic memory")

    # --- 12. Memory 2.0: Structured Field Schema Verification ---
    def test_12_record_schema_verification(self):
        mem_id, _ = self.memory.remember("User uses Riverpod for state management", category="user", key="preferred_state_mgmt")
        rec = self.memory._store_engine.get_record(mem_id)
        self.assertIsNotNone(rec)
        self.assertEqual(rec.get("user_id"), "user_owner")
        self.assertEqual(rec.get("confidence"), 1.0)
        self.assertIn("created_at", rec)
        self.assertIn("updated_at", rec)
        self.assertIn("last_used_at", rec)
        self.assertIn("importance", rec)

if __name__ == "__main__":
    unittest.main()

