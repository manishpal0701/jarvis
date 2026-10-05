"""
tests/test_app_builder.py
Comprehensive Unit & Integration Test Suite for JARVIS App Builder (Phase 1 & Phase 2).
Tests actual behavior: brief merging, workspace isolation, Flutter/Node project creation,
command execution, auto-debugging loop, WebSocket event broadcasting, queue handoff, and persistence.
"""
import os
import shutil
import unittest
from tools.app_builder.app_manager import AppManager
from tools.app_builder.app_model import AppState, AppProject, AppBrief
from tools.app_builder.app_intent_router import AppIntentRouter
from tools.app_builder.app_brief_merger import AppBriefMerger
from tools.app_builder.app_development_planner import AppDevelopmentPlanner
from tools.app_builder.app_workspace_manager import AppWorkspaceManager, DATA_DIR, PROJECTS_PERSISTENCE_FILE
from tools.app_builder.node_generator import NodeProjectGenerator
from tools.app_builder.flutter_generator import FlutterProjectGenerator
from tools.app_builder.command_executor import AppCommandExecutor
from tools.app_builder.auto_debugger import AppAutoDebugger
from tools.app_builder.ide_interfaces import ConcreteFlutterAndroidStudioRunner, ConcreteNodeVSCodeRunner
from tools.app_builder.app_orchestrator import AppDevelopmentOrchestrator


class TestAppBuilderPhase2(unittest.TestCase):

    def setUp(self):
        """Reset AppManager singleton and clean up temporary test workspaces before each test."""
        self.app_manager = AppManager()
        self.app_manager.reset()
        self.test_workspace_root = os.path.join(os.getcwd(), "JARVIS App Projects Test")
        if os.path.exists(self.test_workspace_root):
            shutil.rmtree(self.test_workspace_root, ignore_errors=True)

    def tearDown(self):
        if os.path.exists(self.test_workspace_root):
            shutil.rmtree(self.test_workspace_root, ignore_errors=True)

    def test_01_app_project_creation(self):
        """1. App project creation via AppIntentRouter & AppManager."""
        cmd = "Jarvis ek Android app bana do."
        self.assertTrue(AppIntentRouter.is_app_build_intent(cmd))

        app = self.app_manager.create_app_project(initial_prompt=cmd)
        self.assertIsNotNone(app)
        self.assertEqual(app.status, AppState.WAITING_FOR_BRIEF)
        self.assertEqual(app.technology["frontend"], "Flutter")
        self.assertEqual(app.technology["backend"], "Node.js")

    def test_02_brief_collection_first_message(self):
        """2. Brief collection (first message parsing)."""
        app = self.app_manager.create_app_project(initial_prompt="Jarvis ek app bana do")
        updated = self.app_manager.update_app_brief(app.app_id, new_text="App ka naam Expense Tracker hai.")

        self.assertEqual(updated.brief.name, "Expense Tracker")
        self.assertEqual(updated.name, "Expense Tracker")
        self.assertEqual(updated.status, AppState.BRIEF_COLLECTING)

    def test_03_multi_message_brief_merging(self):
        """3. Multi-message brief merging (preserving name, features, design)."""
        app = self.app_manager.create_app_project(initial_prompt="Jarvis ek app bana do")
        self.app_manager.update_app_brief(app.app_id, new_text="App ka naam Expense Tracker hai.")

        msg_2 = "Isme login, add expense, categories aur dashboard reports hone chahiye."
        self.app_manager.update_app_brief(app.app_id, new_text=msg_2)

        msg_3 = "Dark blue theme rakhna."
        updated = self.app_manager.update_app_brief(app.app_id, new_text=msg_3)

        self.assertEqual(updated.brief.name, "Expense Tracker")
        self.assertTrue(len(updated.brief.features) >= 3)
        self.assertTrue(any("dark" in p.lower() for p in updated.brief.design_preferences))

    def test_04_brief_completeness(self):
        """4. Brief completeness determination."""
        empty_brief = AppBrief()
        sufficient, msg = AppBriefMerger.is_brief_sufficient(empty_brief)
        self.assertFalse(sufficient)

        filled_brief = AppBrief(
            name="Attendance App",
            features=["QR scan", "Leave request"],
            description="Attendance marking system"
        )
        sufficient, msg = AppBriefMerger.is_brief_sufficient(filled_brief)
        self.assertTrue(sufficient)

    def test_05_development_plan_generation(self):
        """5. Development plan generation (AppDevelopmentPlanner)."""
        brief = AppBrief(
            name="Fitness Tracker",
            features=["Workout tracking", "Calorie counter", "Login"],
            description="Fitness mobile application with Node.js backend"
        )
        plan = AppDevelopmentPlanner.generate_plan(brief)

        self.assertEqual(plan["app_name"], "Fitness Tracker")
        self.assertEqual(plan["domain"], "fitness")
        self.assertTrue(len(plan["flutter"]["screens"]) >= 4)
        self.assertTrue(len(plan["node"]["endpoints"]) >= 3)
        self.assertIn("express", plan["node"]["packages"])

    def test_06_workspace_creation(self):
        """6. Workspace creation under JARVIS App Projects/."""
        ws_mgr = AppWorkspaceManager(workspace_root=self.test_workspace_root)
        app = self.app_manager.create_app_project(name="TestApp")
        plan = AppDevelopmentPlanner.generate_plan(app.brief)

        res = ws_mgr.create_workspace(app, plan)
        self.assertTrue(os.path.exists(res["workspace_path"]))
        self.assertTrue(os.path.exists(res["frontend_path"]))
        self.assertTrue(os.path.exists(res["backend_path"]))
        self.assertTrue(os.path.exists(os.path.join(res["workspace_path"], "project.json")))
        self.assertTrue(os.path.exists(os.path.join(res["workspace_path"], "brief.json")))

    def test_07_flutter_project_creation(self):
        """7. Flutter project creation (files check)."""
        ws_mgr = AppWorkspaceManager(workspace_root=self.test_workspace_root)
        app = self.app_manager.create_app_project(name="FlutterApp")
        plan = AppDevelopmentPlanner.generate_plan(app.brief)
        ws_paths = ws_mgr.create_workspace(app, plan)

        created_files = FlutterProjectGenerator.generate_frontend(ws_paths["frontend_path"], plan)
        self.assertTrue(len(created_files) >= 8)
        self.assertTrue(os.path.exists(os.path.join(ws_paths["frontend_path"], "pubspec.yaml")))
        self.assertTrue(os.path.exists(os.path.join(ws_paths["frontend_path"], "lib", "main.dart")))
        self.assertTrue(os.path.exists(os.path.join(ws_paths["frontend_path"], "lib", "services", "api_service.dart")))

    def test_08_node_project_creation(self):
        """8. Node.js project creation (files check)."""
        ws_mgr = AppWorkspaceManager(workspace_root=self.test_workspace_root)
        app = self.app_manager.create_app_project(name="NodeApp")
        plan = AppDevelopmentPlanner.generate_plan(app.brief)
        ws_paths = ws_mgr.create_workspace(app, plan)

        created_files = NodeProjectGenerator.generate_backend(ws_paths["backend_path"], plan)
        self.assertTrue(len(created_files) >= 10)
        self.assertTrue(os.path.exists(os.path.join(ws_paths["backend_path"], "package.json")))
        self.assertTrue(os.path.exists(os.path.join(ws_paths["backend_path"], "src", "server.js")))
        self.assertTrue(os.path.exists(os.path.join(ws_paths["backend_path"], "src", "app.js")))

    def test_09_real_file_generation_and_verification(self):
        """9. Real file coding & existence verification."""
        ws_mgr = AppWorkspaceManager(workspace_root=self.test_workspace_root)
        app = self.app_manager.create_app_project(name="FileCheckApp")
        plan = AppDevelopmentPlanner.generate_plan(app.brief)
        ws_paths = ws_mgr.create_workspace(app, plan)

        f_files = FlutterProjectGenerator.generate_frontend(ws_paths["frontend_path"], plan)
        n_files = NodeProjectGenerator.generate_backend(ws_paths["backend_path"], plan)

        for path in f_files + n_files:
            self.assertTrue(os.path.exists(path), f"Generated file missing: {path}")
            self.assertTrue(os.path.getsize(path) > 0, f"Generated file empty: {path}")

    def test_10_command_execution(self):
        """10. Command execution layer."""
        ws_mgr = AppWorkspaceManager(workspace_root=self.test_workspace_root)
        app = self.app_manager.create_app_project(name="CmdApp")
        plan = AppDevelopmentPlanner.generate_plan(app.brief)
        ws_paths = ws_mgr.create_workspace(app, plan)
        NodeProjectGenerator.generate_backend(ws_paths["backend_path"], plan)

        res = AppCommandExecutor.execute("node --version", cwd=ws_paths["backend_path"], app_id=app.app_id)
        self.assertTrue(res["success"])
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("v", res["stdout"])

    def test_11_build_failure_handling(self):
        """11. Build failure handling on invalid command."""
        ws_mgr = AppWorkspaceManager(workspace_root=self.test_workspace_root)
        app = self.app_manager.create_app_project(name="FailApp")
        plan = AppDevelopmentPlanner.generate_plan(app.brief)
        ws_paths = ws_mgr.create_workspace(app, plan)

        res = AppCommandExecutor.execute("node nonexistent_script_xyz.js", cwd=ws_paths["backend_path"], app_id=app.app_id)
        self.assertFalse(res["success"])
        self.assertNotEqual(res["exit_code"], 0)

    def test_12_automatic_debugging_loop(self):
        """12. Automatic debugging loop (AppAutoDebugger)."""
        ws_mgr = AppWorkspaceManager(workspace_root=self.test_workspace_root)
        app = self.app_manager.create_app_project(name="AutoDebugApp")
        plan = AppDevelopmentPlanner.generate_plan(app.brief)
        ws_paths = ws_mgr.create_workspace(app, plan)
        NodeProjectGenerator.generate_backend(ws_paths["backend_path"], plan)

        # Execute node test suite check
        debug_res = AppAutoDebugger.verify_and_debug_backend(ws_paths["backend_path"], app_id=app.app_id)
        self.assertTrue(debug_res["success"])

    def test_13_websocket_progress_events(self):
        """13. WebSocket progress events emission."""
        events_received = []
        app = self.app_manager.create_app_project(name="WSEventApp")

        # Mock broadcast_event capture
        orig_broadcast = self.app_manager.broadcast_event
        self.app_manager.broadcast_event = lambda event_type, app_obj, message="", extra=None: events_received.append(event_type)

        try:
            self.app_manager.update_app_status(app.app_id, AppState.PLANNING)
            self.app_manager.update_app_status(app.app_id, AppState.CODING_FRONTEND)
            self.app_manager.update_app_status(app.app_id, AppState.COMPLETED)
        finally:
            self.app_manager.broadcast_event = orig_broadcast

        self.assertIn("app_planning", events_received)
        self.assertIn("app_frontend_started", events_received)
        self.assertIn("app_completed", events_received)

    def test_14_queue_behavior(self):
        """14. Secondary app queuing behavior."""
        app1 = self.app_manager.create_app_project(name="App1", initial_prompt="Jarvis app 1 bana do")
        app2 = self.app_manager.create_app_project(name="App2", initial_prompt="Jarvis app 2 bana do")

        self.assertEqual(self.app_manager.get_active_app().app_id, app1.app_id)
        queue = self.app_manager.get_queue()
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0].app_id, app2.app_id)

    def test_15_app_to_website_task_handoff(self):
        """15. App -> Website task queue handoff."""
        app1 = self.app_manager.create_app_project(name="App1", initial_prompt="Jarvis app 1 bana do")
        web_task = self.app_manager.create_app_project(name="WebTask", initial_prompt="3D animated website bana do", task_type="WEBSITE")

        self.assertEqual(len(self.app_manager.get_queue()), 1)
        self.assertEqual(self.app_manager.get_queue()[0].task_type, "WEBSITE")

    def test_16_persistence_and_recovery(self):
        """16. State persistence and restart recovery."""
        app = self.app_manager.create_app_project(name="PersistApp", initial_prompt="Jarvis app bana do")
        self.app_manager.update_app_brief(app.app_id, new_text="App ka naam PersistApp hai.")

        # Load from persistence file
        persisted = AppWorkspaceManager.load_state()
        self.assertIsNotNone(persisted["active_app"])
        self.assertEqual(persisted["active_app"].app_id, app.app_id)
        self.assertEqual(persisted["active_app"].brief.name, "PersistApp")


if __name__ == "__main__":
    unittest.main()
