import unittest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.coding.code_assistant import CodeAssistant
from tools.coding.website_technology_selector import WebsiteTechnologySelector
from tools.coding.website_planner import WebsiteProjectPlanner
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer, WebsiteCategory, WebsiteSubject

class TestCodeAssistantAPI(unittest.TestCase):

    def setUp(self):
        self.assistant = CodeAssistant()

    # --- Test 1: Method exists ---
    def test_01_method_exists(self):
        self.assertTrue(hasattr(CodeAssistant, "generate_code"), "CodeAssistant must have 'generate_code' method.")
        self.assertTrue(hasattr(CodeAssistant, "classify_coding_mode"), "CodeAssistant must have 'classify_coding_mode' method.")
        self.assertTrue(hasattr(CodeAssistant, "review_file"), "CodeAssistant must have 'review_file' method.")

    # --- Test 2: Existing caller compatibility ---
    def test_02_existing_caller_compatibility(self):
        task = "python calculator bana do"
        with patch.object(self.assistant, '_generate_standalone', return_value=("print('calc')", "main.py")):
            code, path = self.assistant.generate_code(task)
            self.assertEqual(code, "print('calc')")
            self.assertEqual(path, "main.py")

    # --- Test 3: Correct website pipeline delegation ---
    def test_03_correct_website_pipeline_delegation(self):
        task = "mere liye ek modern portfolio website bnao main ek python developer hun"
        with patch.object(self.assistant, 'build_website', return_value=("export default function App() {}", "src/App.tsx")) as mock_build:
            code, path = self.assistant.generate_code(task)
            mock_build.assert_called_once()
            self.assertEqual(code, "export default function App() {}")

    # --- Test 4: Standalone code delegation ---
    def test_04_standalone_delegation(self):
        task = "python script likho weather data ke liye"
        with patch.object(self.assistant, '_generate_standalone', return_value=("import requests", "main.py")) as mock_standalone:
            code, path = self.assistant.generate_code(task)
            mock_standalone.assert_called_once()
            self.assertEqual(code, "import requests")

    # --- Test 5: Project modification delegation ---
    def test_05_modify_delegation(self):
        task = "mere Jarvis project mein calculator add karo"
        with patch.object(self.assistant, 'modify_website', return_value=("<!-- updated -->", "index.html")) as mock_modify:
            code, path = self.assistant.generate_code(task)
            mock_modify.assert_called_once()
            self.assertEqual(code, "<!-- updated -->")

    # --- Test 6: Review file API ---
    def test_06_review_file_api(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def add(a, b):\n    return a + b\n")
            temp_path = f.name

        try:
            with patch.object(self.assistant.ai_manager, 'generate_response', return_value="ERRORS FOUND:\nNo critical issue found."):
                res = self.assistant.review_file(temp_path)
                self.assertIn("No critical issue found.", res)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # --- Test 7: Default website technology stack ---
    def test_07_default_website_technology_stack(self):
        cmd = "mere liye ek modern portfolio website bnao main ek python developer hun"
        tech = WebsiteTechnologySelector.detect_stack(cmd)
        self.assertTrue(tech.default_stack)
        self.assertEqual(tech.framework, "react")
        self.assertEqual(tech.language, "typescript")
        self.assertEqual(tech.styling, "tailwind")
        self.assertEqual(tech.build_system, "vite")

    # --- Test 8: Infrastructure files zero LLM calls ---
    def test_08_infrastructure_zero_llm_calls(self):
        brief = WebsiteRequirementsAnalyzer.extract_information(
            "portfolio website bana do",
            WebsiteCategory.PORTFOLIO,
            WebsiteSubject(name="Python Dev")
        )
        infra_files = {"package.json", "tsconfig.json", "vite.config.ts", "index.html", "src/main.tsx"}
        llm_called_files = []

        def mock_llm_gen(messages, lang, rel_path, *args, **kwargs):
            llm_called_files.append(rel_path)
            project_dir = kwargs.get("project_dir", None)
            code = "export default function App() { return <div>App</div>; }"
            if project_dir:
                from tools.coding.workspace_manager import WorkspaceManager
                WorkspaceManager.get_instance().write_workspace_file(project_dir, rel_path, code)
            return code

        with patch.object(self.assistant, '_generate_and_validate', side_effect=mock_llm_gen):
            with patch('tools.coding.workspace_manager.WorkspaceManager.open_workspace'):
                with patch('tools.coding.local_website_server.LocalWebsiteServer.start_preview', return_value=("http://127.0.0.1:5173", 5173)):
                    with patch('tools.coding.website_deployer.LocalPreviewDeployer.execute_production_build', return_value=(True, "")):
                        self.assistant.build_website("portfolio website bana do", brief=brief, open_browser=False)

        for infra_f in infra_files:
            self.assertNotIn(infra_f, llm_called_files, f"LLM was illegally invoked for infrastructure file: {infra_f}")

    # --- Test 9: UI files use LLM ---
    def test_09_ui_files_use_llm(self):
        brief = WebsiteRequirementsAnalyzer.extract_information(
            "portfolio website bana do",
            WebsiteCategory.PORTFOLIO,
            WebsiteSubject(name="Python Dev")
        )
        llm_called_files = []

        def mock_llm_gen(messages, lang, rel_path, *args, **kwargs):
            llm_called_files.append(rel_path)
            project_dir = kwargs.get("project_dir", None)
            if lang == "css":
                code = '@import "tailwindcss";'
            else:
                code = "export default function App() { return <div>App</div>; }"
            if project_dir:
                from tools.coding.workspace_manager import WorkspaceManager
                WorkspaceManager.get_instance().write_workspace_file(project_dir, rel_path, code)
            return code

        with patch('tools.coding.workspace_manager.WorkspaceManager.open_workspace'):
            with patch('tools.coding.local_website_server.LocalWebsiteServer.start_preview', return_value=("http://127.0.0.1:5173", 5173)):
                with patch('tools.coding.website_deployer.LocalPreviewDeployer.execute_production_build', return_value=(True, "")):
                    code, entry_path = self.assistant.build_website("portfolio website bana do", brief=brief, open_browser=False)

        project_dir = os.path.dirname(os.path.dirname(entry_path)) if "src" in entry_path else os.path.dirname(entry_path)
        self.assertTrue(os.path.isfile(os.path.join(project_dir, "src", "App.tsx")), "src/App.tsx physically generated")
        self.assertTrue(os.path.isfile(os.path.join(project_dir, "src", "index.css")), "src/index.css physically generated")

    # --- Test 10: No old Vanilla pipeline for default stack ---
    def test_10_no_old_vanilla_pipeline_for_default_stack(self):
        task = "modern portfolio bana do"
        plan = WebsiteProjectPlanner.plan_project(task)
        paths = [f.path for f in plan.files]

        self.assertEqual(plan.framework, "react")
        self.assertIn("package.json", paths)
        self.assertIn("src/App.tsx", paths)
        self.assertNotIn("script.js", paths)

    # --- Test 11: AIResponseManager generate_response integration ---
    def test_11_ai_manager_generate_response_integration(self):
        with patch.object(self.assistant.ai_manager, 'generate_response_token_stream', return_value=iter(["export default function App() { return <div>App</div>; }"])) as mock_gen:
            code = self.assistant._generate_and_validate([{"role": "user", "content": "hi"}], "tsx", "src/App.tsx", stream_to_ws=False)
            mock_gen.assert_called_once()
            self.assertIn("export default function App", code)
            self.assertFalse(hasattr(self.assistant.ai_manager, "generate_response_token_streaming"), "AIResponseManager must not have fake generate_response_token_streaming method.")

    # --- Test 12: React TSX document wrapper rejection ---
    def test_12_react_tsx_document_wrapper_rejection(self):
        from tools.coding.code_validator import CodeValidator
        bad_tsx = "<html><head><title>App</title></head><body><div>Hello</div></body></html>"
        is_valid, err = CodeValidator.validate_tsx(bad_tsx)
        self.assertFalse(is_valid)
        self.assertIn("Contains HTML document wrapper tag", err)

    # --- Test 13: Tailwind v4 undefined custom utility rejection ---
    def test_13_tailwind_v4_undefined_utility_rejection(self):
        from tools.coding.code_validator import CodeValidator
        bad_tsx = "export default function App() { return <div className='bg-primary-color text-white'>App</div>; }"
        is_valid, err = CodeValidator.validate_tsx(bad_tsx)
        self.assertFalse(is_valid)
        self.assertIn("undefined custom utility class", err)

        bad_css = "@import 'tailwindcss'; .custom { @apply bg-primary-color; }"
        is_css_valid, css_err = CodeValidator.validate_css(bad_css)
        self.assertFalse(is_css_valid)
        self.assertIn("undefined custom utility class", css_err)

    # --- Test 14: Direct workspace file write test ---
    def test_14_direct_workspace_file_write(self):
        from tools.coding.workspace_manager import WorkspaceManager
        ws = WorkspaceManager.get_instance()
        with tempfile.TemporaryDirectory() as temp_dir:
            test_rel = "src/components/Test.tsx"
            test_content = "export default function Test() { return <div>Test</div>; }"
            full_path = ws.write_workspace_file(temp_dir, test_rel, test_content)

            self.assertTrue(os.path.isfile(full_path), "File must physically exist on disk.")
            with open(full_path, "r", encoding="utf-8") as f:
                disk_text = f.read()
            self.assertEqual(disk_text, test_content, "Disk content must match written content exactly.")

    # --- Test 15: Streaming event order regression ---
    def test_15_streaming_regression(self):
        from tools.coding.workspace_manager import WorkspaceManager
        ws = WorkspaceManager.get_instance()
        broadcast_events = []

        def mock_broadcast(data):
            broadcast_events.append(data.get("type"))

        with patch.object(ws, '_broadcast', side_effect=mock_broadcast):
            with tempfile.TemporaryDirectory() as temp_dir:
                ws.stream_file_start("src/App.tsx")
                ws.write_workspace_file(temp_dir, "src/App.tsx", "export default function App() {}")

        self.assertIn("file_start", broadcast_events)
        self.assertIn("file_end", broadcast_events)
        start_idx = broadcast_events.index("file_start")
        end_idx = broadcast_events.index("file_end")
        self.assertLess(start_idx, end_idx, "file_start must precede file_end.")

    # --- Test 16: Full website workspace disk E2E verification ---
    def test_16_full_website_workspace_disk_e2e(self):
        cmd = "mera ek modern portfolio website banaa do main ek python developer hun"
        brief = WebsiteRequirementsAnalyzer.extract_information(
            cmd,
            WebsiteCategory.PORTFOLIO,
            WebsiteSubject(name="Python Dev")
        )

        def mock_llm_gen(messages, lang, rel_path, *args, **kwargs):
            from tools.coding.workspace_manager import WorkspaceManager
            ws = WorkspaceManager.get_instance()
            project_dir = kwargs.get("project_dir", None)
            if lang == "css":
                content = '@import "tailwindcss"; body { background-color: #0f172a; }'
            else:
                content = f"export default function Component_{rel_path.replace('/', '_').replace('.', '_')}() {{ return <section className='min-h-screen bg-slate-900 text-white p-8'><h1>Python Developer Portfolio Section</h1><p>Projects, Skills, Experience</p></section>; }}"
            if project_dir:
                ws.write_workspace_file(project_dir, rel_path, content)
            return content

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(self.assistant, '_generate_and_validate', side_effect=mock_llm_gen):
                with patch('tools.coding.workspace_manager.WorkspaceManager.open_workspace'):
                    with patch('tools.coding.local_website_server.LocalWebsiteServer.start_preview', return_value=("http://127.0.0.1:5173", 5173)):
                        with patch('tools.coding.website_deployer.LocalPreviewDeployer.execute_production_build', return_value=(True, "")):
                            code, entry_path = self.assistant.build_website(cmd, project_dir=temp_dir, brief=brief, open_browser=False)
                            output_dir = os.path.dirname(os.path.dirname(entry_path))

            expected_files = [
                "package.json", "tsconfig.json", "vite.config.ts", "index.html", "src/main.tsx",
                "src/App.tsx", "src/index.css"
            ]
            for ef in expected_files:
                f_path = os.path.join(output_dir, ef)
                self.assertTrue(os.path.isfile(f_path), f"File physically missing from disk: {ef}")
                self.assertGreater(os.path.getsize(f_path), 0, f"File on disk is empty: {ef}")

if __name__ == "__main__":
    unittest.main()
