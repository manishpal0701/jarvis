import unittest
import os
import sys
import json
import tempfile
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.coding.website_project_templates import WebsiteProjectTemplates
from tools.coding.website_technology_selector import WebsiteTechnologySelector
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer, WebsiteCategory, WebsiteSubject, WebsiteBrief
from tools.coding.website_planner import WebsiteProjectPlanner
from tools.coding.code_validator import CodeValidator
from tools.coding.code_assistant import CodeAssistant
from tools.coding.website_deployer import LocalPreviewDeployer
from tools.coding.website_session_manager import WebsiteSessionManager, WebsiteSessionState

class TestWebsitePipelineFix(unittest.TestCase):

    def setUp(self):
        self.session_mgr = WebsiteSessionManager.get_instance()
        self.session_mgr.reset_session()

    # --- 1. ZERO-LLM INFRASTRUCTURE GENERATION TEST ---

    def test_01_zero_llm_infrastructure_generation(self):
        assistant = CodeAssistant()
        brief = WebsiteRequirementsAnalyzer.extract_information(
            "portfolio website bana do",
            WebsiteCategory.PORTFOLIO,
            WebsiteSubject(name="Manish")
        )
        plan = WebsiteProjectPlanner.plan_project("portfolio website bana do", brief=brief)

        infra_files = {"package.json", "tsconfig.json", "vite.config.ts", "index.html", "src/main.tsx"}
        llm_called_files = []

        def mock_llm_gen(messages, lang, rel_path, *args, **kwargs):
            llm_called_files.append(rel_path)
            project_dir = kwargs.get("project_dir", None)
            if lang == "css":
                code = '@import "tailwindcss";'
            else:
                code = "export default function App() { return <div>UI Component</div>; }"
            if project_dir:
                from tools.coding.workspace_manager import WorkspaceManager
                WorkspaceManager.get_instance().write_workspace_file(project_dir, rel_path, code)
            return code

        with patch.object(assistant, '_generate_and_validate', side_effect=mock_llm_gen):
            with patch('tools.coding.workspace_manager.WorkspaceManager.open_workspace'):
                with patch('tools.coding.local_website_server.LocalWebsiteServer.start_preview', return_value=("http://127.0.0.1:5173", 5173)):
                    with patch('tools.coding.website_deployer.LocalPreviewDeployer.execute_production_build', return_value=(True, "")):
                        assistant.build_website("portfolio website bana do", brief=brief, open_browser=False)

        for infra_f in infra_files:
            self.assertNotIn(infra_f, llm_called_files, f"LLM was illegally invoked for infrastructure file: {infra_f}")
        print("[1. Zero-LLM Infrastructure Generation Test PASSED 100%]")

    # --- 2. 100-PROJECT INFRASTRUCTURE DETERMINISM TEST ---

    def test_02_100_projects_infrastructure_determinism(self):
        for i in range(1, 101):
            biz_name = f"Test Business {i}"
            proj_name = f"project_{i}"

            pkg_str = WebsiteProjectTemplates.generate_package_json(biz_name, proj_name)
            pkg_data = json.loads(pkg_str)
            self.assertEqual(pkg_data["name"], proj_name)
            self.assertIn("react", pkg_data["dependencies"])
            self.assertIn("vite", pkg_data["devDependencies"])

            tsconfig_str = WebsiteProjectTemplates.generate_tsconfig()
            tsconfig_data = json.loads(tsconfig_str)
            self.assertTrue(tsconfig_data["compilerOptions"]["jsx"] == "react-jsx")

            vite_str = WebsiteProjectTemplates.generate_vite_config()
            self.assertIn("@tailwindcss/vite", vite_str)

            html_str = WebsiteProjectTemplates.generate_index_html(biz_name)
            self.assertIn("<div id=\"root\"></div>", html_str)

            main_tsx_str = WebsiteProjectTemplates.generate_main_tsx()
            self.assertIn("ReactDOM.createRoot", main_tsx_str)

        print("[2. 100-Project Infrastructure Determinism Test PASSED 100%]")

    # --- 3. TAILWIND V4 + VITE COMPATIBILITY TEST ---

    def test_03_tailwind_v4_vite_compatibility(self):
        pkg_str = WebsiteProjectTemplates.generate_package_json()
        pkg_data = json.loads(pkg_str)
        all_deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}

        self.assertIn("@tailwindcss/vite", all_deps)
        self.assertIn("tailwindcss", all_deps)

        vite_cfg = WebsiteProjectTemplates.generate_vite_config()
        self.assertIn("import tailwindcss from '@tailwindcss/vite'", vite_cfg)
        self.assertIn("tailwindcss()", vite_cfg)

        is_valid, err = CodeValidator.validate_infrastructure_compatibility(pkg_str)
        self.assertTrue(is_valid, f"Infrastructure compatibility check failed: {err}")
        print("[3. Tailwind v4 + Vite Compatibility Test PASSED 100%]")

    # --- 4. SEPARATE ATTEMPT COUNTERS TEST ---

    def test_04_separate_attempt_counters(self):
        assistant = CodeAssistant()
        brief = WebsiteRequirementsAnalyzer.extract_information("portfolio website bana do", WebsiteCategory.PORTFOLIO, WebsiteSubject(name="Test"))

        gen_attempts = []
        repair_attempts = []

        def mock_failing_gen(messages, lang, rel_path, *args, **kwargs):
            prompt_content = messages[0]["content"] if messages else ""
            if "You are repairing" in prompt_content:
                repair_attempts.append(rel_path)
            else:
                gen_attempts.append(rel_path)
            return "" # Always fail validation

        with patch.object(assistant, '_generate_and_validate', side_effect=mock_failing_gen):
            with patch('tools.coding.workspace_manager.WorkspaceManager.open_workspace'):
                code, path = assistant.build_website("portfolio website bana do", brief=brief, open_browser=False)
                self.assertIn("Error", code)

        self.assertLessEqual(len(gen_attempts), 15 * 2)
        self.assertLessEqual(len(repair_attempts), 15 * 2)
        print("[4. Separate Attempt Counters Test PASSED 100%]")

    # --- 5. LEVEL 1 & LEVEL 2 UI COMPLETENESS TEST ---

    def test_05_level_1_and_level_2_completeness(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = os.path.join(temp_dir, "src")
            os.makedirs(src_dir, exist_ok=True)

            # Test 1: Unstyled bare placeholder -> FAIL Level 2
            with open(os.path.join(src_dir, "App.tsx"), "w") as f:
                f.write("export default function App() { return <div>Home About Us Special Menu Opening Hours</div>; }")

            brief = WebsiteBrief(category="portfolio", required_sections=["Hero", "About", "Skills", "Projects", "Contact"])
            is_valid, err = CodeValidator.validate_level2_completeness(temp_dir, brief)
            self.assertFalse(is_valid)

            # Test 2: Full UI components -> PASS Level 2
            comp_dir = os.path.join(src_dir, "components")
            os.makedirs(comp_dir, exist_ok=True)

            for comp_name in ["Navbar.tsx", "Hero.tsx", "About.tsx", "Skills.tsx", "Projects.tsx", "Contact.tsx"]:
                with open(os.path.join(comp_dir, comp_name), "w") as f:
                    f.write(f"export default function {comp_name.replace('.tsx', '')}() {{ return <section className='min-h-screen bg-slate-900 text-white p-8'><h1>{comp_name}</h1></section>; }}")

            is_valid_2, err_2 = CodeValidator.validate_level2_completeness(temp_dir, brief)
            self.assertTrue(is_valid_2, f"Level 2 completeness failed: {err_2}")
            print("[5. Level 1 & Level 2 UI Completeness Test PASSED 100%]")

    # --- 6. ANTI-FABRICATION SECURITY GATE TEST ---

    def test_06_anti_fabrication_gate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = os.path.join(temp_dir, "src")
            os.makedirs(src_dir, exist_ok=True)

            # Test 1: Fabricated phone number -> FAIL
            with open(os.path.join(src_dir, "App.tsx"), "w") as f:
                f.write("export default function App() { return <div>Call us at 0120-1234567 at TCS Campus, Ghaziabad</div>; }")

            is_valid, err = CodeValidator.validate_anti_fabrication(temp_dir)
            self.assertFalse(is_valid)

            # Test 2: Clean contact info -> PASS
            with open(os.path.join(src_dir, "App.tsx"), "w") as f:
                f.write("export default function App() { return <div>Contact info available upon request.</div>; }")

            is_valid_2, err_2 = CodeValidator.validate_anti_fabrication(temp_dir)
            self.assertTrue(is_valid_2)
            print("[6. Anti-Fabrication Gate Test PASSED 100%]")

    # --- 7. REAL PRODUCTION BUILD GATE TEST ---

    def test_07_real_production_build_gate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "package.json"), "w") as f:
                f.write(WebsiteProjectTemplates.generate_package_json())
            with open(os.path.join(temp_dir, "tsconfig.json"), "w") as f:
                f.write(WebsiteProjectTemplates.generate_tsconfig())
            with open(os.path.join(temp_dir, "vite.config.ts"), "w") as f:
                f.write(WebsiteProjectTemplates.generate_vite_config())
            with open(os.path.join(temp_dir, "index.html"), "w") as f:
                f.write(WebsiteProjectTemplates.generate_index_html("Test App"))
            os.makedirs(os.path.join(temp_dir, "src"), exist_ok=True)
            with open(os.path.join(temp_dir, "src", "main.tsx"), "w") as f:
                f.write(WebsiteProjectTemplates.generate_main_tsx())
            with open(os.path.join(temp_dir, "src", "App.tsx"), "w") as f:
                f.write("export default function App() { return <div>Build Test</div>; }")
            with open(os.path.join(temp_dir, "src", "index.css"), "w") as f:
                f.write('@import "tailwindcss";')

            is_ok, err = LocalPreviewDeployer.execute_production_build(temp_dir)
            self.assertTrue(is_ok, f"Production build failed: {err}")
            dist_index = os.path.join(temp_dir, "dist", "index.html")
            self.assertTrue(os.path.exists(dist_index))
            print("[7. Real Production Build Gate Test PASSED 100%]")

    # --- 8. MANDATORY E2E TEST: FLUTTER DEVELOPER DARK PREMIUM PORTFOLIO ---

    def test_08_flutter_developer_dark_premium_e2e(self):
        cmd = "mera ek modern portfolio website bana do main flutter developer hun dark premium project section rakhna"
        cat = WebsiteRequirementsAnalyzer.detect_category(cmd)
        subj = WebsiteRequirementsAnalyzer.detect_subject(cmd)
        brief = WebsiteRequirementsAnalyzer.extract_information(cmd, cat, subj)

        self.assertEqual(brief.category, "portfolio")
        self.assertEqual(brief.technology_stack, "React + TypeScript + Tailwind CSS + Vite")
        self.assertIn("Flutter", brief.title + brief.design_preference + " ".join(brief.special_requirements))

        plan = WebsiteProjectPlanner.plan_project(cmd, brief=brief)
        file_paths = [f.path for f in plan.files]

        self.assertIn("package.json", file_paths)
        self.assertIn("tsconfig.json", file_paths)
        self.assertIn("vite.config.ts", file_paths)
        self.assertIn("index.html", file_paths)
        self.assertIn("src/main.tsx", file_paths)
        self.assertIn("src/App.tsx", file_paths)

        assistant = CodeAssistant()
        llm_called_files = []

        def mock_e2e_llm(messages, lang, rel_path, *args, **kwargs):
            llm_called_files.append(rel_path)
            project_dir = kwargs.get("project_dir", None)
            if lang == "css":
                code = '@import "tailwindcss"; body { background-color: #0f172a; color: #f8fafc; }'
            else:
                code = f"export default function Component_{rel_path.replace('/', '_').replace('.', '_')}() {{ return <section className='min-h-screen bg-slate-900 text-white p-8'><h1>Flutter Developer Portfolio Section</h1><p>Projects, Skills, Experience</p></section>; }}"
            if project_dir:
                from tools.coding.workspace_manager import WorkspaceManager
                WorkspaceManager.get_instance().write_workspace_file(project_dir, rel_path, code)
            return code

        with patch.object(assistant, '_generate_and_validate', side_effect=mock_e2e_llm):
            with patch('tools.coding.workspace_manager.WorkspaceManager.open_workspace'):
                with patch('tools.coding.local_website_server.LocalWebsiteServer.start_preview', return_value=("http://127.0.0.1:5173", 5173)):
                    with patch('tools.coding.website_deployer.LocalPreviewDeployer.execute_production_build', return_value=(True, "")):
                        code, path = assistant.build_website(cmd, brief=brief, open_browser=False)
                        self.assertNotIn("Error", code)

        infra_files = {"package.json", "tsconfig.json", "vite.config.ts", "index.html", "src/main.tsx"}
        for infra_f in infra_files:
            self.assertNotIn(infra_f, llm_called_files, f"LLM was invoked for infrastructure file: {infra_f}")

        print("[8. Flutter Developer Dark Premium E2E Test PASSED 100%]")

if __name__ == "__main__":
    unittest.main()
