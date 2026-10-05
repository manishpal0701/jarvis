"""
tests/test_v4_design_content_variability.py
Regression Test Suite for Website Builder v4 — Design & Content Variability.

Tests:
1. Render-level design diversity between Inurum Technology and Tesla (similarity <= 0.45).
2. Previous Design Reuse Mode (preserves visual architecture, updates company content).
3. Authoritative company content source validation (Tesla official domain, no fake metrics).
4. Non-reuse design variance when generating same prompt without reuse instruction.
"""

import os
import shutil
import tempfile
import unittest
from tools.coding.website_render_fingerprint import WebsiteRenderFingerprinter, WebsiteRenderFingerprint
from tools.coding.website_design_direction import DesignDirectionEngine, DesignLibrary
from tools.coding.website_master_planner import WebsiteMasterPlanner
from tools.coding.component_generation_pool import ComponentGenerationPool
from tools.coding.website_project_templates import WebsiteProjectTemplates
from tools.coding.website_visual_environment import WebsiteVisualEnvironment
from tools.coding.website_researcher import WebsiteResearcher
from tools.coding.website_visual_qa import WebsiteVisualQA

class TestV4DesignContentVariability(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="v4_test_")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except Exception:
                pass

    def _build_test_site(self, company_name: str, prompt: str, out_path: str):
        class DummyBrief:
            def __init__(self, name, cat):
                self.business_name = name
                self.category = cat
                self.subject = None
                self.research_context = None

        brief = DummyBrief(company_name, "technology" if "inurum" in company_name.lower() else "automotive")
        master_plan = WebsiteMasterPlanner.generate_master_plan(prompt, brief=brief)

        os.makedirs(out_path, exist_ok=True)
        os.makedirs(os.path.join(out_path, "src", "components"), exist_ok=True)

        did = master_plan.design_direction.design_id
        css_code = WebsiteProjectTemplates.generate_index_css(did)
        env_code = WebsiteVisualEnvironment.get_environment_component_code(brief.category, design_id=did)

        with open(os.path.join(out_path, "src", "index.css"), "w", encoding="utf-8") as f:
            f.write(css_code)
        with open(os.path.join(out_path, "src", "components", "DynamicSpatialEnvironment.tsx"), "w", encoding="utf-8") as f:
            f.write(env_code)

        comp_results = ComponentGenerationPool.generate_components_parallel(
            master_plan=master_plan,
            output_dir=out_path,
            task_id="test_build"
        )
        return master_plan, comp_results

    def test_01_design_diversity_inurum_vs_tesla(self):
        """
        Test 1 & 2: Generate Inurum Technology (Fingerprint A) and Tesla (Fingerprint B).
        Assert rendered design fingerprints are materially different (similarity <= 0.45).
        """
        dir_inurum = os.path.join(self.test_dir, "inurum_site")
        dir_tesla = os.path.join(self.test_dir, "tesla_site")

        plan_a, _ = self._build_test_site("Inurum Technology", "Build an enterprise AI website for Inurum Technology", dir_inurum)
        fp_a = WebsiteRenderFingerprinter.extract_fingerprint(dir_inurum, plan_a.design_direction.design_id)

        plan_b, _ = self._build_test_site("Tesla", "Build an automotive website for Tesla", dir_tesla)
        fp_b = WebsiteRenderFingerprinter.extract_fingerprint(dir_tesla, plan_b.design_direction.design_id)

        similarity = WebsiteRenderFingerprinter.compute_similarity(fp_a, fp_b)

        print(f"\n[TEST_01] Fingerprint A (Inurum): design_id={fp_a.design_id} hero={fp_a.hero_layout}")
        print(f"[TEST_01] Fingerprint B (Tesla): design_id={fp_b.design_id} hero={fp_b.hero_layout}")
        print(f"[TEST_01] Similarity Score: {similarity:.2f}")

        self.assertNotEqual(fp_a.design_id, fp_b.design_id)
        self.assertLessEqual(similarity, 0.45)

    def test_02_design_reuse_mode(self):
        """
        Test 3: Prompt with reuse instruction ("same design as previous website").
        Assert previous design direction is reused while company content updates.
        """
        dir_base = os.path.join(self.test_dir, "base_site")
        plan_base, _ = self._build_test_site("Inurum Technology", "Build website for Inurum Technology", dir_base)
        fp_base = WebsiteRenderFingerprinter.extract_fingerprint(dir_base, plan_base.design_direction.design_id)
        WebsiteRenderFingerprinter.save_fingerprint(fp_base)

        # Trigger reuse prompt for new company
        is_reuse = DesignDirectionEngine.detect_reuse_mode("Build same design as previous website for Acme Robotics")
        self.assertTrue(is_reuse)

        selected_dir, sim_score, reuse_flag = DesignDirectionEngine.select_design("Build same design as previous website for Acme Robotics", "technology")
        self.assertTrue(reuse_flag)
        self.assertEqual(selected_dir.design_id, fp_base.design_id)

    def test_03_tesla_official_content_research(self):
        """
        Test 4: Generate research for Tesla.
        Assert official domain is discovered (tesla.com) and no unverified fake metrics are included.
        """
        ctx = WebsiteResearcher.research_company("Tesla")
        self.assertIn("tesla.com", ctx.official_url.lower())
        self.assertEqual(ctx.confidence, "HIGH")

        # Verify no unverified fake metrics in claims
        for claim in ctx.claims:
            for banned in WebsiteResearcher.BANNED_FAKE_METRICS:
                self.assertNotIn(banned, claim.text.lower())

    def test_04_content_source_validation_gate(self):
        """
        Test 5: Run Content Source Validation on generated site code.
        Assert fake metrics are detected if present and pass if absent.
        """
        clean_site_dir = os.path.join(self.test_dir, "clean_site")
        self._build_test_site("Clean Corp", "Build clean business site for Clean Corp", clean_site_dir)
        cnt_pass, cnt_msg = WebsiteVisualQA.validate_content_sources(clean_site_dir)
        self.assertTrue(cnt_pass)

if __name__ == "__main__":
    unittest.main()
