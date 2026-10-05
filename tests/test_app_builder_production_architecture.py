"""
tests/test_app_builder_production_architecture.py
Unit test suite for Phase 8 JARVIS Production App Generation Architecture & Quality Gates.
Tests ApplicationSpecification, PlaceholderDetector, FeatureCoverageAnalyzer,
ProductionQualityGate, FlutterProjectGenerator, and NodeProjectGenerator.
"""
import os
import shutil
import tempfile
import unittest

from tools.app_builder.app_specification import ApplicationSpecification, AppSpecificationBuilder
from tools.app_builder.placeholder_detector import PlaceholderDetector
from tools.app_builder.feature_coverage_analyzer import FeatureCoverageAnalyzer
from tools.app_builder.production_quality_gate import ProductionQualityGate
from tools.app_builder.flutter_generator import FlutterProjectGenerator
from tools.app_builder.node_generator import NodeProjectGenerator


class TestAppBuilderProductionArchitecture(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="jarvis_test_app_")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_application_specification_builder(self):
        from tools.app_builder.app_model import AppBrief
        brief = AppBrief(name="JARVIS Music Player", features=["play_music", "playlists", "search_artist"])
        spec = AppSpecificationBuilder.from_brief(brief, self.test_dir)

        self.assertEqual(spec.app_name, "JARVIS Music Player")
        self.assertEqual(spec.domain, "music")
        self.assertGreaterEqual(len(spec.screens), 4)
        screen_names = [s["name"] for s in spec.screens]
        self.assertIn("HomeScreen", screen_names)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "app_build_spec.json")))

    def test_placeholder_detector(self):
        # Create clean file
        lib_dir = os.path.join(self.test_dir, "frontend", "lib")
        os.makedirs(lib_dir, exist_ok=True)
        clean_file = os.path.join(lib_dir, "home_screen.dart")
        with open(clean_file, "w", encoding="utf-8") as f:
            f.write("class HomeScreen extends StatelessWidget { Widget build(BuildContext c) { return Container(); } }")

        res_clean = PlaceholderDetector.scan_workspace(self.test_dir)
        self.assertFalse(res_clean["has_placeholders"])

        # Create file with forbidden placeholder string
        dirty_file = os.path.join(lib_dir, "stub_screen.dart")
        with open(dirty_file, "w", encoding="utf-8") as f:
            f.write("class StubScreen { Text text = Text('SplashScreen Component Ready'); }")

        res_dirty = PlaceholderDetector.scan_workspace(self.test_dir)
        self.assertTrue(res_dirty["has_placeholders"])
        self.assertGreaterEqual(res_dirty["count"], 1)

    def test_flutter_and_node_generators_zero_placeholders(self):
        frontend_dir = os.path.join(self.test_dir, "frontend")
        backend_dir = os.path.join(self.test_dir, "backend")
        plan = {"app_name": "JARVIS Music VIP", "domain": "music"}

        fl_files = FlutterProjectGenerator.generate_frontend(frontend_dir, plan)
        nd_files = NodeProjectGenerator.generate_backend(backend_dir, plan)

        self.assertGreater(len(fl_files), 5)
        self.assertGreater(len(nd_files), 5)

        # Scan workspace for placeholders
        p_res = PlaceholderDetector.scan_workspace(self.test_dir)
        self.assertFalse(p_res["has_placeholders"], f"Placeholders found in generated code: {p_res.get('matches')}")

    def test_feature_coverage_analyzer(self):
        frontend_dir = os.path.join(self.test_dir, "frontend")
        backend_dir = os.path.join(self.test_dir, "backend")
        plan = {"app_name": "JARVIS Weather App", "domain": "weather"}

        FlutterProjectGenerator.generate_frontend(frontend_dir, plan)
        NodeProjectGenerator.generate_backend(backend_dir, plan)

        from tools.app_builder.app_model import AppBrief
        brief = AppBrief(name="JARVIS Weather App", features=["forecast", "search_city"])
        spec = AppSpecificationBuilder.from_brief(brief, self.test_dir)

        report = FeatureCoverageAnalyzer.evaluate(self.test_dir, spec)
        self.assertGreater(report["passed_count"], 3)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "feature_coverage_report.json")))

    def test_production_quality_gate(self):
        frontend_dir = os.path.join(self.test_dir, "frontend")
        backend_dir = os.path.join(self.test_dir, "backend")
        plan = {"app_name": "JARVIS Music System", "domain": "music"}

        FlutterProjectGenerator.generate_frontend(frontend_dir, plan)
        NodeProjectGenerator.generate_backend(backend_dir, plan)

        # Write mock verification reports to simulate successful build & runtime verification
        with open(os.path.join(self.test_dir, "runtime_verification_report.json"), "w", encoding="utf-8") as f:
            import json
            json.dump({"status": "VERIFIED", "flutter": {"debug_build": "PASS"}, "node": {"server": "PASS"}}, f)

        with open(os.path.join(self.test_dir, "architecture_plan.json"), "w", encoding="utf-8") as f:
            import json
            json.dump(plan, f)

        with open(os.path.join(self.test_dir, "api_contract.json"), "w", encoding="utf-8") as f:
            import json
            json.dump({"endpoints": []}, f)

        from tools.app_builder.app_model import AppBrief
        brief = AppBrief(name="JARVIS Music System", features=["play_music"])
        spec = AppSpecificationBuilder.from_brief(brief, self.test_dir)

        gate_res = ProductionQualityGate.evaluate_production_quality(self.test_dir, spec)
        self.assertEqual(gate_res["overall_status"], "PASS")
        self.assertEqual(gate_res["gates"].get("PLACEHOLDER_DETECTION"), "PASS")
        self.assertEqual(gate_res["gates"].get("PRODUCTION_APP_READY"), "PASS")
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "production_quality_gate_report.json")))

    def test_task_domain_app_generation(self):
        frontend_dir = os.path.join(self.test_dir, "frontend")
        backend_dir = os.path.join(self.test_dir, "backend")
        plan = {"app_name": "JARVIS Task Manager Pro", "domain": "task"}

        fl_files = FlutterProjectGenerator.generate_frontend(frontend_dir, plan)
        nd_files = NodeProjectGenerator.generate_backend(backend_dir, plan)

        self.assertGreater(len(fl_files), 10)
        self.assertGreater(len(nd_files), 8)

        # Check key task domain frontend files
        task_provider_path = os.path.join(frontend_dir, "lib", "providers", "task_provider.dart")
        task_repo_path = os.path.join(frontend_dir, "lib", "repositories", "task_repository.dart")
        task_model_path = os.path.join(frontend_dir, "lib", "models", "task_model.dart")
        self.assertTrue(os.path.exists(task_provider_path), "task_provider.dart missing")
        self.assertTrue(os.path.exists(task_repo_path), "task_repository.dart missing")
        self.assertTrue(os.path.exists(task_model_path), "task_model.dart missing")

        # Check pubspec.yaml for flutter_riverpod
        pubspec_path = os.path.join(frontend_dir, "pubspec.yaml")
        with open(pubspec_path, "r", encoding="utf-8") as f:
            pubspec_content = f.read()
        self.assertIn("flutter_riverpod", pubspec_content)

        # Check key task domain backend files
        task_ctrl_path = os.path.join(backend_dir, "src", "controllers", "taskController.js")
        task_routes_path = os.path.join(backend_dir, "src", "routes", "taskRoutes.js")
        self.assertTrue(os.path.exists(task_ctrl_path), "taskController.js missing")
        self.assertTrue(os.path.exists(task_routes_path), "taskRoutes.js missing")

        # Scan workspace for placeholders
        p_res = PlaceholderDetector.scan_workspace(self.test_dir)
        self.assertFalse(p_res["has_placeholders"], f"Placeholders found in task app: {p_res.get('matches')}")


if __name__ == "__main__":
    unittest.main()

