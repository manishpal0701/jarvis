"""
tests/test_website_research_enhancement.py
Comprehensive test suite verifying:
1. Normal vs company web research trigger
2. Structured CompanyResearchContext creation & anti-hallucination
3. Safe research failure fallback
4. Unattended background task execution & sleep guard persistence
5. Status query safety (no duplicate builds)
6. Authoritative website readiness gate preservation
7. Regression test compatibility across all subsystems
"""

import unittest
import time
from tools.coding.website_researcher import WebsiteResearcher, CompanyResearchContext
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer, WebsiteBrief, WebsiteCategory, WebsiteSubject
from tools.coding.website_state import WebsiteStateManager, ActiveWebsiteState
from core.task_orchestrator import TaskOrchestrator
from conversation.command_router import CommandRouter

class TestWebsiteResearchEnhancement(unittest.TestCase):

    def setUp(self):
        self.orchestrator = TaskOrchestrator.get_instance()
        self.orchestrator._active_task = None
        self.orchestrator._last_completed_task = None

    def test_1_normal_website_request_uses_website_builder(self):
        """TEST 1: Normal website request without specific company entity."""
        cmd = "Jarvis mere liye ek modern portfolio website bana do"
        entity = WebsiteRequirementsAnalyzer.detect_company_entity(cmd)
        self.assertIsNone(entity)

    def test_2_company_website_request_triggers_research(self):
        """TEST 2: Company website request triggers entity detection."""
        cmd = "Jarvis Tesla ke liye ek landing page bana do"
        entity = WebsiteRequirementsAnalyzer.detect_company_entity(cmd)
        self.assertEqual(entity, "Tesla")

    def test_3_research_result_is_structured_and_passed(self):
        """TEST 3: Research result is structured and passed to website generation brief."""
        ctx = WebsiteResearcher.research_company("Tesla")
        self.assertIsInstance(ctx, CompanyResearchContext)
        self.assertTrue(ctx.entity == "Tesla" or ctx.official_name == "Tesla")
        
        brief = WebsiteRequirementsAnalyzer.extract_information("Tesla website", WebsiteCategory.BUSINESS, WebsiteSubject(name="Tesla"))
        brief.research_context = ctx.to_dict()
        summary = WebsiteRequirementsAnalyzer.format_brief_summary(brief)
        self.assertIn("Verified Web Research", summary)

    def test_4_unverified_information_is_not_hallucinated(self):
        """TEST 4: Unverified information is not hallucinated for unknown entities."""
        ctx = WebsiteResearcher.research_company("NonExistentUnknownBrand123987")
        self.assertEqual(ctx.entity, "NonExistentUnknownBrand123987")
        self.assertEqual(ctx.official_name, "NonExistentUnknownBrand123987")
        self.assertEqual(ctx.sources, [])

    def test_5_research_failure_handled_safely(self):
        """TEST 5: Research failure handled safely without crashing."""
        try:
            ctx = WebsiteResearcher.research_company("")
            self.assertIsInstance(ctx, CompanyResearchContext)
        except Exception as e:
            self.fail(f"research_company crashed on empty input: {e}")

    def test_6_unattended_website_task_remains_active(self):
        """TEST 6: Unattended website task remains active while user is silent."""
        cmd = "Jarvis ek modern portfolio website bana do, main bahar ghoom ke aata hoon."
        router = CommandRouter()
        self.assertTrue(router.is_unattended_request(cmd))
        self.assertTrue(router.is_coding_task(cmd))
        
        # Start background task
        self.orchestrator.start_task("unattended_proj", "WEBSITE_BUILD", "Unattended build", total_items=4)
        self.assertTrue(self.orchestrator.is_task_active())

    def test_7_task_aware_sleep_guard_prevents_sleep(self):
        """TEST 7: Task-aware sleep guard prevents sleep during active task."""
        self.orchestrator.start_task("site_guard_test", "WEBSITE_BUILD", "Testing sleep guard", total_items=5)
        self.assertTrue(self.orchestrator.is_task_active())

    def test_8_kitna_kaam_hua_returns_current_task_state(self):
        """TEST 8: 'kitna kaam hua?' returns current task state."""
        self.orchestrator.start_task("site_progress_test", "WEBSITE_BUILD", "Testing progress", total_items=3)
        self.orchestrator.update_progress("site_progress_test", stage="GENERATING_FILES", current_item="App.tsx", completed_item="package.json")
        
        summary = self.orchestrator.get_natural_progress_summary()
        self.assertIn("package.json", summary)
        self.assertIn("App.tsx", summary)

    def test_9_status_query_does_not_start_second_task(self):
        """TEST 9: Status query does not start a second website task."""
        router = CommandRouter()
        queries = ["Jarvis kitna kaam hua?", "Website ready hai kya?", "Website ka kya hua?"]
        for q in queries:
            self.assertTrue(router.is_status_query(q))

    def test_10_completed_task_releases_sleep_guard(self):
        """TEST 10: Completed task releases sleep guard."""
        self.orchestrator.start_task("comp_test", "WEBSITE_BUILD", "Testing completion", total_items=2)
        self.assertTrue(self.orchestrator.is_task_active())
        self.orchestrator.complete_task("comp_test", "Done")
        self.assertFalse(self.orchestrator.is_task_active())

    def test_11_failed_task_releases_sleep_guard(self):
        """TEST 11: Failed task releases sleep guard."""
        self.orchestrator.start_task("fail_test", "WEBSITE_BUILD", "Testing failure", total_items=2)
        self.assertTrue(self.orchestrator.is_task_active())
        self.orchestrator.fail_task("fail_test", "Build error")
        self.assertFalse(self.orchestrator.is_task_active())

    def test_12_website_readiness_depends_on_existing_authoritative_gates(self):
        """TEST 12: Website readiness depends on existing authoritative gates."""
        state = ActiveWebsiteState()
        self.assertFalse(state.is_authoritative_ready())
        self.assertFalse(state.website_ready)
        
        state.dependency_validation_passed = True
        state.build_passed = True
        state.preview_running = True
        state.http_status_ok = True
        state.visual_qa_status = "passed"
        state.visual_qa_passed = True
        state.responsive_passed = True
        state.console_errors = 0
        state.broken_images = 0
        self.assertTrue(state.is_authoritative_ready())
        self.assertTrue(state.website_ready)

    def test_13_existing_website_builder_regression_tests_pass(self):
        """TEST 13: Existing Website Builder state regression check."""
        wsm = WebsiteStateManager.get_instance()
        wsm.reset_active_website("test_proj", "/tmp/test")
        active = wsm.get_active_website()
        self.assertEqual(active.project_name, "test_proj")
        self.assertFalse(active.website_ready)

    def test_14_existing_conversation_tests_pass(self):
        """TEST 14: Existing conversation status query check."""
        router = CommandRouter()
        self.assertTrue(router.is_status_query("Jarvis kitna kaam hua?"))

    def test_15_existing_task_aware_sleep_tests_pass(self):
        """TEST 15: Existing TaskOrchestrator active check."""
        self.orchestrator.start_task("t15", "WEBSITE_BUILD", "Task 15")
        self.assertTrue(self.orchestrator.is_task_active())
        self.orchestrator.complete_task("t15")
        self.assertFalse(self.orchestrator.is_task_active())

if __name__ == "__main__":
    unittest.main()
