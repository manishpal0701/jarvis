import unittest
import os
import sys
import json
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.coding.website_technology_selector import WebsiteTechnologySelector, TechnologyStackSpec
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer, WebsiteCategory, WebsiteSubject, WebsiteBrief
from tools.coding.website_planner import WebsiteProjectPlanner, WebsiteProjectPlan
from tools.coding.existing_project_analyzer import ExistingProjectAnalyzer, ProjectPatternSpec
from tools.coding.code_validator import CodeValidator
from tools.coding.website_session_manager import WebsiteSessionManager, WebsiteSessionState
from tools.coding.workspace_manager import WorkspaceManager
from tools.coding.code_assistant import CodeAssistant
from tools.coding.website_asset_planner import WebsiteAssetPlanner

class TestWebsiteReactVite(unittest.TestCase):

    def setUp(self):
        self.session_mgr = WebsiteSessionManager.get_instance()
        self.session_mgr.reset_session()
        self.ws = WorkspaceManager.get_instance()

    def test_01_default_react_vite_selection(self):
        cmd = "mera modern portfolio bana do"
        tech = WebsiteTechnologySelector.detect_stack(cmd)
        self.assertTrue(tech.default_stack)
        self.assertEqual(tech.framework, "react")
        self.assertEqual(tech.language, "typescript")
        self.assertEqual(tech.styling, "tailwind")
        self.assertEqual(tech.build_system, "vite")
        self.assertEqual(tech.display_name, "React + TypeScript + Tailwind CSS + Vite")

    def test_02_explicit_nextjs_selection(self):
        cmd = "Next.js mein website bana do"
        tech = WebsiteTechnologySelector.detect_stack(cmd)
        self.assertFalse(tech.default_stack)
        self.assertEqual(tech.framework, "nextjs")

    def test_03_explicit_vue_selection(self):
        cmd = "Vue website bana do"
        tech = WebsiteTechnologySelector.detect_stack(cmd)
        self.assertFalse(tech.default_stack)
        self.assertEqual(tech.framework, "vue")

    def test_04_explicit_vanilla_selection(self):
        cmd = "HTML CSS JS mein website bana do"
        tech = WebsiteTechnologySelector.detect_stack(cmd)
        self.assertFalse(tech.default_stack)
        self.assertEqual(tech.framework, "vanilla")

    def test_05_explicit_java_selection(self):
        cmd = "Java Spring Boot website bana do"
        tech = WebsiteTechnologySelector.detect_stack(cmd)
        self.assertFalse(tech.default_stack)
        self.assertEqual(tech.framework, "spring_boot")

    def test_06_valid_react_tsx(self):
        good_tsx = "export default function App() { return <div className='min-h-screen bg-slate-900'><h1>App</h1></div>; }"
        self.assertTrue(CodeValidator.validate_tsx(good_tsx)[0])

    def test_07_css_contains_no_html(self):
        bad_css = "<!DOCTYPE html><html><body><h1>CSS</h1></body></html>"
        is_valid, err = CodeValidator.validate_css(bad_css)
        self.assertFalse(is_valid)
        self.assertIn("HTML", err)

    def test_08_tsx_contains_no_standalone_html_doc(self):
        bad_tsx = "<!DOCTYPE html><html><head><title>Title</title></head></html>"
        is_valid, err = CodeValidator.validate_tsx(bad_tsx)
        self.assertFalse(is_valid)
        self.assertIn("HTML document wrapper", err)

    def test_09_json_validation(self):
        good_json = '{"name": "react-app", "dependencies": {"react": "^18.0.0"}}'
        bad_json = '{"name": "react-app",}'
        self.assertTrue(CodeValidator.validate_json(good_json)[0])
        self.assertFalse(CodeValidator.validate_json(bad_json)[0])

    def test_10_vite_project_structure(self):
        task = "portfolio website bana do"
        plan = WebsiteProjectPlanner.plan_project(task)
        file_paths = [f.path for f in plan.files]

        self.assertEqual(plan.framework, "react")
        self.assertIn("package.json", file_paths)
        self.assertIn("tsconfig.json", file_paths)
        self.assertIn("vite.config.ts", file_paths)
        self.assertIn("index.html", file_paths)
        self.assertIn("src/main.tsx", file_paths)
        self.assertIn("src/App.tsx", file_paths)
        self.assertIn("src/index.css", file_paths)

if __name__ == "__main__":
    unittest.main()
