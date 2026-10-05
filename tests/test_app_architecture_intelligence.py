"""
tests/test_app_architecture_intelligence.py
Phase 3 Unit Test Suite — App Understanding & Architecture Intelligence.
Tests all 14 mandatory scenarios:
1. Simple app request (Calculator)
2. Complex app request (Banking / E-Commerce / Expense Manager)
3. Multi-message brief merging
4. Missing critical requirement detection (NEEDS_CLARIFICATION)
5. Automatic sensible default inference (READY)
6. Screen generation details
7. API contract generation
8. Database plan generation
9. Flutter plan generation
10. Node plan generation
11. Reference / design metadata preservation
12. Plan persistence (all 6 JSON files created)
13. Requirement update invalidation & hash change
14. Architecture consistency
"""
import os
import shutil
import unittest
from tools.app_builder.app_model import AppProject, AppBrief, AppState
from tools.app_builder.app_manager import AppManager
from tools.app_builder.app_requirements_analyzer import AppRequirementsAnalyzer, MissingRequirementDetector
from tools.app_builder.architecture_planner import ArchitecturePlanner
from tools.app_builder.app_development_planner import AppDevelopmentPlanner
from tools.app_builder.app_workspace_manager import AppWorkspaceManager
from tools.app_builder.app_orchestrator import AppDevelopmentOrchestrator


class TestAppArchitectureIntelligence(unittest.TestCase):

    def setUp(self):
        self.app_mgr = AppManager()
        self.app_mgr.reset()

    def tearDown(self):
        self.app_mgr.reset()

    # 1. Simple app request
    def test_01_simple_app_request(self):
        brief = AppBrief(name="CalculatorApp", description="Simple math calculator", features=["Add", "Subtract", "Multiply"])
        plan = AppDevelopmentPlanner.generate_plan(brief, app_id="test_simple")
        self.assertEqual(plan["domain"], "calculator")
        self.assertFalse(plan["app_metadata"]["needs_backend"])
        self.assertEqual(len(plan["screens"]), 1)

    # 2. Complex app request
    def test_02_complex_app_request(self):
        brief = AppBrief(
            name="FinTrack Pro",
            description="Expense tracking app with budget limits and category reports",
            features=["Login", "Add Expense", "Category Filter", "Monthly Analytics Report"],
            authentication="JWT Auth"
        )
        plan = AppDevelopmentPlanner.generate_plan(brief, app_id="test_complex")
        self.assertEqual(plan["domain"], "expense")
        self.assertTrue(plan["app_metadata"]["needs_backend"])
        self.assertGreaterEqual(len(plan["screens"]), 5)
        self.assertTrue(any(e["path"] == "/api/expenses" for e in plan["api_contract"]["endpoints"]))

    # 3. Multi-message brief merging
    def test_03_multi_message_brief(self):
        app_proj = self.app_mgr.create_app_project(initial_prompt="Jarvis ek Expense app bana do")
        self.app_mgr.update_app_brief(app_proj.app_id, new_text="App ka naam Expense Manager hai.")
        updated = self.app_mgr.update_app_brief(app_proj.app_id, new_text="Isme login, category analytics, and monthly reports feature honi chahiye.")
        
        self.assertEqual(updated.name, "Expense Manager")
        self.assertTrue(any("login" in f.lower() for f in updated.brief.features))

    # 4. Missing critical requirement detection (NEEDS_CLARIFICATION)
    def test_04_missing_critical_requirement(self):
        ambiguous_brief = AppBrief(name="App", description="")
        analyzed = AppRequirementsAnalyzer.analyze(ambiguous_brief)
        readiness = MissingRequirementDetector.check_requirements(analyzed, ambiguous_brief)
        
        self.assertEqual(readiness["status"], "NEEDS_CLARIFICATION")
        self.assertGreater(len(readiness["critical_questions"]), 0)

    # 5. Automatic sensible default inference (READY)
    def test_05_sensible_defaults_inference(self):
        calc_brief = AppBrief(name="QuickCalc", description="Math utility", features=["Calculator"])
        analyzed = AppRequirementsAnalyzer.analyze(calc_brief)
        readiness = MissingRequirementDetector.check_requirements(analyzed, calc_brief)
        
        self.assertEqual(readiness["status"], "READY")
        self.assertIn("auth", readiness["inferred_defaults"])

    # 6. Screen generation details
    def test_06_screen_generation(self):
        brief = AppBrief(name="Tasker", description="Todo list app", features=["Create Task", "List Tasks"])
        plan = AppDevelopmentPlanner.generate_plan(brief, app_id="test_screens")
        screens = plan["screens"]
        
        dashboard_screen = next((s for s in screens if s["id"] == "dashboard_screen"), None)
        self.assertIsNotNone(dashboard_screen)
        self.assertIn("route", dashboard_screen)
        self.assertIn("ui_components", dashboard_screen)
        self.assertIn("state_required", dashboard_screen)

    # 7. API contract generation
    def test_07_api_contract_generation(self):
        contract = ArchitecturePlanner.generate_api_contract("ExpenseManager", "expense", needs_backend=True)
        self.assertIn("endpoints", contract)
        endpoints = contract["endpoints"]
        login_ep = next((e for e in endpoints if e["path"] == "/api/auth/login"), None)
        self.assertIsNotNone(login_ep)
        self.assertEqual(login_ep["method"], "POST")

    # 8. Database plan generation
    def test_08_database_plan_generation(self):
        db_plan = ArchitecturePlanner.generate_database_plan("ExpenseManager", "expense", needs_backend=True)
        self.assertIn("entities", db_plan)
        entities = db_plan["entities"]
        user_entity = next((e for e in entities if e["name"] == "User"), None)
        self.assertIsNotNone(user_entity)
        self.assertTrue(any(f["name"] == "email" for f in user_entity["fields"]))

    # 9. Flutter plan generation
    def test_09_flutter_plan_generation(self):
        flutter_plan = ArchitecturePlanner.generate_flutter_plan("ExpenseManager", "expense", [], {})
        self.assertIn("folder_structure", flutter_plan)
        self.assertIn("providers", flutter_plan)
        self.assertIn("dependencies", flutter_plan)
        self.assertIn("http", flutter_plan["dependencies"])

    # 10. Node plan generation
    def test_10_node_plan_generation(self):
        node_plan = ArchitecturePlanner.generate_node_plan("ExpenseManager", "expense", {}, {}, needs_backend=True)
        self.assertIn("express_structure", node_plan)
        self.assertIn("routes", node_plan)
        self.assertIn("middleware", node_plan)
        self.assertIn("cors", node_plan["middleware"])

    # 11. Reference / design metadata preservation
    def test_11_design_reference_preservation(self):
        ref_metadata = [{"url": "https://dribbble.com/shots/123", "type": "image", "notes": "Dark neon accent"}]
        brief = AppBrief(name="RefApp", description="App with custom design", references=ref_metadata, ui_ux={"colors": ["#1A1A1A", "#00FFCC"]})
        analyzed = AppRequirementsAnalyzer.analyze(brief)
        ui_plan = ArchitecturePlanner.generate_ui_design_plan(analyzed["ui_design_requirements"])
        
        self.assertEqual(ui_plan["references"], ref_metadata)
        self.assertEqual(ui_plan["color_system"]["background"], "#1A1A1A")

    # 12. Plan persistence (All 6 JSON files created in workspace)
    def test_12_plan_persistence(self):
        app_proj = self.app_mgr.create_app_project(initial_prompt="Jarvis ek Expense Manager app bana do")
        self.app_mgr.update_app_brief(app_proj.app_id, new_text="Features: login and expense tracking.")
        
        orchestrator = AppDevelopmentOrchestrator()
        orchestrator.execute_pipeline(app_proj)
        
        workspace_path = app_proj.workspace_path
        self.assertIsNotNone(workspace_path)
        self.assertTrue(os.path.exists(workspace_path))
        
        expected_files = [
            "brief.json",
            "architecture_plan.json",
            "flutter_plan.json",
            "node_plan.json",
            "api_contract.json",
            "database_plan.json"
        ]
        for f in expected_files:
            file_path = os.path.join(workspace_path, f)
            self.assertTrue(os.path.exists(file_path), f"Missing persisted plan file: {f}")

    # 13. Requirement update invalidation & hash change
    def test_13_requirement_invalidation(self):
        app_proj = self.app_mgr.create_app_project(initial_prompt="Jarvis ek Calculator app bana do")
        plan1 = AppDevelopmentPlanner.generate_plan(app_proj.brief, app_id=app_proj.app_id)
        app_proj.development_plan = plan1
        hash1 = plan1["architecture_hash"]
        
        # Update brief to add expense management
        self.app_mgr.update_app_brief(app_proj.app_id, new_text="Change app to Expense Manager with backend login and database")
        plan2 = app_proj.development_plan
        hash2 = plan2["architecture_hash"]
        
        self.assertNotEqual(hash1, hash2)
        self.assertEqual(plan2["brief_version"], 2)

    # 14. Architecture consistency across Flutter and Node
    def test_14_architecture_consistency(self):
        brief = AppBrief(name="SyncApp", description="Expense tracker app", features=["Login", "Expenses"])
        plan = AppDevelopmentPlanner.generate_plan(brief, app_id="test_consistency")
        
        api_endpoints = [e["path"] for e in plan["api_contract"]["endpoints"]]
        node_routes = plan["node_plan"]["routes"]
        
        self.assertIn("/api/auth/login", api_endpoints)
        self.assertIn("authRoutes.js", node_routes)


if __name__ == "__main__":
    unittest.main()
