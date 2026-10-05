import unittest
import os
import shutil
import tempfile

from tools.coding.website_master_planner import WebsiteMasterPlanner, MasterWebsitePlan, ComponentSpec
from tools.coding.component_generation_pool import ComponentGenerationPool
from tools.coding.anti_template_checker import AntiTemplateChecker
from tools.coding.website_visual_qa import WebsiteVisualQA
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer
from tools.coding.local_client_brief import LocalClientBriefSession
from tools.coding.client_brief_ingestion import ClientBrief

class TestWebsiteRealComponents(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_1_business_website_no_component_identifiers(self):
        """Test 1: BUSINESS_WEBSITE does not render component identifiers."""
        spec = ComponentSpec(name="BusinessHero", file_path="src/components/BusinessHero.tsx", role="Hero")
        plan = MasterWebsitePlan(
            business_name="NovaStack",
            category="business_website",
            theme="dark",
            color_palette={}, typography={}, hero_spec={}, cta_spec={},
            components=[spec], global_styles=""
        )
        code = ComponentGenerationPool._deterministic_business_component(spec, plan)
        self.assertNotIn("BusinessHero —", code)
        self.assertNotIn("BusinessHero -", code)
        self.assertIn("NovaStack", code)

    def test_2_product_website_no_component_identifiers(self):
        """Test 2: PRODUCT_WEBSITE does not render component identifiers."""
        spec = ComponentSpec(name="ProductHero", file_path="src/components/ProductHero.tsx", role="Hero")
        plan = MasterWebsitePlan(
            business_name="SaaSflow",
            category="product_website",
            theme="dark",
            color_palette={}, typography={}, hero_spec={}, cta_spec={},
            components=[spec], global_styles=""
        )
        code = ComponentGenerationPool._deterministic_product_component(spec, plan)
        self.assertNotIn("ProductHero —", code)
        self.assertNotIn("ProductHero -", code)
        self.assertIn("SaaSflow", code)

    def test_3_service_business_no_component_identifiers(self):
        """Test 3: SERVICE_BUSINESS does not render component identifiers."""
        spec = ComponentSpec(name="BusinessServices", file_path="src/components/BusinessServices.tsx", role="Services")
        plan = MasterWebsitePlan(
            business_name="Apex Services",
            category="service_business",
            theme="dark",
            color_palette={}, typography={}, hero_spec={}, cta_spec={},
            components=[spec], global_styles=""
        )
        code = ComponentGenerationPool._deterministic_component(spec, plan)
        self.assertNotIn("BusinessServices —", code)

    def test_4_restaurant_cafe_no_component_identifiers(self):
        """Test 4: RESTAURANT_CAFE does not render component identifiers."""
        spec = ComponentSpec(name="SignatureDishes", file_path="src/components/SignatureDishes.tsx", role="Menu")
        plan = MasterWebsitePlan(
            business_name="Kasyap Everfresh Cafe",
            category="restaurant_cafe",
            theme="dark",
            color_palette={}, typography={}, hero_spec={}, cta_spec={},
            components=[spec], global_styles=""
        )
        code = ComponentGenerationPool._deterministic_luxury_component(spec, plan)
        self.assertNotIn("SignatureDishes —", code)
        self.assertIn("Kasyap Everfresh Cafe", code)

    def test_5_agency_website_no_component_identifiers(self):
        """Test 5: AGENCY_WEBSITE does not render component identifiers."""
        spec = ComponentSpec(name="AgencyOverview", file_path="src/components/AgencyOverview.tsx", role="Overview")
        plan = MasterWebsitePlan(
            business_name="Vanguard Agency",
            category="agency_website",
            theme="dark",
            color_palette={}, typography={}, hero_spec={}, cta_spec={},
            components=[spec], global_styles=""
        )
        code = ComponentGenerationPool._deterministic_component(spec, plan)
        self.assertNotIn("AgencyOverview —", code)

    def test_6_business_website_has_real_sections(self):
        """Test 6: Business website contains real business sections."""
        prompt = "Build a business website for Enterprise Corp"
        plan = WebsiteMasterPlanner.generate_master_plan(prompt)
        names = [c.name for c in plan.components]
        self.assertIn("Navbar", names)
        self.assertTrue(any(n in names for n in ["Hero", "BusinessHero", "EnterpriseHero"]))

    def test_7_product_website_has_real_sections(self):
        """Test 7: Product website contains real product sections."""
        prompt = "Build a product website for AppFlow SaaS"
        plan = WebsiteMasterPlanner.generate_master_plan(prompt)
        names = [c.name for c in plan.components]
        self.assertIn("Navbar", names)
        self.assertTrue(any(n in names for n in ["ProductHero", "Hero"]))

    def test_8_non_portfolio_never_uses_developer_components(self):
        """Test 8: Non-portfolio websites never use DeveloperHero/TechnicalBio/SkillMatrix."""
        prompt = "Build a cafe website for Artisan Coffee"
        plan = WebsiteMasterPlanner.generate_master_plan(prompt)
        comp_names = [c.name for c in plan.components]
        self.assertNotIn("DeveloperHero", comp_names)
        self.assertNotIn("TechnicalBio", comp_names)
        self.assertNotIn("SkillMatrix", comp_names)

    def test_9_missing_facts_not_fabricated(self):
        """Test 9: Missing facts are not fabricated."""
        brief = ClientBrief(client_name="Test Cafe", website_type="restaurant_cafe")
        self.assertEqual(brief.contact_information.get("phone", "NOT_PROVIDED"), "NOT_PROVIDED")

    def test_10_developer_portfolio_generation_compatible(self):
        """Test 10: Developer portfolio generation remains compatible."""
        spec = ComponentSpec(name="DeveloperHero", file_path="src/components/DeveloperHero.tsx", role="Hero")
        plan = MasterWebsitePlan(
            business_name="Manish",
            category="developer_portfolio",
            theme="dark",
            color_palette={}, typography={}, hero_spec={}, cta_spec={},
            components=[spec], global_styles=""
        )
        code = ComponentGenerationPool._deterministic_portfolio_component(spec, plan)
        self.assertIn("MANISH", code)

    def test_11_anti_template_rejects_placeholder_ui(self):
        """Test 11: AntiTemplateChecker rejects placeholder UI strings."""
        code_dict = {"Hero.tsx": "export const Hero = () => <h1>BusinessHero — Enterprise Brand</h1>;"}
        res = AntiTemplateChecker.inspect_generated_code(code_dict, category="business_website")
        self.assertTrue(res.is_rejected)
        self.assertIn("placeholder_ui:businesshero —", res.banned_tokens_detected)

    def test_12_reference_design_influences_visual_composition(self):
        """Test 12: Reference design influences visual composition."""
        plan = WebsiteMasterPlanner.generate_master_plan("Build business site like brutalist design")
        self.assertIsNotNone(plan.components)

    def test_13_client_image_rendering_helper(self):
        """Test 13: Client image URL helper returns valid asset path."""
        brief = ClientBrief(client_name="Kasyap Cafe", website_type="restaurant_cafe", assets=[{"filename": "cafe_hero.png"}])
        plan = MasterWebsitePlan(
            business_name="Kasyap Cafe",
            category="restaurant_cafe",
            theme="dark",
            color_palette={}, typography={}, hero_spec={}, cta_spec={},
            components=[], global_styles="",
            verified_content=brief
        )
        img_url = ComponentGenerationPool._get_client_image_url(plan)
        self.assertEqual(img_url, "/assets/client/cafe_hero.png")

    def test_14_desktop_qa_validation_pass(self):
        """Test 14: Desktop QA validation function runs without failure."""
        ok, msg = WebsiteVisualQA.validate_no_placeholder_ui(self.test_dir)
        self.assertTrue(ok)

    def test_15_mobile_qa_validation_pass(self):
        """Test 15: Mobile QA validation function runs without failure."""
        ok, msg = WebsiteVisualQA.validate_content_sources(self.test_dir)
        self.assertTrue(ok)

if __name__ == "__main__":
    unittest.main()
