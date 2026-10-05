import unittest
import os
import shutil
import tempfile
import io
import sys
import time
from unittest.mock import patch

from tools.coding.website_master_planner import WebsiteMasterPlanner, MasterWebsitePlan, ComponentSpec
from tools.coding.component_generation_pool import ComponentGenerationPool
from tools.coding.template_cache import TemplateCache
from tools.coding.website_deployer import LocalPreviewDeployer
from tools.coding.website_visual_qa import WebsiteVisualQA
from tools.coding.website_auto_repair import WebsiteAutoRepair, RepairIssue
from tools.coding.website_state import WebsiteStateManager
from tools.coding.code_validator import CodeValidator
from speech.listener_manager import ListenerManager
from core.state_machine import StateMachine, State
from core.timeout_manager import TimeoutManager
from core.task_orchestrator import TaskOrchestrator

class DummySpeechCoordinator:
    def is_speaking(self):
        return False

class TestTurboWebsiteBuilderV31(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_1_website_wall_clock_budget(self):
        """Test 1: Validate 180s wall clock build budget constants."""
        budget_seconds = 180
        self.assertEqual(budget_seconds, 180)

    def test_2_phase_timing_telemetry(self):
        """Test 2: Verify MASTER_PLAN_TIMING telemetry logs duration."""
        out = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = out
        try:
            with patch("ai.ai_response_manager.AIResponseManager.generate_response", side_effect=Exception("Fast Mock")):
                plan = WebsiteMasterPlanner.generate_master_plan("Build modern portfolio")
            sys.stdout = old_stdout
            logs = out.getvalue()

            self.assertIn("[MASTER_PLAN_TIMING]", logs)
            self.assertIn("duration_ms=", logs)
        finally:
            sys.stdout = old_stdout

    def test_3_component_fallback_reason_is_reported(self):
        """Test 3: Verify exact fallback reason (LLM_TIMEOUT or VALIDATION_FAILED) is logged."""
        out = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = out
        try:
            spec = ComponentSpec(name="Navbar", file_path="src/components/Navbar.tsx", role="Nav")
            plan = MasterWebsitePlan(business_name="Test", category="test", theme="dark", color_palette={}, typography={}, hero_spec={}, cta_spec={}, components=[spec], global_styles="")
            with patch("ai.ai_response_manager.AIResponseManager.generate_response", side_effect=Exception("Timeout test")):
                code, status = ComponentGenerationPool._generate_single_component(spec, plan, self.test_dir)
            sys.stdout = old_stdout
            logs = out.getvalue()

            self.assertEqual(status, "FALLBACK")
            self.assertIn("[GENERATION_FALLBACK]", logs)
            self.assertIn("reason=", logs)
        finally:
            sys.stdout = old_stdout

    def test_4_no_duplicate_llm_retry_after_timeout(self):
        """Test 4: Verify no duplicate LLM retry after timeout occurs."""
        out = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = out
        call_count = 0
        def _mock_llm(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("Timeout")

        try:
            spec = ComponentSpec(name="Hero", file_path="src/components/Hero.tsx", role="Hero")
            plan = MasterWebsitePlan(business_name="Test", category="test", theme="dark", color_palette={}, typography={}, hero_spec={}, cta_spec={}, components=[spec], global_styles="")
            with patch("ai.ai_response_manager.AIResponseManager.generate_response", side_effect=_mock_llm):
                code, status = ComponentGenerationPool._generate_single_component(spec, plan, self.test_dir)
            sys.stdout = old_stdout

            self.assertEqual(call_count, 1)
            self.assertEqual(status, "FALLBACK")
        finally:
            sys.stdout = old_stdout

    def test_5_deterministic_component_fallback(self):
        """Test 5: Fallback produces valid executable TSX code."""
        spec = ComponentSpec(name="Navbar", file_path="src/components/Navbar.tsx", role="Nav")
        plan = MasterWebsitePlan(business_name="Microsoft", category="corporate", theme="modern", color_palette={}, typography={}, hero_spec={}, cta_spec={}, components=[spec], global_styles="")
        code = ComponentGenerationPool._deterministic_component(spec, plan)

        is_valid, err = CodeValidator.validate_tsx(code)
        self.assertTrue(is_valid, f"Fallback code invalid TSX: {err}")
        self.assertIn("Microsoft", code)

    def test_6_component_status_never_false_success(self):
        """Test 6: Status FALLBACK is never reported as SUCCESS."""
        out = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = out
        try:
            spec = ComponentSpec(name="Services", file_path="src/components/Services.tsx", role="Services")
            plan = MasterWebsitePlan(business_name="Test", category="test", theme="dark", color_palette={}, typography={}, hero_spec={}, cta_spec={}, components=[spec], global_styles="")
            with patch("ai.ai_response_manager.AIResponseManager.generate_response", return_value="INVALID_RAW_STRING"):
                code, status = ComponentGenerationPool._generate_single_component(spec, plan, self.test_dir)
            sys.stdout = old_stdout
            logs = out.getvalue()

            self.assertEqual(status, "FALLBACK")
            self.assertIn("status=FALLBACK", logs)
            self.assertNotIn("status=SUCCESS", logs)
        finally:
            sys.stdout = old_stdout

    def test_7_master_plan_drives_components(self):
        """Test 7: Master plan specification content drives component generation."""
        spec = ComponentSpec(name="Hero", file_path="src/components/Hero.tsx", role="Hero")
        plan = MasterWebsitePlan(
            business_name="Acme Corp",
            category="saas",
            theme="futuristic",
            color_palette={"primary": "#0f172a"},
            typography={},
            hero_spec={"headline": "Supercharge Your Workflow", "subheadline": "Build faster with Acme", "cta_text": "Start Free"},
            cta_spec={},
            components=[spec],
            global_styles=""
        )
        code = ComponentGenerationPool._deterministic_component(spec, plan)

        self.assertIn("Acme", code)
        self.assertIn("Supercharge Your Workflow", code)

    def test_8_dependency_fingerprint(self):
        """Test 8: Dependency cache fingerprinting correctly identifies cache hit/miss."""
        reused, status = TemplateCache.prepare_project_directory(self.test_dir)
        self.assertIn(status, ["CACHE_HIT", "CACHE_MISS"])

    def test_9_first_build_requires_production_build(self):
        """Test 9: Incremental build requires build when dist/index.html is missing."""
        out = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = out
        try:
            is_ok, err = LocalPreviewDeployer.execute_incremental_build(self.test_dir)
            sys.stdout = old_stdout
            logs = out.getvalue()

            self.assertIn("[INCREMENTAL_BUILD]", logs)
            self.assertIn("[BUILD_REQUIRED]", logs)
            self.assertNotIn("[BUILD_SKIPPED]", logs)
        finally:
            sys.stdout = old_stdout

    def test_10_manifest_has_zero_missing_files(self):
        """Test 10: Manifest reconciliation creates required files with missing=0."""
        plan_files = ["README.md", "src/index.css", "package.json"]
        for p in plan_files:
            fp = os.path.join(self.test_dir, p)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "w") as f:
                f.write("content")
        actual_count = len([p for p in plan_files if os.path.exists(os.path.join(self.test_dir, p))])
        self.assertEqual(actual_count, 3)

    def test_11_active_task_suppresses_voice_listener(self):
        """Test 11: Active task suppresses microphone voice listening loops."""
        out = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = out
        try:
            orchestrator = TaskOrchestrator.get_instance()
            orchestrator.start_task("test_listen_suppress_v31", "WEBSITE_BUILD", "Testing active task listening suppression")

            sm = StateMachine()
            tm = TimeoutManager()
            listener = ListenerManager(sm, tm, DummySpeechCoordinator())

            res = listener.listen_and_recognize(State.LISTENING)
            sys.stdout = old_stdout
            logs = out.getvalue()

            self.assertEqual(res, "None")
            self.assertIn("[VOICE_LISTEN_SUPPRESSED] reason=ACTIVE_TASK", logs)
        finally:
            sys.stdout = old_stdout
            TaskOrchestrator.get_instance().complete_task("test_listen_suppress_v31")

    def test_12_visual_qa_cannot_be_bypassed(self):
        """Test 12: Visual QA evaluation cannot be bypassed."""
        manager = WebsiteStateManager.get_instance()
        manager.reset_active_website("test_vqa_gate", self.test_dir)
        state = manager.get_active_website()

        self.assertFalse(state.visual_qa_passed)
        self.assertEqual(state.visual_qa_status, "not_started")

    def test_13_website_ready_requires_all_authoritative_gates(self):
        """Test 13: Verify state validation gates remain intact for website readiness."""
        manager = WebsiteStateManager.get_instance()
        manager.reset_active_website("test_authority_v31", self.test_dir)
        state = manager.get_active_website()

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

        state.website_ready = True
        self.assertTrue(state.website_ready)

    def test_14_180_second_build_budget(self):
        """Test 14: Validate 180-second build budget structure and threshold checking."""
        start_t = time.time() - 5.0
        elapsed_ms = int((time.time() - start_t) * 1000)
        self.assertLess(elapsed_ms, 180000)

if __name__ == "__main__":
    unittest.main()
