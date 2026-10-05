import os
import sys
import unittest
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from memory.memory_store import MemoryStore
from memory.memory_policy import MemoryPolicy
from memory.memory_writer import MemoryWriter
from memory.memory_retriever import MemoryRetriever
from memory.working_memory import WorkingMemory
from memory.episodic_memory import EpisodicMemory
from memory.semantic_memory import SemanticMemory
from memory.user_memory import UserMemory
from memory.project_memory import ProjectMemory
from memory.task_memory import TaskMemory
from memory.memory_manager import MemoryManager
from memory.memory import load_memory, save_memory

class TestMemoryLayer(unittest.TestCase):

    def setUp(self):
        MemoryManager._instance = None
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store_file = os.path.join(self.temp_dir.name, "test_memory.json")
        self.store = MemoryStore(store_file=self.store_file)
        self.policy = MemoryPolicy()
        self.writer = MemoryWriter(store=self.store, policy=self.policy)
        self.retriever = MemoryRetriever(store=self.store)

    def tearDown(self):
        MemoryManager._instance = None
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_store_crud(self):
        record = {
            "id": "mem_test_1",
            "type": "semantic",
            "content": "Python is awesome",
            "importance": 0.8,
            "created_at": "2026-08-14T12:00:00",
            "updated_at": "2026-08-14T12:00:00"
        }
        self.assertTrue(self.store.save_record(record))
        fetched = self.store.get_record("mem_test_1")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["content"], "Python is awesome")

        self.assertTrue(self.store.delete_record("mem_test_1"))
        self.assertIsNone(self.store.get_record("mem_test_1"))

    def test_secret_filtering(self):
        should_store, reason = self.policy.should_remember("My password is supersecret123", "user")
        self.assertFalse(should_store)
        self.assertIn("Privacy violation", reason)

        should_store2, reason2 = self.policy.should_remember("API_KEY = sk_test_1234567890", "semantic")
        self.assertFalse(should_store2)

        should_store3, reason3 = self.policy.should_remember("I prefer Python over JavaScript", "user")
        self.assertTrue(should_store3)

    def test_working_memory(self):
        wm = WorkingMemory()
        wm.update_task_state(task="Fix Login Bug", step="Executing API Check", active_file="auth.py")
        wm.set("error_code", 401)

        state = wm.get_all()
        self.assertEqual(state["current_task"], "Fix Login Bug")
        self.assertEqual(state["current_step"], "Executing API Check")
        self.assertEqual(state["current_file"], "auth.py")
        self.assertEqual(state["context"]["error_code"], 401)

        wm.clear()
        cleared_state = wm.get_all()
        self.assertIsNone(cleared_state["current_task"])

    def test_episodic_memory(self):
        ep = EpisodicMemory(writer=self.writer, retriever=self.retriever)
        mem_id, msg = ep.log_event("Refactored Auth Service", outcome="success", details="All 5 unit tests passed")
        self.assertIsNotNone(mem_id)

        events = ep.get_recent_events(limit=5)
        self.assertTrue(len(events) > 0)
        self.assertIn("Refactored Auth Service", events[0]["content"])

    def test_semantic_memory(self):
        sem = SemanticMemory(writer=self.writer, retriever=self.retriever)
        mem_id, _ = sem.add_fact("Jarvis uses Ollama qwen3:8b locally for AI responses", tags=["ai", "ollama"])
        self.assertIsNotNone(mem_id)

        facts = sem.search_facts("Ollama")
        self.assertTrue(len(facts) > 0)

    def test_user_memory(self):
        um = UserMemory(writer=self.writer, retriever=self.retriever)
        mem_id, _ = um.set_preference("preferred_language", "Python")
        self.assertIsNotNone(mem_id)

        prefs = um.get_user_memories()
        self.assertTrue(len(prefs) > 0)

    def test_project_memory(self):
        pm = ProjectMemory(writer=self.writer, retriever=self.retriever)
        mem_id, _ = pm.record_project_info("Jarvis", "architecture", "Modular package layer")
        self.assertIsNotNone(mem_id)

        mems = pm.get_project_memories("Jarvis")
        self.assertTrue(len(mems) > 0)

    def test_task_memory(self):
        tm = TaskMemory(writer=self.writer, retriever=self.retriever)
        mem_id, _ = tm.record_task("task_001", "Implement Memory Layer", status="in_progress")
        self.assertIsNotNone(mem_id)

        task_rec = tm.get_task("task_001")
        self.assertIsNotNone(task_rec)
        self.assertEqual(task_rec["metadata"]["status"], "in_progress")

        mem_id2, _ = tm.record_task("task_001", "Implement Memory Layer", status="completed")
        updated_rec = tm.get_task("task_001")
        self.assertEqual(updated_rec["metadata"]["status"], "completed")

    def test_memory_manager_facade(self):
        mgr = MemoryManager(store_file=self.store_file)
        
        mem_id = mgr.store("Jarvis backend uses Python FastAPI", memory_type="semantic", tags=["fastapi"])
        self.assertIsNotNone(mem_id)

        relevant = mgr.retrieve_relevant("FastAPI", limit=3)
        self.assertTrue(len(relevant) > 0)
        self.assertIn("FastAPI", relevant[0]["content"])

        found = mgr.search("Python")
        self.assertTrue(len(found) > 0)

        mgr.set_working_context("active_agent", "MemoryAgent")
        self.assertEqual(mgr.get_working_context("active_agent"), "MemoryAgent")
        mgr.clear_working_memory()
        self.assertIsNone(mgr.get_working_context("active_agent"))

    def test_concurrency(self):
        mgr = MemoryManager(store_file=self.store_file)
        errors = []

        def worker(thread_idx):
            try:
                for i in range(10):
                    mgr.store(f"Unique Thread {thread_idx} memory entry {i} timestamp {time.time_ns()}", memory_type="episodic")
                    time.sleep(0.005)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        all_recs = mgr.retrieve(memory_type="episodic", limit=100)
        self.assertGreaterEqual(len(all_recs), 50)

    def test_backward_compatibility(self):
        self.assertTrue(save_memory({"preferred_editor": "VSCode", "mode": "dark"}))
        loaded = load_memory()
        self.assertIsInstance(loaded, dict)
        self.assertIn("preferred_editor", loaded)
        self.assertEqual(loaded["preferred_editor"], "VSCode")


if __name__ == "__main__":
    unittest.main()
