import unittest
from ai.model_router import ModelRouter
from tools.coding.website_researcher import WebsiteResearcher
from tools.coding.website_content_strategist import WebsiteContentStrategist
from tools.coding.website_design_system import WebsiteDesignSystemGenerator

class TestWebsiteResearcher(unittest.TestCase):
    def test_01_model_router_mapping(self):
        router = ModelRouter.get_instance()
        self.assertEqual(router.get_model_for_task("website_research"), "qwen3:8b")
        self.assertEqual(router.get_model_for_task("website_generation"), "qwen3:4b-instruct")
        self.assertEqual(router.get_model_for_task("intent_classification"), "phi4-mini:latest")
        self.assertEqual(router.get_model_for_task("conversation"), "qwen3:8b")

    def test_02_conduct_research_portfolio(self):
        spec = WebsiteResearcher.conduct_research("Jarvis, mera ek portfolio bana do", category="portfolio")
        self.assertEqual(spec.website_type, "developer_portfolio")
        self.assertIn("Hero", spec.sections)
        self.assertIn("Featured Projects", spec.sections)

    def test_03_content_strategist(self):
        research = WebsiteResearcher.conduct_research("Manish portfolio", category="portfolio")
        content = WebsiteContentStrategist.generate_content_strategy(research, "Manish portfolio")
        self.assertEqual(content.person_or_brand_name, "Manish")
        self.assertIn("Navbar", content.sections_content)

    def test_04_design_system(self):
        research = WebsiteResearcher.conduct_research("Developer Portfolio", category="portfolio")
        ds = WebsiteDesignSystemGenerator.generate_design_system(research, "Developer Portfolio")
        self.assertEqual(ds.theme_name, "dark_developer")

    def test_05_conduct_research_restaurant(self):
        spec = WebsiteResearcher.conduct_research("Jarvis, ek premium modern Italian restaurant ki website bana do. Bella Tavola.", category="restaurant")
        self.assertEqual(spec.website_type, "luxurious_italian_restaurant")
        self.assertIn("SignatureDishes", spec.sections)
        self.assertIn("TableReservation", spec.sections)

        ds = WebsiteDesignSystemGenerator.generate_design_system(spec, "Bella Tavola Italian Restaurant")
        self.assertEqual(ds.theme_name, "luxurious_gastronomy")
        self.assertEqual(ds.primary_color, "#f59e0b")

if __name__ == "__main__":
    unittest.main()
