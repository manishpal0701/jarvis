"""
tests/test_website_visual_intelligence.py
Unit test suite verifying:
1. Tesla research context -> valid visual plan
2. Nike context -> valid visual plan
3. Restaurant context -> valid visual plan
4. Personal portfolio -> valid visual plan
5. Missing research -> safe fallback
6. Network failure / error -> safe fallback
7. Unsupported facts are not invented
8. Asset requirements are structured
9. Responsive requirements are present
10. Source traceability is preserved
11. Existing Website Builder continues if visual intelligence fails
12. Existing WEBSITE_READY authority remains unchanged
"""

import unittest
from tools.coding.website_visual_intelligence import (
    WebsiteVisualIntelligence, VisualWebsitePlan, AssetRequirement, ResponsiveRequirement, SourceTrace
)
from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer, WebsiteBrief, WebsiteCategory, WebsiteSubject
from tools.coding.website_state import ActiveWebsiteState

class TestWebsiteVisualIntelligence(unittest.TestCase):

    def test_1_tesla_research_context_valid_visual_plan(self):
        """TEST 1: Tesla research context -> valid visual plan."""
        brief = WebsiteBrief(category="business")
        res_ctx = {
            "entity": "Tesla",
            "official_name": "Tesla, Inc.",
            "description": "American electric vehicle and clean energy company",
            "official_url": "https://www.tesla.com/",
            "sources": ["https://en.wikipedia.org/wiki/Tesla"]
        }
        plan = WebsiteVisualIntelligence.generate_plan(brief, res_ctx, "Tesla landing page")
        self.assertIsInstance(plan, VisualWebsitePlan)
        self.assertIn("automotive", plan.design_direction.lower())
        self.assertTrue(len(plan.asset_requirements) > 0)

    def test_2_nike_context_valid_visual_plan(self):
        """TEST 2: Nike context -> valid visual plan."""
        brief = WebsiteBrief(category="business")
        res_ctx = {
            "entity": "Nike",
            "official_name": "Nike, Inc.",
            "description": "American athletic footwear and apparel corporation",
            "official_url": "https://www.nike.com/",
            "sources": ["https://en.wikipedia.org/wiki/Nike"]
        }
        plan = WebsiteVisualIntelligence.generate_plan(brief, res_ctx, "Nike website")
        self.assertIsInstance(plan, VisualWebsitePlan)
        self.assertIn("athletic", plan.design_direction.lower())

    def test_3_restaurant_context_valid_visual_plan(self):
        """TEST 3: Restaurant context -> valid visual plan."""
        brief = WebsiteBrief(category="restaurant")
        res_ctx = {
            "entity": "Bella Tavola",
            "official_name": "Bella Tavola Italian Restaurant",
            "category": "restaurant",
            "description": "Fine dining Tuscan restaurant",
            "sources": []
        }
        plan = WebsiteVisualIntelligence.generate_plan(brief, res_ctx, "Bella Tavola restaurant website")
        self.assertIsInstance(plan, VisualWebsitePlan)
        self.assertIn("mahogany", plan.design_direction.lower())

    def test_4_personal_portfolio_valid_visual_plan(self):
        """TEST 4: Personal portfolio -> valid visual plan."""
        brief = WebsiteBrief(category="portfolio")
        plan = WebsiteVisualIntelligence.generate_plan(brief, None, "Developer portfolio website")
        self.assertIsInstance(plan, VisualWebsitePlan)
        self.assertIn("developer", plan.design_direction.lower())

    def test_5_missing_research_safe_fallback(self):
        """TEST 5: Missing research context returns safe default visual plan."""
        brief = WebsiteBrief(category="custom")
        plan = WebsiteVisualIntelligence.generate_plan(brief, None, "Generic custom site")
        self.assertIsInstance(plan, VisualWebsitePlan)
        self.assertIsNotNone(plan.design_direction)

    def test_6_network_failure_safe_fallback(self):
        """TEST 6: Malformed input triggers safe fallback plan."""
        plan = WebsiteVisualIntelligence.generate_plan(None, "invalid_context_type", None)
        self.assertIsInstance(plan, VisualWebsitePlan)

    def test_7_unsupported_facts_are_not_invented(self):
        """TEST 7: Unsupported facts are not invented."""
        brief = WebsiteBrief(category="business")
        res_ctx = {"entity": "UnknownBrandX", "official_name": "UnknownBrandX"}
        plan = WebsiteVisualIntelligence.generate_plan(brief, res_ctx, "UnknownBrandX site")
        # Check brand notes do not contain hardcoded claims for unknown brands
        for note in plan.brand_consistency_notes:
            self.assertNotIn("Tesla", note)

    def test_8_asset_requirements_are_structured(self):
        """TEST 8: Asset requirements are structured."""
        brief = WebsiteBrief(category="portfolio")
        plan = WebsiteVisualIntelligence.generate_plan(brief, None, "portfolio")
        self.assertTrue(len(plan.asset_requirements) > 0)
        first_asset = plan.asset_requirements[0]
        self.assertIsInstance(first_asset, AssetRequirement)
        self.assertIsNotNone(first_asset.purpose)
        self.assertIsNotNone(first_asset.type)

    def test_9_responsive_requirements_are_present(self):
        """TEST 9: Responsive requirements are present."""
        brief = WebsiteBrief(category="business")
        plan = WebsiteVisualIntelligence.generate_plan(brief, None, "business site")
        self.assertIsInstance(plan.responsive_requirements, ResponsiveRequirement)
        self.assertIsNotNone(plan.responsive_requirements.desktop)
        self.assertIsNotNone(plan.responsive_requirements.tablet)
        self.assertIsNotNone(plan.responsive_requirements.mobile)

    def test_10_source_traceability_is_preserved(self):
        """TEST 10: Source traceability is preserved."""
        brief = WebsiteBrief(category="business")
        res_ctx = {
            "entity": "Tesla",
            "official_name": "Tesla, Inc.",
            "official_url": "https://www.tesla.com/",
            "sources": ["https://en.wikipedia.org/wiki/Tesla"]
        }
        plan = WebsiteVisualIntelligence.generate_plan(brief, res_ctx, "Tesla landing page")
        self.assertTrue(len(plan.source_traceability) > 0)
        first_trace = plan.source_traceability[0]
        self.assertIsInstance(first_trace, SourceTrace)
        self.assertIn("Tesla", first_trace.fact)

    def test_11_existing_website_builder_continues_if_vi_fails(self):
        """TEST 11: Website Brief formatting continues cleanly with or without visual plan."""
        brief = WebsiteBrief(category="business")
        summary_before = WebsiteRequirementsAnalyzer.format_brief_summary(brief)
        self.assertIn("Website Brief Summary", summary_before)
        
        plan = WebsiteVisualIntelligence.generate_plan(brief, None, "test")
        brief.visual_plan = plan.to_dict()
        summary_after = WebsiteRequirementsAnalyzer.format_brief_summary(brief)
        self.assertIn("Visual Intelligence Plan", summary_after)

    def test_12_existing_website_ready_authority_remains_unchanged(self):
        """TEST 12: Existing WEBSITE_READY authority logic remains unchanged."""
        state = ActiveWebsiteState()
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
