import unittest
import os
import shutil
import tempfile
from main import is_coding_task
from tools.coding.code_parser import CodeParser
from tools.coding.code_validator import CodeValidator
from tools.coding.code_assistant import CodeAssistant
from tools.coding.workspace_manager import WorkspaceManager, find_free_port

class TestCodeWorkspaceArchitecture(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.assistant = CodeAssistant()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_a_python_calculator_intent(self):
        cmd = "ek python calculator bana do"
        self.assertTrue(is_coding_task(cmd))
        mode = self.assistant.classify_coding_mode(cmd)
        self.assertEqual(mode, "STANDALONE_CODE")
        rel, lang, ext = self.assistant.detect_target_file(cmd)
        self.assertEqual(lang, "python")
        self.assertEqual(ext, ".py")
        self.assertEqual(rel, "calculator.py")

    def test_b_javascript_calculator_intent(self):
        cmd = "javascript calculator bana do"
        self.assertTrue(is_coding_task(cmd))
        rel, lang, ext = self.assistant.detect_target_file(cmd)
        self.assertEqual(lang, "javascript")
        self.assertEqual(ext, ".js")
        self.assertEqual(rel, "calculator.js")

    def test_c_protected_files_protection(self):
        rel, lang, ext = self.assistant.detect_target_file("write main.py")
        self.assertEqual(rel, "generated_main.py")

        protected_renamed = self.assistant.protect_target_file("config.py")
        self.assertEqual(protected_renamed, "generated_config.py")

    def test_c_html_website_intent(self):
        cmd = "ek html website bana do"
        self.assertTrue(is_coding_task(cmd))
        rel, lang, ext = self.assistant.detect_target_file(cmd)
        self.assertEqual(lang, "html")
        self.assertEqual(ext, ".html")

    def test_d_existing_project_mode(self):
        cmd = "mere Flutter project mein calculator add karo"
        self.assertTrue(is_coding_task(cmd))
        mode = self.assistant.classify_coding_mode(cmd)
        self.assertEqual(mode, "PROJECT_MODIFICATION")

    def test_e_validator_rejects_flutter_code_for_python(self):
        flutter_hallucination = """
import 'package:flutter/material.dart';

class CalculatorApp extends StatelessWidget {
    @override
    Widget build(BuildContext context) {
        return Scaffold(body: Text("Calculator"));
    }
}
        """
        is_valid, err_msg = CodeValidator.validate(flutter_hallucination, "python")
        self.assertFalse(is_valid)
        self.assertIn("Dart/Flutter", err_msg)

    def test_f_validator_passes_valid_python_and_matches_disk(self):
        valid_python = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

if __name__ == '__main__':
    print("Calculator:", add(10, 5))
        """
        is_valid, err_msg = CodeValidator.validate(valid_python, "python")
        self.assertTrue(is_valid)

        ws = WorkspaceManager.get_instance()
        test_file = os.path.join(self.test_dir, "test_calc.py")
        
        ws.set_file_info("test_calc.py", "python")
        ws.set_final_code(valid_python.strip())
        
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(valid_python.strip())

        with open(test_file, "r", encoding="utf-8") as f:
            disk_content = f.read()

        self.assertEqual(ws.code_content, disk_content)

if __name__ == "__main__":
    unittest.main()
