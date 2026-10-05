"""
tests/test_cinematic_3d_website_builder.py
Unit tests verifying True 3D / Cinematic Website Builder Engine:
1. Cinematic visual plan generation.
2. Technology/AI 3D profile detection.
3. 3D CSS utilities & depth layer injection.
4. Visual primitive & spatial component generation.
5. Multi-layer Hero generation with mouse parallax.
6. Section composition diversity.
7. Reduced-motion support.
8. Static cinematic QA evaluation (evaluate_cinematic_3d_quality).
9. PREMIUM_VISUAL_ACCEPTANCE telemetry & failure detection.
10. Existing readiness gate preservation.
"""

import unittest
import os
import shutil
import tempfile
import io
import sys

from tools.coding.website_visual_intelligence import WebsiteVisualIntelligence, VisualWebsitePlan
from tools.coding.website_design_system import WebsiteDesignSystemGenerator, WebsiteDesignSystem
from tools.coding.website_project_templates import WebsiteProjectTemplates
from tools.coding.component_generation_pool import ComponentGenerationPool
from tools.coding.website_master_planner import MasterWebsitePlan, ComponentSpec
from tools.coding.website_visual_qa import WebsiteVisualQA
from tools.coding.website_state import WebsiteStateManager

class TestCinematic3DWebsiteBuilder(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_1_cinematic_visual_plan_generation(self):
        """Test 1: VisualWebsitePlan includes 3D attributes."""
        plan = WebsiteVisualIntelligence.generate_plan(None, None, "Inurum Technology 3D website")
        self.assertIsInstance(plan, VisualWebsitePlan)
        self.assertTrue(plan.mouse_parallax_enabled)
        self.assertEqual(plan.three_d_level, "high")
        self.assertIn("depth-bg", plan.spatial_depth_layers)

    def test_2_technology_ai_3d_profile(self):
        """Test 2: Technology/AI prompt creates cinematic spatial tech design system."""
        ds = WebsiteDesignSystemGenerator.generate_design_system(None, "Inurum Technology futuristic spatial platform")
        self.assertIsInstance(ds, WebsiteDesignSystem)
        self.assertEqual(ds.theme_name, "cinematic_spatial_tech")
        self.assertEqual(ds.glassmorphism_class, "spatial-glass-panel")
        self.assertEqual(ds.card_hover_class, "card-3d-tilt")

    def test_3_3d_css_utilities_generation(self):
        """Test 3: generate_index_css creates perspective, preserve-3d, and keyframes."""
        css = WebsiteProjectTemplates.generate_index_css()
        self.assertIn("perspective-1200", css)
        self.assertIn("preserve-3d", css)
        self.assertIn("card-3d-tilt", css)
        self.assertIn("spatial-glass-panel", css)
        self.assertIn("@keyframes rotateSlow", css)
        self.assertIn("@keyframes floatSlow", css)
        self.assertIn("@keyframes breathingGlow", css)

    def test_4_visual_primitive_component_generation(self):
        """Test 4: Component fallback generates valid TSX with 3D elements."""
        spec = ComponentSpec(name="Services", file_path="src/components/Services.tsx", role="Services")
        plan = MasterWebsitePlan(business_name="Inurum", category="technology", theme="cinematic", color_palette={}, typography={}, hero_spec={}, cta_spec={}, components=[spec], global_styles="")
        code = ComponentGenerationPool._deterministic_component(spec, plan)
        self.assertIn("import React", code)
        self.assertIn("card-3d-tilt", code)
        self.assertIn("spatial-glass-panel", code)

    def test_5_multi_layer_hero_with_mouse_parallax(self):
        """Test 5: Hero component includes mouse parallax hook and 3D visual focal object."""
        spec = ComponentSpec(name="Hero", file_path="src/components/Hero.tsx", role="Hero")
        plan = MasterWebsitePlan(business_name="Inurum Technology", category="technology", theme="cinematic", color_palette={}, typography={}, hero_spec={}, cta_spec={}, components=[spec], global_styles="")
        code = ComponentGenerationPool._deterministic_component(spec, plan)

        self.assertIn("mousePos", code)
        self.assertIn("mousemove", code)
        self.assertIn("translate3d", code)
        self.assertIn("-CORE", code)
        self.assertIn("animate-rotate-slow", code)

    def test_6_section_composition_diversity(self):
        """Test 6: Sections do not use uniform repetitive 3-card grids."""
        spec_services = ComponentSpec(name="Services", file_path="src/components/Services.tsx", role="Services")
        plan = MasterWebsitePlan(business_name="Inurum", category="technology", theme="cinematic", color_palette={}, typography={}, hero_spec={}, cta_spec={}, components=[spec_services], global_styles="")
        code = ComponentGenerationPool._deterministic_component(spec_services, plan)
        self.assertIn("lg:col-span-4 lg:sticky", code)

    def test_7_reduced_motion_support(self):
        """Test 7: index.css includes prefers-reduced-motion media query."""
        css = WebsiteProjectTemplates.generate_index_css()
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)

    def test_8_static_cinematic_qa_evaluation_pass(self):
        """Test 8: Valid output directory passes evaluate_cinematic_3d_quality."""
        os.makedirs(os.path.join(self.test_dir, "src", "components"), exist_ok=True)
        with open(os.path.join(self.test_dir, "src", "index.css"), "w", encoding="utf-8") as f:
            f.write(WebsiteProjectTemplates.generate_index_css())

        spec_hero = ComponentSpec(name="Hero", file_path="src/components/Hero.tsx", role="Hero")
        plan = MasterWebsitePlan(business_name="Inurum", category="technology", theme="cinematic", color_palette={}, typography={}, hero_spec={}, cta_spec={}, components=[spec_hero], global_styles="")
        hero_code = ComponentGenerationPool._deterministic_component(spec_hero, plan)

        with open(os.path.join(self.test_dir, "src", "components", "Hero.tsx"), "w", encoding="utf-8") as f:
            f.write(hero_code)

        passed, issues = WebsiteVisualQA.evaluate_cinematic_3d_quality(self.test_dir)
        self.assertTrue(passed, f"Cinematic QA failed unexpectedly: {issues}")

    def test_9_premium_visual_acceptance_failure_detection(self):
        """Test 9: Output directory without 3D focal object triggers PREMIUM_VISUAL_ACCEPTANCE status=FAIL."""
        os.makedirs(os.path.join(self.test_dir, "src", "components"), exist_ok=True)
        with open(os.path.join(self.test_dir, "src", "index.css"), "w", encoding="utf-8") as f:
            f.write("/* plain flat css */\n")

        with open(os.path.join(self.test_dir, "src", "components", "Hero.tsx"), "w", encoding="utf-8") as f:
            f.write("export const Hero = () => <div>Flat standard Hero card</div>;\n")

        out = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = out
        try:
            passed, issues = WebsiteVisualQA.evaluate_cinematic_3d_quality(self.test_dir)
            sys.stdout = old_stdout
            logs = out.getvalue()

            self.assertFalse(passed)
            self.assertIn("[PREMIUM_VISUAL_ACCEPTANCE]", logs)
            self.assertIn("status=FAIL", logs)
        finally:
            sys.stdout = old_stdout

    def test_10_existing_readiness_gate_preservation(self):
        """Test 10: Website state readiness authority flags remain unchanged."""
        manager = WebsiteStateManager.get_instance()
        manager.reset_active_website("test_authority_cinematic", self.test_dir)
        state = manager.get_active_website()

        self.assertFalse(state.is_authoritative_ready())
        state.dependency_validation_passed = True
        state.build_passed = True
        state.preview_running = True
        state.http_status_ok = True
        state.visual_qa_status = "passed"
        state.visual_qa_passed = True
        state.responsive_passed = True
        state.console_errors = 0
        state.broken_images = 0
        self.assertTrue(state.is_authoritative_ready())

if __name__ == "__main__":
    unittest.main()
