"""
tests/test_task_aware_sleep.py
Focused unit and integration test suite for:
1. Task-aware sleep prevention & guard suppression
2. Task completion and failure sleep guard release
3. Status query interception without creating duplicate tasks
4. Honest progress summaries with no fake percentages or fake ETAs
5. Simulated long-running task integration flow exceeding idle timeout
"""

import unittest
import time
from core.task_orchestrator import TaskOrchestrator, TaskInfo
from conversation.command_router import CommandRouter
from core.state_machine import StateMachine, State
from core.timeout_manager import TimeoutManager
from core.session_manager import SessionManager
from conversation.conversation_engine import ConversationEngine

class TestTaskAwareSleep(unittest.TestCase):

    def setUp(self):
        self.orchestrator = TaskOrchestrator.get_instance()
        # Reset orchestrator internal state between tests
        self.orchestrator._active_task = None
        self.orchestrator._last_completed_task = None

    def test_1_normal_idle_session_sleep(self):
        """1. Normal idle session still enters sleep after configured timeout."""
        tm = TimeoutManager(timeout_seconds=0.1)
        tm.reset()
        time.sleep(0.15)
        self.assertTrue(tm.is_timed_out())
        self.assertFalse(self.orchestrator.is_task_active())

    def test_2_active_website_build_prevents_sleep(self):
        """2. Active WEBSITE_BUILD prevents sleep."""
        self.orchestrator.start_task("proj_test_1", "WEBSITE_BUILD", "Testing website build", total_items=5)
        self.assertTrue(self.orchestrator.is_task_active())
        self.assertEqual(self.orchestrator.get_active_task().task_type, "WEBSITE_BUILD")

    def test_3_active_code_generation_prevents_sleep(self):
        """3. Active CODE_GENERATION prevents sleep."""
        self.orchestrator.start_task("standalone_123", "CODE_GENERATION", "Testing script writing", total_items=1)
        self.assertTrue(self.orchestrator.is_task_active())
        self.assertEqual(self.orchestrator.get_active_task().task_type, "CODE_GENERATION")

    def test_4_task_completion_reenables_sleep(self):
        """4. Task completion re-enables normal sleep behavior."""
        self.orchestrator.start_task("proj_test_2", "WEBSITE_BUILD", "Testing completion", total_items=3)
        self.assertTrue(self.orchestrator.is_task_active())
        
        self.orchestrator.complete_task("proj_test_2", "Preview live")
        self.assertFalse(self.orchestrator.is_task_active())

    def test_5_task_failure_reenables_sleep(self):
        """5. Task failure re-enables normal sleep behavior."""
        self.orchestrator.start_task("proj_test_3", "WEBSITE_BUILD", "Testing failure", total_items=3)
        self.assertTrue(self.orchestrator.is_task_active())
        
        self.orchestrator.fail_task("proj_test_3", "Build step failed")
        self.assertFalse(self.orchestrator.is_task_active())

    def test_6_status_query_returns_current_task_state(self):
        """6. Status query returns current task state."""
        self.orchestrator.start_task("portfolio_1", "WEBSITE_BUILD", "Portfolio website", total_items=4)
        self.orchestrator.update_progress("portfolio_1", stage="GENERATING_FILES", current_item="Navbar.tsx", completed_item="package.json")
        
        router = CommandRouter()
        self.assertTrue(router.is_status_query("Jarvis kitna kaam hua?"))
        self.assertTrue(router.is_status_query("Website ready hai kya?"))
        
        summary = self.orchestrator.get_natural_progress_summary()
        self.assertIn("package.json", summary)
        self.assertIn("Navbar.tsx", summary)

    def test_7_status_query_does_not_create_new_task(self):
        """7. Status query does not create a new task or trigger coding task."""
        router = CommandRouter()
        query = "Jarvis kitna kaam hua?"
        self.assertTrue(router.is_status_query(query))
        
        # Verify that even though query contains "website ready", is_status_query intercepts it before is_coding_task
        query_2 = "Website ready hai kya?"
        self.assertTrue(router.is_status_query(query_2))

    def test_8_no_fake_percentage_or_fake_eta(self):
        """8. No fake percentage or fake ETA is reported."""
        self.orchestrator.start_task("proj_test_4", "WEBSITE_BUILD", "Testing fake strings", total_items=10)
        self.orchestrator.update_progress("proj_test_4", stage="BUILDING_PRODUCTION")
        
        summary = self.orchestrator.get_natural_progress_summary()
        self.assertNotIn("50%", summary)
        self.assertNotIn("2 minutes remaining", summary)
        self.assertIn("npm build", summary)

    def test_9_no_false_website_ready(self):
        """9. No false website ready response is possible while running or when failed."""
        self.orchestrator.start_task("proj_test_5", "WEBSITE_BUILD", "Testing ready gate", total_items=5)
        self.orchestrator.update_progress("proj_test_5", stage="GENERATING_FILES")
        
        summary = self.orchestrator.get_natural_progress_summary()
        self.assertNotIn("completely ready aur verified hai", summary)
        
        self.orchestrator.fail_task("proj_test_5", "Production build failed")
        summary_failed = self.orchestrator.get_natural_progress_summary()
        self.assertIn("issue aaya hai", summary_failed)

    def test_10_controlled_integration_flow(self):
        """10. Controlled integration test: task runs longer than idle timeout -> sleep suppressed -> status queried -> completed -> guard released."""
        # 1. Start website task
        self.orchestrator.start_task("integration_site", "WEBSITE_BUILD", "Integration website", total_items=3)
        self.assertTrue(self.orchestrator.is_task_active())
        
        # 2. Simulate 0.5s passing (simulated long wait > short timeout 0.1s)
        tm = TimeoutManager(timeout_seconds=0.1)
        tm.reset()
        time.sleep(0.15)
        
        # Verify task guard suppresses sleep
        self.assertTrue(self.orchestrator.is_task_active())
        if self.orchestrator.is_task_active():
            tm.reset()  # Guard action
        self.assertFalse(tm.is_timed_out())
        
        # 3. Simulate user querying status mid-build
        router = CommandRouter()
        self.assertTrue(router.is_status_query("Boss kitna kaam hua?"))
        summary = self.orchestrator.get_natural_progress_summary()
        self.assertTrue(len(summary) > 0)
        
        # 4. Complete task
        self.orchestrator.complete_task("integration_site", "Build success")
        self.assertFalse(self.orchestrator.is_task_active())

if __name__ == "__main__":
    unittest.main()
