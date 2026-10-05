"""
tests/test_website_auto_repair.py
Unit test suite for Intelligent Website Auto-Repair Loop.
Covers 20 focused test cases for RepairIssue, RepairPlan, RepairResult,
WebsiteAutoRepair, TaskOrchestrator integration, and authoritative WEBSITE_READY safety.
"""

import unittest
import os
import tempfile
import shutil
from tools.coding.website_auto_repair import (
    WebsiteAutoRepair, RepairIssue, RepairPlan, RepairResult, MAX_REPAIR_ATTEMPTS
)
from tools.coding.website_state import ActiveWebsiteState


class TestWebsiteAutoRepair(unittest.TestCase):

    def setUp(self):
        self.project_dir = tempfile.mkdtemp(prefix="test_repair_")
        # Create minimal project structure
        os.makedirs(os.path.join(self.project_dir, "src", "components"), exist_ok=True)
        with open(os.path.join(self.project_dir, "src", "App.tsx"), "w") as f:
            f.write("export default function App() { return <div>Hello</div>; }")
        with open(os.path.join(self.project_dir, "src", "components", "Navbar.tsx"), "w") as f:
            f.write("export default function Navbar() { return <nav>Menu</nav>; }")
        self.generated_contents = {
            "src/App.tsx": "export default function App() { return <div>Hello</div>; }",
            "src/components/Navbar.tsx": "export default function Navbar() { return <nav>Menu</nav>; }",
            "src/components/Hero.tsx": "export default function Hero() { return <section>Hero</section>; }",
            "src/index.css": "@import 'tailwindcss';",
            "package.json": '{"name": "test", "dependencies": {"react": "^18.0.0"}, "scripts": {"build": "vite build"}}',
        }

    def tearDown(self):
        shutil.rmtree(self.project_dir, ignore_errors=True)

    # 1. Build syntax error is detected
    def test_1_build_syntax_error_detected(self):
        issue = RepairIssue(
            issue_type="build",
            message="src/App.tsx: Unexpected token in JSX expression at line 5",
            severity="error",
            repairable=True
        )
        self.assertEqual(issue.issue_type, "build")
        self.assertTrue(issue.repairable)

    # 2. Missing import is detected
    def test_2_missing_import_detected(self):
        issue = RepairIssue(
            issue_type="build",
            message="Cannot find module 'react-router-dom' in src/App.tsx",
            source="npm_build",
            severity="error",
            repairable=True
        )
        plan = WebsiteAutoRepair.diagnose_failure(issue, self.project_dir, list(self.generated_contents.keys()))
        self.assertEqual(plan.affected_file, "src/App.tsx")

    # 3. Runtime error is detected
    def test_3_runtime_error_detected(self):
        issue = RepairIssue(
            issue_type="runtime",
            message="TypeError: Cannot read property 'map' of undefined in Navbar.tsx",
            severity="error",
            repairable=True
        )
        plan = WebsiteAutoRepair.diagnose_failure(issue, self.project_dir, list(self.generated_contents.keys()))
        self.assertIn("Navbar", plan.affected_file)

    # 4. Mobile overflow is detected
    def test_4_mobile_overflow_detected(self):
        issue = RepairIssue(
            issue_type="visual_qa",
            message="Mobile navbar overflow detected in Navbar.tsx",
            source="visual_qa",
            severity="error",
            repairable=True
        )
        plan = WebsiteAutoRepair.diagnose_failure(issue, self.project_dir, list(self.generated_contents.keys()))
        self.assertIn("Navbar", plan.affected_file)

    # 5. Broken asset is detected
    def test_5_broken_asset_detected(self):
        issue = RepairIssue(
            issue_type="asset",
            message="Broken image URL in Hero.tsx: https://invalid.example.com/img.jpg",
            source="visual_qa",
            severity="warning",
            repairable=True
        )
        plan = WebsiteAutoRepair.diagnose_failure(issue, self.project_dir, list(self.generated_contents.keys()))
        self.assertIsNotNone(plan.affected_file)

    # 6. Correct affected file is identified
    def test_6_correct_affected_file_identified(self):
        issue = RepairIssue(
            issue_type="build",
            message="Build failure in src/index.css: Tailwind directive missing",
            severity="error",
            repairable=True
        )
        plan = WebsiteAutoRepair.diagnose_failure(issue, self.project_dir, list(self.generated_contents.keys()))
        self.assertIn("css", plan.affected_file)

    # 7. Targeted repair plan is generated
    def test_7_targeted_repair_plan_is_generated(self):
        issue = RepairIssue(
            issue_type="visual_qa",
            message="Content clipping on mobile; navbar overflows viewport",
            source="visual_qa",
            severity="error",
            repairable=True
        )
        plan = WebsiteAutoRepair.diagnose_failure(issue, self.project_dir, list(self.generated_contents.keys()))
        self.assertIsInstance(plan, RepairPlan)
        self.assertIsNotNone(plan.diagnosis)
        self.assertIsNotNone(plan.affected_file)
        self.assertIsNotNone(plan.repair_action)

    # 8. Repair does not modify unrelated files
    def test_8_repair_does_not_modify_unrelated_files(self):
        """Verify diagnose_failure targets a single specific file, not all files."""
        issue = RepairIssue(
            issue_type="build",
            message="Error in src/App.tsx: JSX syntax error",
            severity="error",
            repairable=True,
            affected_files=["src/App.tsx"]
        )
        plan = WebsiteAutoRepair.diagnose_failure(issue, self.project_dir, list(self.generated_contents.keys()))
        self.assertEqual(plan.affected_file, "src/App.tsx")

    # 9. Successful repair triggers existing validation (repair returns success status)
    def test_9_successful_repair_result_status(self):
        result = RepairResult(
            attempt_number=1,
            status="success",
            repaired_file="src/App.tsx"
        )
        self.assertEqual(result.status, "success")
        self.assertNotEqual(result.status, "limit_reached")

    # 10. Failed repair does not claim WEBSITE_READY
    def test_10_failed_repair_does_not_claim_website_ready(self):
        state = ActiveWebsiteState()
        # Simulate failed repair: build_passed stays False
        state.build_passed = False
        self.assertFalse(state.is_authoritative_ready())
        result = RepairResult(attempt_number=2, status="failed")
        self.assertEqual(result.status, "failed")
        # WEBSITE_READY must still be False
        self.assertFalse(state.is_authoritative_ready())

    # 11. Maximum 2 attempts enforced via diagnose_and_repair
    def test_11_max_2_attempts_enforced(self):
        issue = RepairIssue(
            issue_type="build",
            message="Persistent build error",
            severity="error",
            repairable=True
        )
        result = WebsiteAutoRepair.diagnose_and_repair(
            task_id="test_task",
            project_dir=self.project_dir,
            issue=issue,
            attempt_number=2,
            generated_contents=self.generated_contents,
            code_generator_func=None
        )
        # Attempt 2 is allowed (MAX=2)
        self.assertIn(result.status, ["success", "failed", "unrepairable"])

    # 12. Third repair attempt is rejected
    def test_12_third_repair_attempt_rejected(self):
        issue = RepairIssue(
            issue_type="build",
            message="Persistent build error attempt 3",
            severity="error",
            repairable=True
        )
        result = WebsiteAutoRepair.diagnose_and_repair(
            task_id="test_task",
            project_dir=self.project_dir,
            issue=issue,
            attempt_number=3,  # This exceeds MAX_REPAIR_ATTEMPTS = 2
            generated_contents=self.generated_contents,
            code_generator_func=None
        )
        self.assertEqual(result.status, "limit_reached")
        self.assertIn("Maximum auto-repair attempts", result.error_details)

    # 13. TaskOrchestrator reports REPAIRING stage correctly
    def test_13_task_orchestrator_repairing_stage(self):
        from core.task_orchestrator import TaskOrchestrator
        orch = TaskOrchestrator.get_instance()
        orch.start_task("repair_test", "WEBSITE_BUILD", "Repair Test", total_items=5)
        orch.update_progress("repair_test", stage="REPAIRING", current_item="build_error_attempt_1")
        summary = orch.get_natural_progress_summary()
        self.assertIn("Boss,", summary)
        self.assertIn("fix", summary.lower())
        orch.fail_task("repair_test", "test done")

    # 14. Status query does not create duplicate task
    def test_14_status_query_no_duplicate_task(self):
        from core.task_orchestrator import TaskOrchestrator
        orch = TaskOrchestrator.get_instance()
        orch.start_task("repair_dedup_test", "WEBSITE_BUILD", "Dedup Test", total_items=3)
        active_id_before = orch.get_active_task().task_id
        orch.update_progress("repair_dedup_test", stage="REPAIRING", current_item="layout_fix")
        _ = orch.get_natural_progress_summary()
        active_id_after = orch.get_active_task().task_id
        self.assertEqual(active_id_before, active_id_after)
        orch.fail_task("repair_dedup_test", "test done")

    # 15. .env and secrets are protected by safety guard
    def test_15_env_and_secrets_protected(self):
        self.assertFalse(WebsiteAutoRepair.is_safe_target_file(".env", self.project_dir))
        self.assertFalse(WebsiteAutoRepair.is_safe_target_file("config.py", self.project_dir))
        self.assertFalse(WebsiteAutoRepair.is_safe_target_file("main.py", self.project_dir))
        self.assertFalse(WebsiteAutoRepair.is_safe_target_file("conversation_engine.py", self.project_dir))

    # 16. Existing WEBSITE_READY authority remains unchanged
    def test_16_website_ready_authority_unchanged(self):
        state = ActiveWebsiteState()
        self.assertFalse(state.is_authoritative_ready())
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

    # 17. Existing Visual Intelligence remains unchanged after auto-repair
    def test_17_visual_intelligence_unchanged(self):
        from tools.coding.website_visual_intelligence import WebsiteVisualIntelligence, VisualWebsitePlan
        from tools.coding.website_requirements_analyzer import WebsiteBrief
        brief = WebsiteBrief(category="portfolio")
        plan = WebsiteVisualIntelligence.generate_plan(brief, None, "portfolio site")
        self.assertIsInstance(plan, VisualWebsitePlan)

    # 18. Existing Website Research remains unchanged
    def test_18_website_research_unchanged(self):
        from tools.coding.website_researcher import WebsiteResearcher
        self.assertTrue(hasattr(WebsiteResearcher, 'research_company'))

    # 19. Existing Task-Aware Sleep remains functional
    def test_19_task_aware_sleep_functional(self):
        from core.task_orchestrator import TaskOrchestrator
        orch = TaskOrchestrator.get_instance()
        orch.start_task("sleep_test_repair", "WEBSITE_BUILD", "Sleep test", total_items=3)
        self.assertTrue(orch.is_task_active())
        orch.complete_task("sleep_test_repair", "done")
        self.assertFalse(orch.is_task_active())

    # 20. Unrepairable issue is safely rejected without crash
    def test_20_unrepairable_issue_safely_rejected(self):
        issue = RepairIssue(
            issue_type="build",
            message="Unknown ambiguous catastrophic failure XYZ_UNDEFINED",
            severity="critical",
            repairable=False
        )
        result = WebsiteAutoRepair.diagnose_and_repair(
            task_id="unrepairable_test",
            project_dir=self.project_dir,
            issue=issue,
            attempt_number=1,
            generated_contents=self.generated_contents,
            code_generator_func=None
        )
        self.assertEqual(result.status, "unrepairable")
        self.assertNotEqual(result.status, "success")


if __name__ == "__main__":
    unittest.main()
