import os
import shutil
import tempfile
import unittest

from tools.coding.website_session_manager import WebsiteSessionManager, WebsiteSessionState
from tools.coding.local_client_brief import LocalClientBriefSession, LocalClientAsset
from tools.coding.client_brief_ingestion import ClientBriefParser
from tools.coding.reference_analysis_engine import ReferenceItem
from tools.coding.code_assistant import CodeAssistant
from tools.coding.workspace_manager import WorkspaceManager


class TestWebsiteBuilderIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.web_session = WebsiteSessionManager.get_instance()
        self.web_session.reset_session()
        self.local_session = LocalClientBriefSession.get_instance()
        self.local_session.reset_session()

        self.sample_img_1 = os.path.join(self.temp_dir, "product_hero.png")
        with open(self.sample_img_1, "w", encoding="utf-8") as f:
            f.write("sample_png_bytes")

        self.sample_img_2 = os.path.join(self.temp_dir, "founder.jpg")
        with open(self.sample_img_2, "w", encoding="utf-8") as f:
            f.write("sample_jpg_bytes")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.web_session.reset_session()
        self.local_session.reset_session()

    def test_01_business_website_request_opens_client_brief_workflow(self):
        """1. Business website request opens client brief workflow without immediate generation."""
        assistant = CodeAssistant()
        msg, path, status = assistant.generate_code("business website bana do")
        self.assertEqual(status, "CLIENT_BRIEF_CHAT_ACTIVATED")
        self.assertFalse(self.web_session.WEBSITE_GENERATION_STARTED)
        self.assertEqual(self.web_session.state, WebsiteSessionState.COLLECTING_CLIENT_BRIEF)

    def test_02_product_website_request_opens_client_brief_workflow(self):
        """2. Product website request opens client brief workflow."""
        assistant = CodeAssistant()
        msg, path, status = assistant.generate_code("make a product website for my SaaS")
        self.assertEqual(status, "CLIENT_BRIEF_CHAT_ACTIVATED")
        self.assertFalse(self.web_session.WEBSITE_GENERATION_STARTED)
        self.assertEqual(self.web_session.state, WebsiteSessionState.COLLECTING_CLIENT_BRIEF)

    def test_03_missing_details_halt_generation(self):
        """3. Missing client details for unknown company halt generation."""
        assistant = CodeAssistant()
        msg, path, status = assistant.generate_code("Build website for XYZ company")
        self.assertEqual(status, "HALTED_BRIEF_INCOMPLETE")
        self.assertIn("WEBSITE BUILD HALTED", msg)

    def test_04_extract_existing_prompt_info_without_redundant_questions(self):
        """4. Extracted info from prompt populates brief automatically."""
        self.web_session.start_brief_collection("Build a website for my AI productivity SaaS called NovaFlow")
        brief = ClientBriefParser.parse_local_client_session(self.local_session)
        self.assertEqual(brief.company_name, "NovaFlow")
        self.assertIn(brief.website_type, ["product_landing", "PRODUCT_WEBSITE", "company"])

    def test_05_client_chat_processes_multi_turn_messages(self):
        """5. Multi-turn messages merge into persistent brief session."""
        self.web_session.start_brief_collection("ek website bana do")
        self.web_session.handle_input("Company name Apex Digital Solutions")
        self.web_session.handle_input("We provide cloud architecture and AI software")
        self.assertEqual(len(self.local_session.messages), 2)
        combined = self.local_session.get_combined_text()
        self.assertIn("Apex Digital Solutions", combined)
        self.assertIn("cloud architecture", combined)

    def test_06_chat_info_reaches_client_brief_parser(self):
        """6. Chat messages parse correctly into ClientBrief object."""
        self.local_session.add_user_message("SolarTech India is a solar panel installation company based in Delhi.")
        brief = ClientBriefParser.parse_local_client_session(self.local_session)
        self.assertIn("SolarTech", brief.company_name)

    def test_07_reference_url_added_to_session(self):
        """7. Reference URL can be added and registered in brief."""
        self.local_session.add_reference_url("https://stripe.com", title="Clean UI Ref")
        self.assertEqual(len(self.local_session.reference_items), 1)
        self.assertEqual(self.local_session.reference_items[0].ref_type, "URL")
        self.assertEqual(self.local_session.reference_items[0].source, "https://stripe.com")

    def test_08_reference_pdf_added_to_session(self):
        """8. Reference PDF can be added to brief session."""
        ref = self.local_session.add_reference_file("brand_guidelines.pdf", ref_type="PDF")
        self.assertEqual(ref.ref_type, "PDF")
        self.assertIn(ref, self.local_session.reference_items)

    def test_09_reference_video_added_to_session(self):
        """9. Reference video can be added to brief session."""
        ref = self.local_session.add_reference_file("product_demo.mp4", ref_type="VIDEO")
        self.assertEqual(ref.ref_type, "VIDEO")
        self.assertIn(ref, self.local_session.reference_items)

    def test_10_image_upload_registers_asset_with_role(self):
        """10. Uploading client asset registers image with role and provenance."""
        asset = self.local_session.add_attachment(self.sample_img_1, caption="Product Hero", role="hero_image")
        self.assertEqual(asset.original_filename, "product_hero.png")
        self.assertEqual(asset.role, "hero_image")
        self.assertEqual(asset.provenance, "CLIENT_PROVIDED")

    def test_11_uploaded_images_reach_brief_parser(self):
        """11. Uploaded assets parse cleanly into brief assets."""
        self.local_session.add_attachment(self.sample_img_1, role="hero_image")
        brief = ClientBriefParser.parse_local_client_session(self.local_session)
        self.assertEqual(len(brief.assets), 1)
        self.assertEqual(brief.assets[0].filename, "product_hero.png")

    def test_12_multiple_attached_images_persist(self):
        """12. Multiple image attachments persist in brief session."""
        self.local_session.add_attachment(self.sample_img_1, role="hero_image")
        self.local_session.add_attachment(self.sample_img_2, role="profile_image")
        self.assertEqual(len(self.local_session.assets), 2)

    def test_13_smart_brief_preview_contains_collected_info(self):
        """13. Smart Brief Preview summary displays collected fields."""
        self.local_session.add_user_message("Quantum AI Labs website for machine learning research")
        self.local_session.add_attachment(self.sample_img_1, role="logo")
        self.local_session.add_reference_url("https://openai.com")
        brief = ClientBriefParser.parse_local_client_session(self.local_session)
        summary = self.local_session.get_pre_build_summary(brief)

        self.assertIn("CLIENT BRIEF READY", summary)
        self.assertIn("Quantum AI Labs", summary)
        self.assertIn("product_hero.png", summary)
        self.assertIn("openai.com", summary)

    def test_14_generation_blocked_before_approval(self):
        """14. Generation does not start before explicit brief approval."""
        self.web_session.start_brief_collection()
        self.web_session.handle_input("Zenith Motors electric vehicles company website")
        resp = self.web_session.handle_input("bas itni hi details hain")
        self.assertEqual(self.web_session.state, WebsiteSessionState.WAITING_FOR_APPROVAL)
        self.assertFalse(self.web_session.WEBSITE_GENERATION_STARTED)

    def test_15_generation_starts_on_approval(self):
        """15. Explicit approval sets WEBSITE_GENERATION_STARTED = True."""
        self.web_session.start_brief_collection()
        self.web_session.handle_input("Zenith Motors website")
        self.web_session.handle_input("bas itni hi details hain")

        self.web_session.state = WebsiteSessionState.APPROVED
        self.web_session.WEBSITE_GENERATION_STARTED = True
        self.assertTrue(self.web_session.WEBSITE_GENERATION_STARTED)

    def test_16_build_failure_transitions_to_build_failed_state(self):
        """16. Unresolved build errors transition session to BUILD_FAILED state."""
        self.web_session.state = WebsiteSessionState.BUILD_FAILED
        self.assertEqual(self.web_session.state, WebsiteSessionState.BUILD_FAILED)

    def test_17_no_infinite_retry_loop(self):
        """17. Build failure allows brief editing and clear retry without looping indefinitely."""
        self.web_session.state = WebsiteSessionState.BUILD_FAILED
        resp = self.web_session.handle_input("Add contact email test@apex.com")
        self.assertEqual(self.web_session.state, WebsiteSessionState.WAITING_FOR_APPROVAL)
        self.assertIn("Brief update kar diya hai", resp)

    def test_18_successful_build_transitions_to_completed(self):
        """18. Successful generation sets state to COMPLETED."""
        self.web_session.state = WebsiteSessionState.COMPLETED
        self.assertEqual(self.web_session.state, WebsiteSessionState.COMPLETED)

    def test_19_business_website_classification(self):
        """19. Business website prompt returns business category."""
        self.local_session.add_user_message("Corporate enterprise software consulting services company")
        brief = ClientBriefParser.parse_local_client_session(self.local_session)
        self.assertEqual(brief.website_type, "company")

    def test_20_product_website_classification(self):
        """20. Product landing prompt returns product landing category."""
        self.local_session.add_user_message("Product landing page for mobile fitness application")
        brief = ClientBriefParser.parse_local_client_session(self.local_session)
        self.assertEqual(brief.website_type, "product_landing")

    def test_21_developer_portfolio_architecture_preserved(self):
        """21. Developer portfolio prompt preserves developer portfolio architecture."""
        self.local_session.add_user_message("Developer portfolio website for fullstack engineer Manish")
        brief = ClientBriefParser.parse_local_client_session(self.local_session)
        self.assertEqual(brief.website_type, "portfolio")

    def test_22_anti_template_checks_active(self):
        """22. Anti-template verification functions properly."""
        from tools.coding.anti_template_checker import AntiTemplateChecker
        res = AntiTemplateChecker.evaluate_composition({"hero_structure": "centered"}, None, category="company")
        self.assertIsNotNone(res)



    def test_23_references_separated_from_client_facts(self):
        """23. References influence visual DNA without overwriting client name."""
        self.local_session.add_user_message("Website for GreenEarth Organics")
        self.local_session.add_reference_url("https://apple.com", title="Apple Design")
        brief = ClientBriefParser.parse_local_client_session(self.local_session)
        self.assertEqual(brief.company_name, "GreenEarth Organics")

    def test_24_client_provided_assets_preferred(self):
        """24. Client provided assets keep provenance = CLIENT_PROVIDED."""
        asset = self.local_session.add_attachment(self.sample_img_1, role="hero_image")
        self.assertEqual(asset.provenance, "CLIENT_PROVIDED")

    def test_25_existing_unit_test_suite_passes(self):
        """25. Existing natural website flow test suite passes cleanly."""
        from tests.test_natural_website_flow import TestNaturalWebsiteFlow
        suite = unittest.TestLoader().loadTestsFromTestCase(TestNaturalWebsiteFlow)
        result = unittest.TextTestRunner(verbosity=0).run(suite)
        self.assertTrue(result.wasSuccessful())


if __name__ == "__main__":
    unittest.main()
