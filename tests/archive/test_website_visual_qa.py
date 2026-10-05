import unittest
import tempfile
import os
from tools.coding.website_visual_qa import WebsiteVisualQA
from tools.coding.code_validator import CodeValidator

class TestWebsiteVisualQA(unittest.TestCase):
    def test_01_placeholder_validation(self):
        ok, msg = CodeValidator.validate_no_placeholders("<h1>Hero Section</h1>")
        self.assertFalse(ok)
        self.assertIn("Placeholder Violation", msg)

        ok2, msg2 = CodeValidator.validate_no_placeholders("<h1>Building Intelligent AI Systems</h1>")
        self.assertTrue(ok2)

    def test_02_critical_css_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = os.path.join(tmpdir, "src")
            os.makedirs(src_dir, exist_ok=True)
            css_file = os.path.join(src_dir, "index.css")
            with open(css_file, "w", encoding="utf-8") as f:
                f.write('@import "tailwindcss";')

            ok, msg = CodeValidator.validate_critical_css_failure(tmpdir)
            self.assertTrue(ok)

    def test_03_evaluate_website_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = os.path.join(tmpdir, "src", "components")
            os.makedirs(src_dir, exist_ok=True)
            with open(os.path.join(src_dir, "Hero.tsx"), "w", encoding="utf-8") as f:
                f.write("export default function Hero() { return <h1>Building AI</h1>; }")
            with open(os.path.join(src_dir, "Navbar.tsx"), "w", encoding="utf-8") as f:
                f.write("export default function Navbar() { return <nav>Logo</nav>; }")
            with open(os.path.join(src_dir, "Projects.tsx"), "w", encoding="utf-8") as f:
                f.write("export default function Projects() { return <div>Projects</div>; }")
            with open(os.path.join(tmpdir, "src", "index.css"), "w", encoding="utf-8") as f:
                f.write('@import "tailwindcss";')

            passed, issues = WebsiteVisualQA.evaluate_website(tmpdir, preview_url="")
            self.assertTrue(passed)

if __name__ == "__main__":
    unittest.main()
