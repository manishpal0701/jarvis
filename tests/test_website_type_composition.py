import unittest
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer, WebsiteCategory, WebsiteSubject, SubjectType
from tools.coding.website_master_planner import WebsiteMasterPlanner
from tools.coding.website_planner import WebsiteProjectPlanner
from tools.coding.component_generation_pool import ComponentGenerationPool, ComponentSpec, ContentLinter
from tools.coding.anti_template_checker import AntiTemplateChecker
from tools.coding.client_brief_ingestion import ClientBriefParser
from tools.coding.website_design_direction import DesignDirectionEngine

class TestWebsiteTypeComposition(unittest.TestCase):
    """
    Test suite verifying WEBSITE_TYPE controls information architecture + composition,
    not just colors or content.
    """

    # 1. Developer portfolio classification
    def test_01_developer_portfolio_classification(self):
        cat = WebsiteRequirementsAnalyzer.detect_category("Create a developer portfolio for Manish")
        self.assertIn(cat.value, ["developer_portfolio", "portfolio"])

    # 2. Business classification
    def test_02_business_classification(self):
        cat = WebsiteRequirementsAnalyzer.detect_category("Create a website for NovaStack Technologies, a software company")
        self.assertIn(cat.value, ["business_website", "business", "company"])

    # 3. Product classification
    def test_03_product_classification(self):
        cat = WebsiteRequirementsAnalyzer.detect_category("Create a website for a new AI productivity product")
        self.assertIn(cat.value, ["product_website", "product"])

    # 4. Cafe classification
    def test_04_cafe_classification(self):
        cat = WebsiteRequirementsAnalyzer.detect_category("Create a website for Kasyap Everfresh Cafe")
        self.assertIn(cat.value, ["restaurant_cafe", "restaurant", "cafe"])

    # 5. Service classification
    def test_05_service_classification(self):
        cat = WebsiteRequirementsAnalyzer.detect_category("Create a service business website for legal consulting firm")
        self.assertIn(cat.value, ["service_business", "service"])

    # 6. Agency classification
    def test_06_agency_classification(self):
        cat = WebsiteRequirementsAnalyzer.detect_category("Create a website for a digital marketing agency")
        self.assertIn(cat.value, ["agency_website", "agency"])

    # 7. Different section architecture per type
    def test_07_different_section_architecture_per_type(self):
        task_dev = "Create a developer portfolio for Manish"
        brief_dev = WebsiteRequirementsAnalyzer.extract_information(task_dev, WebsiteCategory.DEVELOPER_PORTFOLIO, WebsiteSubject(name="Manish"))
        plan_dev = WebsiteMasterPlanner.generate_master_plan(task_dev, brief_dev)
        sections_dev = [c.name for c in plan_dev.components]

        task_biz = "Create a website for NovaStack Technologies, a software company"
        brief_biz = WebsiteRequirementsAnalyzer.extract_information(task_biz, WebsiteCategory.BUSINESS_WEBSITE, WebsiteSubject(name="NovaStack Technologies"))
        plan_biz = WebsiteMasterPlanner.generate_master_plan(task_biz, brief_biz)
        sections_biz = [c.name for c in plan_biz.components]

        task_prod = "Create a website for a new AI productivity product"
        brief_prod = WebsiteRequirementsAnalyzer.extract_information(task_prod, WebsiteCategory.PRODUCT_WEBSITE, WebsiteSubject(name="AI Productivity Product"))
        plan_prod = WebsiteMasterPlanner.generate_master_plan(task_prod, brief_prod)
        sections_prod = [c.name for c in plan_prod.components]

        task_cafe = "Create a website for Kasyap Everfresh Cafe"
        brief_cafe = WebsiteRequirementsAnalyzer.extract_information(task_cafe, WebsiteCategory.RESTAURANT_CAFE, WebsiteSubject(name="Kasyap Everfresh Cafe"))
        plan_cafe = WebsiteMasterPlanner.generate_master_plan(task_cafe, brief_cafe)
        sections_cafe = [c.name for c in plan_cafe.components]

        # Ensure section compositions are distinct
        self.assertNotEqual(sections_dev, sections_biz)
        self.assertNotEqual(sections_dev, sections_prod)
        self.assertNotEqual(sections_biz, sections_cafe)

    # 8. Portfolio fallback is NOT used for business
    def test_08_portfolio_fallback_not_used_for_business(self):
        task_biz = "Create a website for NovaStack Technologies, a software company"
        brief_biz = WebsiteRequirementsAnalyzer.extract_information(task_biz, WebsiteCategory.BUSINESS_WEBSITE, WebsiteSubject(name="NovaStack Technologies"))
        plan_biz = WebsiteMasterPlanner.generate_master_plan(task_biz, brief_biz)
        component_names = [c.name for c in plan_biz.components]

        self.assertNotIn("DeveloperHero", component_names)
        self.assertNotIn("TechnicalBio", component_names)
        self.assertNotIn("SkillMatrix", component_names)
        self.assertNotIn("FeaturedProjects", component_names)

        # Check deterministic fallback code
        spec = ComponentSpec(name="BusinessHero", file_path="src/components/BusinessHero.tsx", role="Corporate Hero")
        code = ComponentGenerationPool._deterministic_component(spec, plan_biz)
        self.assertNotIn("MANISH", code)
        self.assertNotIn("CodeTerminal", code)

    # 9. Portfolio fallback is NOT used for product
    def test_09_portfolio_fallback_not_used_for_product(self):
        task_prod = "Create a website for a new AI productivity product"
        brief_prod = WebsiteRequirementsAnalyzer.extract_information(task_prod, WebsiteCategory.PRODUCT_WEBSITE, WebsiteSubject(name="FlowAI Product"))
        plan_prod = WebsiteMasterPlanner.generate_master_plan(task_prod, brief_prod)
        component_names = [c.name for c in plan_prod.components]

        self.assertNotIn("DeveloperHero", component_names)
        self.assertNotIn("SkillMatrix", component_names)
        self.assertIn("ProductHero", component_names)
        self.assertIn("ProblemSolution", component_names)

        spec = ComponentSpec(name="ProductHero", file_path="src/components/ProductHero.tsx", role="Product Hero")
        code = ComponentGenerationPool._deterministic_component(spec, plan_prod)
        self.assertNotIn("MANISH", code)
        self.assertNotIn("CodeTerminal", code)

    # 10. Reference does not override website type
    def test_10_reference_does_not_override_website_type(self):
        # Reference is developer portfolio, but prompt is cafe
        cmd = "Create a website for Kasyap Everfresh Cafe with visual reference of dark cyan portfolio"
        brief_cafe = WebsiteRequirementsAnalyzer.extract_information(cmd, WebsiteCategory.RESTAURANT_CAFE, WebsiteSubject(name="Kasyap Everfresh Cafe"))
        plan_cafe = WebsiteMasterPlanner.generate_master_plan(cmd, brief_cafe)
        component_names = [c.name for c in plan_cafe.components]

        self.assertIn("SignatureDishes", component_names)
        self.assertNotIn("SkillMatrix", component_names)

    # 11. Zero fabrication
    def test_11_zero_fabrication(self):
        code = "export const Test = () => <div>99.99% uptime 10M+ users SOC2 certified</div>;"
        ok, reason = ContentLinter.lint_component_code(code, "TestComponent", category="business")
        self.assertFalse(ok)
        self.assertIn("BANNED_CONTENT_PATTERN_DETECTED", reason)

    # 12. Existing portfolio generation still passes
    def test_12_existing_portfolio_generation_still_passes(self):
        task_dev = "Create a developer portfolio for Manish"
        brief_dev = WebsiteRequirementsAnalyzer.extract_information(task_dev, WebsiteCategory.DEVELOPER_PORTFOLIO, WebsiteSubject(name="Manish"))
        plan_dev = WebsiteMasterPlanner.generate_master_plan(task_dev, brief_dev)
        component_names = [c.name for c in plan_dev.components]

        self.assertIn("DeveloperHero", component_names)
        self.assertIn("SkillMatrix", component_names)
        self.assertIn("FeaturedProjects", component_names)

if __name__ == "__main__":
    unittest.main()
