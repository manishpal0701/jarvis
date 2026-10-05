import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.coding.code_assistant import CodeAssistant
from tools.coding.code_validator import CodeValidator
from tools.coding.workspace_manager import WorkspaceManager
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer, WebsiteCategory, WebsiteSubject
from tools.coding.website_project_templates import WebsiteProjectTemplates
from tools.coding.website_deployer import LocalPreviewDeployer
from ai.ai_response_manager import AIResponseManager

class TestCodeAssistantRuntime(unittest.TestCase):

    def setUp(self):
        self.assistant = CodeAssistant()

    # --- 1. AIResponseManager available methods audit ---
    def test_01_ai_response_manager_methods_audit(self):
        ai_mgr = AIResponseManager()
        self.assertTrue(hasattr(ai_mgr, "generate_response"), "AIResponseManager must have generate_response method.")
        self.assertTrue(hasattr(ai_mgr, "generate_response_streaming"), "AIResponseManager must have generate_response_streaming method.")
        print("[1. AIResponseManager API Audit PASSED]")

    # --- 2. No call to non-existent generate_response_token_streaming ---
    def test_02_no_nonexistent_token_streaming_method(self):
        ai_mgr = AIResponseManager()
        self.assertFalse(hasattr(ai_mgr, "generate_response_token_streaming"), "AIResponseManager must NOT have fake generate_response_token_streaming method.")
        print("[2. No Non-existent Token Streaming Method PASSED]")

    # --- 3. generate_code routing test ---
    def test_03_generate_code_routing(self):
        with patch.object(self.assistant, 'build_website', return_value=("code", "path")) as mock_build:
            self.assistant.generate_code("modern portfolio website bana do")
            mock_build.assert_called_once()
        print("[3. CodeAssistant generate_code Routing PASSED]")

    # --- 4 & 5 & 7 & 8 & 9. Website build creates actual files & workspace receives content ---
    def test_04_05_07_08_09_workspace_actual_files_and_content(self):
        cmd = "mera ek modern portfolio website banaa do main ek python developer hun"
        brief = WebsiteRequirementsAnalyzer.extract_information(cmd, WebsiteCategory.PORTFOLIO, WebsiteSubject(name="Python Dev"))
        ws = WorkspaceManager.get_instance()

        def mock_ui_gen(messages, lang, rel_path, *args, **kwargs):
            project_dir = kwargs.get("project_dir", None)
            if lang == "css":
                code = '@import "tailwindcss"; body { background-color: #0f172a; color: #f8fafc; }'
            else:
                code = f"export default function Component_{rel_path.replace('/', '_').replace('.', '_')}() {{ return <section className='min-h-screen bg-slate-900 text-white p-8'><h1>Python Dev Section - {rel_path}</h1><p>Hero, About, Skills, Projects, Experience, Contact</p></section>; }}"
            if project_dir:
                ws.write_workspace_file(project_dir, rel_path, code)
            return code

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(self.assistant, '_generate_and_validate', side_effect=mock_ui_gen):
                with patch('tools.coding.workspace_manager.WorkspaceManager.open_workspace'):
                    with patch('tools.coding.local_website_server.LocalWebsiteServer.start_preview', return_value=("http://127.0.0.1:5173", 5173)):
                        with patch('tools.coding.website_deployer.LocalPreviewDeployer.execute_production_build', return_value=(True, "")):
                            code, entry_path = self.assistant.build_website(cmd, project_dir=temp_dir, brief=brief, open_browser=False)

            output_dir = os.path.dirname(os.path.dirname(entry_path)) if "src" in entry_path else os.path.dirname(entry_path)
            expected_files = ["package.json", "tsconfig.json", "vite.config.ts", "index.html", "src/main.tsx", "src/App.tsx", "src/index.css"]

            for ef in expected_files:
                f_path = os.path.join(output_dir, ef)
                self.assertTrue(os.path.isfile(f_path), f"File physically missing on disk: {ef}")
                self.assertGreater(os.path.getsize(f_path), 0, f"File on disk is empty: {ef}")

        print("[4, 5, 7, 8, 9. Workspace Files & Content Verification PASSED]")

    # --- 6. STREAM_FILE_START and STREAM_FILE_END pairing ---
    def test_06_stream_start_end_pairing(self):
        ws = WorkspaceManager.get_instance()
        events = []

        def mock_broadcast(data):
            events.append(data.get("type"))

        with patch.object(ws, '_broadcast', side_effect=mock_broadcast):
            with tempfile.TemporaryDirectory() as temp_dir:
                ws.stream_file_start("src/App.tsx")
                ws.write_workspace_file(temp_dir, "src/App.tsx", "export default function App() {}")

        self.assertEqual(events.count("file_start"), 1)
        self.assertEqual(events.count("file_end"), 1)
        self.assertLess(events.index("file_start"), events.index("file_end"))
        print("[6. STREAM_FILE_START / END Pairing PASSED]")

    # --- 10. Rejection of undefined Tailwind @apply utilities ---
    def test_10_tailwind_v4_undefined_utility_rejection(self):
        bad_css = "@import 'tailwindcss'; .btn { @apply bg-primary-color; }"
        is_valid, err = CodeValidator.validate_css(bad_css)
        self.assertFalse(is_valid)
        self.assertIn("undefined custom utility class", err)

        bad_tsx = "export default function App() { return <div className='bg-primary-color'>App</div>; }"
        is_tsx_valid, tsx_err = CodeValidator.validate_tsx(bad_tsx)
        self.assertFalse(is_tsx_valid)
        self.assertIn("undefined custom utility class", tsx_err)
        print("[10. Tailwind v4 Undefined Utility Rejection PASSED]")

    # --- 11. Dependency Closure Validation (Unresolved external imports) ---
    def test_11_dependency_closure_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pkg_json = {
                "name": "test-app",
                "dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"},
                "devDependencies": {"typescript": "^5.0.0", "vite": "^5.0.0"}
            }
            with open(os.path.join(temp_dir, "package.json"), "w", encoding="utf-8") as f:
                json.dump(pkg_json, f)

            src_dir = os.path.join(temp_dir, "src")
            os.makedirs(src_dir, exist_ok=True)

            # File imports unlisted 'react-router-dom' -> FAIL
            with open(os.path.join(src_dir, "App.tsx"), "w", encoding="utf-8") as f:
                f.write("import { BrowserRouter } from 'react-router-dom'; export default function App() { return <BrowserRouter />; }")

            is_valid, err = CodeValidator.validate_dependency_closure(temp_dir)
            self.assertFalse(is_valid)
            self.assertIn("DEPENDENCY_ERROR", err)
            self.assertIn("react-router-dom", err)

            # Fix import -> PASS
            with open(os.path.join(src_dir, "App.tsx"), "w", encoding="utf-8") as f:
                f.write("import React from 'react'; export default function App() { return <div>App</div>; }")

            is_valid_2, err_2 = CodeValidator.validate_dependency_closure(temp_dir)
            self.assertTrue(is_valid_2, f"Dependency closure failed unexpectedly: {err_2}")
        print("[11. Dependency Closure Validation PASSED]")

    # --- 12 & 13 & 14 & 15. Real npm build, dist creation & BUILD_SUCCESS logic ---
    def test_12_13_14_15_real_npm_build_and_dist_creation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "package.json"), "w", encoding="utf-8") as f:
                f.write(WebsiteProjectTemplates.generate_package_json("Test App", "test_app"))
            with open(os.path.join(temp_dir, "tsconfig.json"), "w", encoding="utf-8") as f:
                f.write(WebsiteProjectTemplates.generate_tsconfig())
            with open(os.path.join(temp_dir, "vite.config.ts"), "w", encoding="utf-8") as f:
                f.write(WebsiteProjectTemplates.generate_vite_config())
            with open(os.path.join(temp_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(WebsiteProjectTemplates.generate_index_html("Test App"))
            os.makedirs(os.path.join(temp_dir, "src"), exist_ok=True)
            with open(os.path.join(temp_dir, "src", "main.tsx"), "w", encoding="utf-8") as f:
                f.write(WebsiteProjectTemplates.generate_main_tsx())
            with open(os.path.join(temp_dir, "src", "App.tsx"), "w", encoding="utf-8") as f:
                f.write("export default function App() { return <div className='p-8 bg-slate-900 text-white'><h1>Runtime Test</h1></div>; }")
            with open(os.path.join(temp_dir, "src", "index.css"), "w", encoding="utf-8") as f:
                f.write("@tailwind base;\n@tailwind components;\n@tailwind utilities;\n")

            is_ok, err = LocalPreviewDeployer.execute_production_build(temp_dir)
            self.assertTrue(is_ok, f"Real npm build failed: {err}")

            dist_index = os.path.join(temp_dir, "dist", "index.html")
            dist_assets = os.path.join(temp_dir, "dist", "assets")

            self.assertTrue(os.path.isfile(dist_index), "dist/index.html must exist after production build.")
            self.assertTrue(os.path.isdir(dist_assets), "dist/assets directory must exist after production build.")
            self.assertGreater(len(os.listdir(dist_assets)), 0, "dist/assets must contain compiled JS/CSS files.")

        print("[12, 13, 14, 15. Real npm Build Gate & dist Artifact Verification PASSED]")

if __name__ == "__main__":
    unittest.main()
