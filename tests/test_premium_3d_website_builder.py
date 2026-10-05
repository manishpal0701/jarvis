import os
import sys
import unittest
import tempfile
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.coding.website_visual_intelligence import WebsiteVisualIntelligence, VisualWebsitePlan
from tools.coding.website_project_templates import WebsiteProjectTemplates
from tools.coding.component_generation_pool import ComponentGenerationPool, MasterWebsitePlan, ComponentSpec
from tools.coding.website_visual_qa import WebsiteVisualQA
from tools.coding.code_validator import CodeValidator

class TestPremium3DWebsiteBuilder(unittest.TestCase):

    def test_01_3d_visual_plan_generation(self):
        """Verify smart effect selection and 3D visual plan specifications for tech/futuristic queries."""
        plan = WebsiteVisualIntelligence.generate_plan(
            brief=type("Brief", (), {"category": "technology"})(),
            user_command="Jarvis, Inurum Technology ki ek premium futuristic 3D animated website banao."
        )
        self.assertIsInstance(plan, VisualWebsitePlan)
        self.assertEqual(plan.animation_level, "high")
        self.assertEqual(plan.three_d_level, "high")
        self.assertTrue(plan.glassmorphism)
        self.assertTrue(plan.cursor_effects)
        self.assertTrue(plan.reduced_motion_support)

    def test_02_css_3d_and_animation_utilities_template(self):
        """Verify CSS utilities generate 3D perspective, tilt, glassmorphism, and reduced-motion queries."""
        css_content = WebsiteProjectTemplates.generate_index_css()
        self.assertIn(".perspective-1000", css_content)
        self.assertIn(".preserve-3d", css_content)
        self.assertIn(".card-3d-tilt", css_content)
        self.assertIn(".glass-panel", css_content)
        self.assertIn("@keyframes floatSlow", css_content)
        self.assertIn("prefers-reduced-motion", css_content)

    def test_03_component_generation_pool_fallback_3d_classes(self):
        """Verify deterministic fallback components contain 3D perspective and float animation classes."""
        from unittest.mock import patch
        from tools.coding.website_master_planner import WebsiteMasterPlanner
        with patch("ai.ai_response_manager.AIResponseManager.generate_response", side_effect=Exception("Fast Mock Timeout")):
            master_plan = WebsiteMasterPlanner.generate_master_plan(
                task="Jarvis, Inurum Technology website banao"
            )
        spec = ComponentSpec(name="Hero", file_path="src/components/Hero.tsx", role="Hero banner", key_elements=["headline", "cta"])
        code = ComponentGenerationPool._deterministic_component(spec, master_plan)
        self.assertIn("perspective-1000", code)
        self.assertIn("card-3d-tilt", code)
        self.assertIn("glass-panel", code)
        self.assertIn("animate-float-slow", code)

    def test_04_visual_qa_3d_and_reduced_motion_checks(self):
        """Verify WebsiteVisualQA validates index.css reduced-motion and overflow rules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = os.path.join(tmpdir, "src")
            comp_dir = os.path.join(src_dir, "components")
            os.makedirs(comp_dir, exist_ok=True)

            # Create 3 components
            for name in ["Navbar", "Hero", "Footer"]:
                with open(os.path.join(comp_dir, f"{name}.tsx"), "w", encoding="utf-8") as f:
                    f.write("import React from 'react'; export const C = () => <div className='perspective-1000 preserve-3d card-3d-tilt DynamicSpatialEnvironment RotatingCore animate-float-slow'>Component</div>;")

            # Create index.css with 3D and reduced motion
            with open(os.path.join(src_dir, "index.css"), "w", encoding="utf-8") as f:
                f.write(WebsiteProjectTemplates.generate_index_css())

            passed, issues = WebsiteVisualQA.evaluate_website(tmpdir, website_type="technology")
            self.assertTrue(passed, f"Visual QA should pass with complete CSS: {issues}")

    def test_05_website_builder_source_files_preserved(self):
        """Verify Website Builder source files exist and maintain readiness gates."""
        files = [
            os.path.join(BASE_DIR, "tools", "coding", "code_assistant.py"),
            os.path.join(BASE_DIR, "tools", "coding", "component_generation_pool.py"),
            os.path.join(BASE_DIR, "tools", "coding", "website_master_planner.py"),
            os.path.join(BASE_DIR, "tools", "coding", "website_planner.py"),
        ]
        for f in files:
            self.assertTrue(os.path.exists(f), f"Required Website Builder source missing: {f}")

if __name__ == "__main__":
    unittest.main()
