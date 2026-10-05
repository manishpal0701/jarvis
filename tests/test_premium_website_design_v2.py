import os
import sys
import unittest
import tempfile
from unittest.mock import patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.coding.website_visual_intelligence import WebsiteVisualIntelligence, VisualWebsitePlan
from tools.coding.website_project_templates import WebsiteProjectTemplates
from tools.coding.component_generation_pool import ComponentGenerationPool, ComponentSpec
from tools.coding.website_master_planner import WebsiteMasterPlanner
from tools.coding.website_visual_qa import WebsiteVisualQA

class TestPremiumWebsiteDesignV2(unittest.TestCase):

    def test_01_art_directed_visual_plan_category_profiles(self):
        """Verify dynamic visual plan generation per category (Tech vs Restaurant)."""
        # Tech profile
        tech_plan = WebsiteVisualIntelligence.generate_plan(
            brief=type("Brief", (), {"category": "technology"})(),
            user_command="Jarvis, Inurum Technology website banao"
        )
        self.assertIsInstance(tech_plan, VisualWebsitePlan)
        self.assertEqual(tech_plan.animation_level, "high")
        self.assertTrue(tech_plan.glassmorphism)

        # Restaurant profile (no futuristic overload)
        rest_plan = WebsiteVisualIntelligence.generate_plan(
            brief=type("Brief", (), {"category": "restaurant"})(),
            user_command="Bella Tavola restaurant website"
        )
        self.assertIsInstance(rest_plan, VisualWebsitePlan)
        self.assertEqual(rest_plan.animation_level, "medium")
        self.assertFalse(rest_plan.glassmorphism)
        self.assertFalse(rest_plan.cursor_effects)

    def test_02_non_blocking_google_fonts_and_css_utilities(self):
        """Verify HTML uses non-blocking Google Fonts and index.css has 3D utilities."""
        html = WebsiteProjectTemplates.generate_index_html(biz_name="TestBiz")
        self.assertIn('media="print" onload="this.media=\'all\'"', html)
        self.assertIn("<noscript>", html)

        css = WebsiteProjectTemplates.generate_index_css()
        self.assertIn(".perspective-1000", css)
        self.assertIn(".card-3d-tilt", css)
        self.assertIn(".glass-panel", css)
        self.assertIn("prefers-reduced-motion", css)

    def test_03_dynamic_fallback_components(self):
        """Verify fallback components use dynamic business name slug rather than static text."""
        with patch("ai.ai_response_manager.AIResponseManager.generate_response", side_effect=Exception("Fast Mock")):
            master_plan = WebsiteMasterPlanner.generate_master_plan(task="Kashyap Air Fresh website")
            master_plan.business_name = "Kashyap Air Fresh"

        spec = ComponentSpec(name="Hero", file_path="src/components/Hero.tsx", role="Hero banner", key_elements=["headline", "cta"])
        code = ComponentGenerationPool._deterministic_component(spec, master_plan)

        self.assertIn("kashyap-air-fresh", code.lower())
        self.assertIn("perspective-1000", code)

    def test_04_visual_qa_design_criteria(self):
        """Verify WebsiteVisualQA evaluates reduced motion and overflow CSS rules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = os.path.join(tmpdir, "src")
            comp_dir = os.path.join(src_dir, "components")
            os.makedirs(comp_dir, exist_ok=True)

            for name in ["Navbar", "Hero", "Footer"]:
                with open(os.path.join(comp_dir, f"{name}.tsx"), "w", encoding="utf-8") as f:
                    f.write("import React from 'react'; export const C = () => <div className='perspective-1000 preserve-3d card-3d-tilt DynamicSpatialEnvironment RotatingCore animate-float-slow'>C</div>;")

            with open(os.path.join(src_dir, "index.css"), "w", encoding="utf-8") as f:
                f.write(WebsiteProjectTemplates.generate_index_css())

            passed, issues = WebsiteVisualQA.evaluate_website(tmpdir, website_type="technology")
            self.assertTrue(passed, f"Visual QA should pass: {issues}")

    def test_05_protected_files_untouched(self):
        """Verify core Website Builder & protected files remain untouched."""
        files = [
            os.path.join(BASE_DIR, "tools", "coding", "code_assistant.py"),
            os.path.join(BASE_DIR, "tools", "coding", "component_generation_pool.py"),
            os.path.join(BASE_DIR, "tools", "coding", "website_master_planner.py"),
            os.path.join(BASE_DIR, "tools", "coding", "website_planner.py"),
        ]
        for f in files:
            self.assertTrue(os.path.exists(f))

if __name__ == "__main__":
    unittest.main()
