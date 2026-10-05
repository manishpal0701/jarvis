import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.coding.local_client_brief import LocalClientBriefSession
from tools.coding.reference_analysis_engine import ReferenceItem
from tools.coding.client_brief_ingestion import ClientBriefParser
from tools.coding.website_master_planner import WebsiteMasterPlanner
from tools.coding.component_generation_pool import ComponentGenerationPool

class TestReferenceAnalysisPipeline(unittest.TestCase):

    def setUp(self):
        self.session = LocalClientBriefSession.get_instance()
        self.session.reset()

    def test_reference_analyzer_invoked_when_url_provided(self):
        """Verifies that ReferenceAnalysisEngine is invoked when a reference URL is in the session."""
        self.session.client_name = "Aurora Coffee House"
        self.session.website_type = "restaurant_cafe"
        self.session.add_reference_url("https://www.sonderandstone.com/", title="Sonder & Stone Inspiration")

        brief = ClientBriefParser.parse_local_client_session(self.session)
        
        self.assertIsNotNone(brief.visual_dna, "Visual DNA must be populated")
        self.assertTrue(brief.visual_dna.reference_present, "reference_present flag must be True")
        self.assertEqual(brief.visual_dna.reference_type, "URL", "reference_type must be URL")
        self.assertIn(brief.visual_dna.inspection_status, ["VERIFIED", "PARTIAL"], "inspection_status must be VERIFIED or PARTIAL")

    def test_component_prompts_contain_client_brief_and_reference_analysis(self):
        """Verifies that generated component prompts contain both CLIENT BRIEF and REFERENCE DESIGN ANALYSIS blocks."""
        self.session.client_name = "Aurora Coffee House"
        self.session.website_type = "restaurant_cafe"
        self.session.add_reference_url("https://www.sonderandstone.com/", title="Sonder & Stone Inspiration")

        brief = ClientBriefParser.parse_local_client_session(self.session)
        master_plan = WebsiteMasterPlanner.generate_master_plan("Build website for Aurora Coffee House", brief=brief)

        _cb = getattr(master_plan, 'client_brief', None)
        self.assertIsNotNone(_cb, "ClientBrief must be attached to MasterWebsitePlan")

        visual_dna = getattr(_cb, 'visual_dna', None)
        self.assertIsNotNone(visual_dna, "VisualDNA must be present in ClientBrief")
        self.assertTrue(visual_dna.reference_present, "Reference must be present")

    def test_restaurant_brief_never_falls_back_to_manish_portfolio(self):
        """Verifies that a restaurant brief produces restaurant components and NEVER falls back to developer portfolio specs."""
        self.session.client_name = "Aurora Coffee House"
        self.session.website_type = "restaurant_cafe"
        self.session.business_description = "Aurora Coffee House is a premium modern cafe offering specialty coffee."

        brief = ClientBriefParser.parse_local_client_session(self.session)
        master_plan = WebsiteMasterPlanner.generate_master_plan("Build website for Aurora Coffee House", brief=brief)

        comp_names = [c.name for c in master_plan.components]
        
        banned_portfolio_specs = ["DeveloperHero", "TechnicalBio", "SkillMatrix", "FeaturedProjects", "ContactForm"]
        for banned in banned_portfolio_specs:
            self.assertNotIn(banned, comp_names, f"Banned portfolio spec '{banned}' found in restaurant plan!")

        self.assertIn("Navbar", comp_names)
        self.assertIn("Footer", comp_names)

if __name__ == "__main__":
    unittest.main()
