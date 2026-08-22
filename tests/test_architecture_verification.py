import unittest
import os
import shutil
import tempfile
from tools.coding.code_assistant import CodeAssistant
from tools.coding.workspace_manager import WorkspaceManager
from tools.coding.protected_file_validator import ProtectedFileValidator
from tools.coding.path_validator import PathValidator
from tools.coding.filename_generator import FilenameGenerator

class TestArchitectureVerification(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.assistant = CodeAssistant()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_run_seven_required_generations(self):
        test_prompts = [
            "calculator",
            "snake game",
            "weather app",
            "todo app",
            "tic tac toe",
            "hospital management system",
            "student attendance app"
        ]

        ws = WorkspaceManager.get_instance()

        print("\n" + "=" * 70)
        print("PRODUCTION ARCHITECTURE VERIFICATION TEST RESULTS")
        print("=" * 70)

        for prompt in test_prompts:
            target_filename, lang, ext = self.assistant.detect_target_file(prompt, self.test_dir)
            _, protected_triggered = ProtectedFileValidator.protect(target_filename)

            code, saved_path = self.assistant.generate_code(prompt, project_dir=self.test_dir)

            file_exists = os.path.isfile(saved_path)
            with open(saved_path, "r", encoding="utf-8") if file_exists else None as f:
                disk_code = f.read() if f else ""

            rel_name = os.path.basename(saved_path)
            ws_code = ws.files_content.get(rel_name, "")
            streamed = bool(ws_code and len(ws_code) > 0 and ws_code == disk_code)
            browser_updated = bool(ws.status and ("Completed" in ws.status or "writing" in ws.state_class or "success" in ws.state_class))

            passed = file_exists and streamed and len(code) > 0 and not code.startswith("# Error")
            status_str = "PASS" if passed else "FAIL"

            print(f"Generated filename          : {target_filename}")
            print(f"Save location               : {saved_path}")
            print(f"Protected filename triggered?: {protected_triggered}")
            print(f"Workspace updated?          : {streamed}")
            print(f"Browser streamed?           : {browser_updated}")
            print(f"Result                      : {status_str}")
            print("-" * 70)

            self.assertTrue(passed, f"Generation failed for prompt: {prompt}")

    def test_protected_file_renaming(self):
        safe_main, main_protected = ProtectedFileValidator.protect("main.py")
        self.assertTrue(main_protected)
        self.assertEqual(safe_main, "generated_main.py")

        safe_config, config_protected = ProtectedFileValidator.protect("config.py")
        self.assertTrue(config_protected)
        self.assertEqual(safe_config, "generated_config.py")

    def test_path_traversal_prevention(self):
        with self.assertRaises(ValueError):
            PathValidator.validate_and_resolve(self.test_dir, "../../etc/passwd")

        with self.assertRaises(ValueError):
            PathValidator.validate_and_resolve(self.test_dir, "../outside_workspace.py")

    def test_filename_generator_generic_slugify(self):
        fn1 = FilenameGenerator.generate_filename("hospital management system")
        self.assertEqual(fn1, "hospital_management_system.py")

        fn2 = FilenameGenerator.generate_filename("bank management software")
        self.assertEqual(fn2, "bank_management_software.py")

        fn3 = FilenameGenerator.generate_filename("student attendance app")
        self.assertEqual(fn3, "student_attendance_app.py")

if __name__ == "__main__":
    unittest.main()
