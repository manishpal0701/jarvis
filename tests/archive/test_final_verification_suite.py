import unittest
import os
import shutil
import tempfile
from tools.coding.code_assistant import CodeAssistant
from tools.coding.workspace_manager import WorkspaceManager
from tools.coding.filename_generator import FilenameGenerator
from tools.coding.protected_file_validator import ProtectedFileValidator
from tools.coding.path_validator import PathValidator

class TestFinalVerificationSuite(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.assistant = CodeAssistant()
        self.ws = WorkspaceManager.get_instance()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _verify_standalone_generation(self, prompt: str, expected_filename: str) -> dict:
        target_filename, lang, ext = self.assistant.detect_target_file(prompt, self.test_dir)
        code, saved_path = self.assistant.generate_code(prompt, project_dir=self.test_dir)

        file_exists = os.path.isfile(saved_path)
        rel_name = os.path.basename(saved_path)

        ws_code = self.ws.files_content.get(rel_name, "")
        code_matches = bool(ws_code and len(ws_code) > 0 and ws_code == code)
        status_updated = bool(self.ws.status and ("Completed" in self.ws.status or "writing" in self.ws.state_class or "success" in self.ws.state_class))

        passed = file_exists and code_matches and len(code) > 0 and not code.startswith("# Error") and target_filename == expected_filename

        return {
            "target_filename": target_filename,
            "saved_path": saved_path,
            "file_exists": file_exists,
            "ws_switched": self.ws.file_path == target_filename,
            "live_code_streaming": code_matches,
            "status_updated": status_updated,
            "passed": passed
        }

    def test_1_python_calculator(self):
        prompt = "ek python calculator program banaa kar"
        res = self._verify_standalone_generation(prompt, "calculator.py")
        self.assertTrue(res["passed"], f"Test 1 Failed: {res}")

    def test_2_weather_app(self):
        prompt = "weather app"
        res = self._verify_standalone_generation(prompt, "weather_app.py")
        self.assertTrue(res["passed"], f"Test 2 Failed: {res}")

    def test_3_snake_game(self):
        prompt = "snake game"
        res = self._verify_standalone_generation(prompt, "snake_game.py")
        self.assertTrue(res["passed"], f"Test 3 Failed: {res}")

    def test_4_modern_portfolio_website(self):
        prompt = "modern portfolio website"
        from tools.coding.website_planner import WebsiteProjectPlanner
        plan = WebsiteProjectPlanner.plan_project(prompt, self.test_dir)
        paths = [f.path for f in plan.files]

        self.assertIn("package.json", paths)
        self.assertIn("index.html", paths)
        self.assertIn("src/App.tsx", paths)
        self.assertIn("src/main.tsx", paths)

    def test_5_malicious_filenames_and_paths(self):
        # 1. Protected Files
        safe_main, main_protected = ProtectedFileValidator.protect("main.py")
        self.assertTrue(main_protected)
        self.assertEqual(safe_main, "generated_main.py")

        safe_config, config_protected = ProtectedFileValidator.protect("config.py")
        self.assertTrue(config_protected)
        self.assertEqual(safe_config, "generated_config.py")

        safe_wm, wm_protected = ProtectedFileValidator.protect("workspace_manager.py")
        self.assertTrue(wm_protected)
        self.assertEqual(safe_wm, "generated_workspace_manager.py")

        # 2. Path Traversal Boundary Attacks
        with self.assertRaises(ValueError):
            PathValidator.validate_and_resolve(self.test_dir, "../../main.py")

        with self.assertRaises(ValueError):
            PathValidator.validate_and_resolve(self.test_dir, "../../../Windows/System32/test.py")

    def test_6_browser_reconnect_init_payload(self):
        self.ws.files_content["test.py"] = "print('Hello Workspace')"
        self.ws.set_file_info("test.py", "python")
        self.ws.set_status("Jarvis is ready", "writing")

        # Simulating fresh EventSource init payload calculation
        current_code = self.ws.files_content.get(self.ws.file_path, self.ws.code_content)
        init_data = {
            "type": "init",
            "file_path": self.ws.file_path,
            "language": self.ws.language,
            "status": self.ws.status,
            "state": self.ws.state_class,
            "code": current_code,
            "project_files": self.ws.project_files,
            "all_files": self.ws.files_content
        }

        self.assertEqual(init_data["file_path"], "test.py")
        self.assertEqual(init_data["code"], "print('Hello Workspace')")
        self.assertIn("test.py", init_data["all_files"])

if __name__ == "__main__":
    unittest.main()
