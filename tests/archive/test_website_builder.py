import unittest
import os
import shutil
import tempfile
import urllib.request
from tools.coding.code_assistant import CodeAssistant
from tools.coding.website_planner import WebsiteProjectPlanner
from tools.coding.local_website_server import LocalWebsiteServer
from tools.coding.code_validator import CodeValidator
from tools.coding.workspace_manager import WorkspaceManager

class TestWebsiteBuilder(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.assistant = CodeAssistant()

    def tearDown(self):
        LocalWebsiteServer.get_instance().stop_preview()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_1_python_calculator_standalone_mode(self):
        cmd = "python calculator bana do"
        mode = self.assistant.classify_coding_mode(cmd)
        self.assertEqual(mode, "STANDALONE_CODE")
        rel, lang, ext = self.assistant.detect_target_file(cmd)
        self.assertEqual(lang, "python")
        self.assertEqual(ext, ".py")

    def test_2_project_modification_mode(self):
        cmd = "mere Jarvis project mein calculator add karo"
        mode = self.assistant.classify_coding_mode(cmd)
        self.assertEqual(mode, "PROJECT_MODIFICATION")

    def test_3_website_build_mode_and_planner(self):
        cmd = "modern portfolio bana do"
        mode = self.assistant.classify_coding_mode(cmd)
        self.assertEqual(mode, "WEBSITE_BUILD")
        
        plan = WebsiteProjectPlanner.plan_project(cmd, self.test_dir)
        paths = [f.path for f in plan.files]
        self.assertEqual(plan.framework, "react")
        self.assertIn("package.json", paths)
        self.assertIn("tsconfig.json", paths)
        self.assertIn("vite.config.ts", paths)
        self.assertIn("index.html", paths)
        self.assertIn("src/main.tsx", paths)
        self.assertIn("src/App.tsx", paths)

    def test_3b_vanilla_website_explicit_stack(self):
        cmd = "HTML CSS JS mein website bana do"
        mode = self.assistant.classify_coding_mode(cmd)
        self.assertEqual(mode, "WEBSITE_BUILD")
        
        plan = WebsiteProjectPlanner.plan_project(cmd, self.test_dir)
        paths = [f.path for f in plan.files]
        self.assertEqual(plan.framework, "vanilla")
        self.assertIn("index.html", paths)
        self.assertIn("style.css", paths)
        self.assertIn("script.js", paths)

    def test_4_validate_html_content(self):
        valid_html = "<!DOCTYPE html><html><head><title>Portfolio</title></head><body><h1>My Portfolio</h1></body></html>"
        is_valid, _ = CodeValidator.validate(valid_html, "html")
        self.assertTrue(is_valid)

    def test_5_validate_css_content(self):
        valid_css = "body { background-color: #0f111a; color: #fff; } .hero { display: flex; }"
        is_valid, _ = CodeValidator.validate(valid_css, "css")
        self.assertTrue(is_valid)

        invalid_css = "<html><body>Not CSS</body></html>"
        is_valid_bad, _ = CodeValidator.validate(invalid_css, "css")
        self.assertFalse(is_valid_bad)

    def test_6_validate_js_content(self):
        valid_js = "document.addEventListener('DOMContentLoaded', () => { console.log('Loaded'); });"
        is_valid, _ = CodeValidator.validate(valid_js, "javascript")
        self.assertTrue(is_valid)

    def test_7_reject_html_document_saved_as_javascript(self):
        html_as_js = "<!DOCTYPE html><html><body><h1>Wrong file</h1></body></html>"
        is_valid, err_msg = CodeValidator.validate(html_as_js, "javascript")
        self.assertFalse(is_valid)
        self.assertIn("HTML document", err_msg)

    def test_8_local_website_server_port(self):
        site_dir = os.path.join(self.test_dir, "test_site")
        os.makedirs(site_dir, exist_ok=True)
        with open(os.path.join(site_dir, "index.html"), "w") as f:
            f.write("<h1>Test Site</h1>")

        server = LocalWebsiteServer.get_instance()
        url, port = server.start_preview(site_dir, open_browser=False)
        self.assertTrue(url.startswith("http://127.0.0.1:"))
        self.assertGreater(port, 5000)

    def test_9_read_generated_index_html_http_success(self):
        site_dir = os.path.join(self.test_dir, "http_site")
        os.makedirs(site_dir, exist_ok=True)
        with open(os.path.join(site_dir, "index.html"), "w") as f:
            f.write("<!DOCTYPE html><html><body><h1>HTTP Success Test</h1></body></html>")

        server = LocalWebsiteServer.get_instance()
        url, port = server.start_preview(site_dir, open_browser=False)
        
        req = urllib.request.urlopen(f"{url}/index.html")
        self.assertEqual(req.status, 200)
        content = req.read().decode('utf-8')
        self.assertIn("HTTP Success Test", content)

    def test_10_workspace_disk_preview_consistency(self):
        site_dir = os.path.join(self.test_dir, "consistency_site")
        os.makedirs(site_dir, exist_ok=True)
        html_content = "<!DOCTYPE html><html><body><h1>Consistent</h1></body></html>"
        file_path = os.path.join(site_dir, "index.html")
        
        with open(file_path, "w") as f:
            f.write(html_content)

        ws = WorkspaceManager.get_instance()
        ws.set_final_code(html_content)

        with open(file_path, "r") as f:
            disk_content = f.read()

        self.assertEqual(ws.code_content, disk_content)

    def test_11_invalid_generated_file_prevents_preview_startup(self):
        # Simulate validation failure state
        is_valid, _ = CodeValidator.validate("def invalid_html(): pass", "html")
        self.assertFalse(is_valid)
        
        server = LocalWebsiteServer.get_instance()
        self.assertFalse(server.is_running)

if __name__ == "__main__":
    unittest.main()
