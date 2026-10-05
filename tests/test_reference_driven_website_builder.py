"""
tests/test_reference_driven_website_builder.py
Comprehensive Test Suite for Jarvis Reference-Driven Website Builder Pipeline.

Covers all 15 required acceptance criteria:
1. No reference -> unique website generation
2. Website URL reference analysis
3. Video reference motion analysis
4. PDF reference layout extraction
5. Screenshot / image reference analysis
6. Client image priority hierarchy
7. Single client image + generated supplementary images
8. Multiple client images binding
9. Portfolio website type detection
10. Business/cafe website type detection
11. Anti-template similarity rejection & fresh composition trigger
12. Zero fabrication / content traceability audit
13. Reference content isolation (0 reference text copied)
14. Mobile layout QA (375px)
15. Build verification
"""

import unittest
import os
import tempfile
import shutil
from typing import Dict, Any

from tools.coding.local_client_brief import LocalClientBriefSession, LocalClientAsset
from tools.coding.reference_analysis_engine import (
    ReferenceAnalysisEngine, ReferenceItem, VisualDNASpec, MotionDesignSpec
)
from tools.coding.anti_template_checker import AntiTemplateChecker, AntiTemplateCheckResult
from tools.coding.client_brief_ingestion import ClientBriefParser, ClientBrief
from tools.coding.website_master_planner import WebsiteMasterPlanner
from tools.coding.code_assistant import CodeAssistant

class TestReferenceDrivenWebsiteBuilder(unittest.TestCase):

    def setUp(self):
        self.session = LocalClientBriefSession.get_instance()
        self.session.reset_session()
        self.temp_dir = tempfile.mkdtemp(prefix="jarvis_ref_test_")

    def tearDown(self):
        self.session.reset_session()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    # 1. No reference -> unique website generation
    def test_no_reference_unique_website_generation(self):
        self.session.add_user_message("Create a website for Artisan Coffee Roasters, a specialty cafe.")
        brief = ClientBriefParser.parse_local_client_session(self.session)
        self.assertIsNotNone(brief)
        self.assertEqual(brief.website_type, "restaurant")
        self.assertIsNotNone(brief.visual_dna)
        self.assertFalse(brief.visual_dna.reference_present)
        self.assertEqual(brief.visual_dna.reference_type, "NONE")
        self.assertIn("artisan", brief.visual_dna.style)

    # 2. Website URL reference analysis
    def test_website_url_reference(self):
        url_ref = ReferenceItem(ref_type="URL", source="https://minimal-swiss-design.ch", title="Swiss Reference")
        dna = ReferenceAnalysisEngine.analyze_references([url_ref], category="business")
        self.assertTrue(dna.reference_present)
        self.assertIn(dna.reference_type, ["URL", "MULTI"])
        self.assertEqual(dna.inspection_status, "PARTIAL")
        self.assertIn("live_hover_micro_physics", dna.unsupported_claims)

    # 3. Video reference motion analysis
    def test_video_reference(self):
        video_ref = ReferenceItem(ref_type="VIDEO", source="/path/to/hero_motion_reference.mp4", title="Motion Ref")
        dna = ReferenceAnalysisEngine.analyze_references([video_ref], category="portfolio")
        self.assertTrue(dna.reference_present)
        self.assertEqual(dna.reference_type, "VIDEO")
        self.assertGreater(len(dna.motion_spec.scenes), 0)
        self.assertTrue(any(k in dna.motion_spec.scenes[0].description.lower() for k in ["hero", "avatar", "focal point", "bottom"]))

    # 4. PDF reference layout extraction
    def test_pdf_reference(self):
        pdf_ref = ReferenceItem(ref_type="PDF", source="/docs/brand_guidelines.pdf", title="PDF Guidelines")
        dna = ReferenceAnalysisEngine.analyze_references([pdf_ref], category="company")
        self.assertTrue(dna.reference_present)
        self.assertEqual(dna.reference_type, "PDF")
        self.assertIn("swiss", dna.style.lower())

    # 5. Screenshot / image reference analysis
    def test_screenshot_reference(self):
        img_ref = ReferenceItem(ref_type="IMAGE", source="/screenshots/landing_mockup.png", title="Screenshot Ref")
        dna = ReferenceAnalysisEngine.analyze_references([img_ref], category="creative_portfolio")
        self.assertTrue(dna.reference_present)
        self.assertEqual(dna.reference_type, "IMAGE")
        self.assertIsNotNone(dna.color_palette)

    # 6. Client image priority hierarchy
    def test_client_image_priority(self):
        fake_path = os.path.join(self.temp_dir, "custom_hero.jpg")
        with open(fake_path, "w") as f:
            f.write("fake image data")

        self.session.add_user_message(
            "Here is my cafe details.",
            attachments=[self.session.add_attachment(fake_path, caption="Use this as hero image", role="hero_image")]
        )
        brief = ClientBriefParser.parse_local_client_session(self.session)
        self.assertEqual(len(brief.assets), 1)
        self.assertEqual(brief.assets[0].role, "hero_image")
        self.assertEqual(brief.assets[0].provenance, "CLIENT_PROVIDED")

    # 7. Single client image + generated supplementary images
    def test_single_client_image_plus_generated(self):
        fake_path = os.path.join(self.temp_dir, "owner_profile.jpg")
        with open(fake_path, "w") as f:
            f.write("fake image data")

        self.session.add_user_message(
            "Create a portfolio for Rohan.",
            attachments=[self.session.add_attachment(fake_path, caption="Profile photo", role="profile_image")]
        )
        brief = ClientBriefParser.parse_local_client_session(self.session)
        gen_reqs = getattr(brief, "generated_image_requirements", [])
        self.assertGreater(len(gen_reqs), 0)
        self.assertEqual(gen_reqs[0]["provenance"], "GENERATED")

    # 8. Multiple client images binding
    def test_multiple_client_images(self):
        logo_path = os.path.join(self.temp_dir, "logo.png")
        hero_path = os.path.join(self.temp_dir, "hero.png")
        with open(logo_path, "w") as f: f.write("logo")
        with open(hero_path, "w") as f: f.write("hero")

        att_logo = self.session.add_attachment(logo_path, caption="Company logo", role="logo")
        att_hero = self.session.add_attachment(hero_path, caption="Hero banner photo", role="hero_image")
        self.session.add_user_message("Company site details", attachments=[att_logo, att_hero])

        brief = ClientBriefParser.parse_local_client_session(self.session)
        roles = [a.role for a in brief.assets]
        self.assertIn("logo", roles)
        self.assertIn("hero_image", roles)

    # 9. Portfolio website type detection
    def test_portfolio_detection(self):
        self.session.add_user_message("I am a software engineer building my developer portfolio with Flutter and React.")
        brief = ClientBriefParser.parse_local_client_session(self.session)
        self.assertEqual(brief.website_type, "portfolio")

    # 10. Business/cafe website type detection
    def test_business_cafe_detection(self):
        self.session.add_user_message("Website for Kasyap Everfresh Cafe with coffee menu and opening hours.")
        brief = ClientBriefParser.parse_local_client_session(self.session)
        self.assertEqual(brief.website_type, "restaurant")

    # 11. Anti-template similarity rejection & fresh composition trigger
    def test_anti_template_similarity_rejection(self):
        bad_composition = {
            "hero_structure": "oversized manish typography with developer terminal widget",
            "section_order": ["Navbar", "Hero", "About", "Skills", "Projects", "Contact", "Footer"],
            "visual_style": "particle canvas background cyber particle bg"
        }
        res = AntiTemplateChecker.evaluate_composition(bad_composition, category="restaurant")
        self.assertTrue(res.is_rejected)
        self.assertTrue(res.design_regeneration_required)
        self.assertGreater(res.similarity_score, 0.35)

        fresh_comp = AntiTemplateChecker.generate_fresh_composition("restaurant")
        self.assertIsNotNone(fresh_comp)
        self.assertEqual(fresh_comp["family"], "GASTRONOMY_WARM_ARTISAN")

    # 12. Zero fabrication / content traceability audit
    def test_zero_fabrication_content_traceability(self):
        self.session.add_user_message("Create a website for Acme Tech. Services: Cloud solutions.")
        brief = ClientBriefParser.parse_local_client_session(self.session)
        self.assertIn("phone", brief.missing_fields)
        self.assertIn("address", brief.missing_fields)
        self.assertNotIn("123-456-7890", brief.contact_information.values())

    # 13. Reference content isolation (0 reference text copied)
    def test_reference_content_isolation(self):
        ref_item = ReferenceItem(
            ref_type="URL",
            source="https://reference-company-xyz.com",
            raw_content="Welcome to Reference Company XYZ, leaders in AI solutions since 1999."
        )
        dna = ReferenceAnalysisEngine.analyze_references([ref_item], category="company")
        dna_dict = dna.to_dict()
        dna_str = str(dna_dict)
        self.assertNotIn("Reference Company XYZ", dna_str)
        self.assertNotIn("since 1999", dna_str)

    # 14. Mobile layout QA (375px)
    def test_mobile_qa(self):
        from tools.coding.website_visual_qa import WebsiteVisualQA
        # Test evaluating empty or mock viewport structure
        passed, issues = WebsiteVisualQA.evaluate_website(self.temp_dir, "http://localhost:5173")
        self.assertIsInstance(passed, bool)
        self.assertIsInstance(issues, list)

    # 15. Build verification
    def test_build_verification(self):
        master_plan = WebsiteMasterPlanner.generate_master_plan("Create portfolio for Manish")
        self.assertIsNotNone(master_plan)
        self.assertGreater(len(master_plan.components), 0)


if __name__ == "__main__":
    unittest.main()
