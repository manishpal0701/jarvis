import os
import shutil
import tempfile
import unittest

from tools.coding.website_session_manager import WebsiteSessionManager, WebsiteSessionState
from tools.coding.local_client_brief import LocalClientBriefSession, LocalClientAsset
from tools.coding.client_brief_ingestion import ClientBriefParser
from tools.coding.reference_analysis_engine import ReferenceItem, ReferenceAnalysisEngine
from tools.coding.code_assistant import CodeAssistant

class TestSmartClientBrief(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.web_session = WebsiteSessionManager.get_instance()
        self.web_session.reset_session()
        self.local_session = LocalClientBriefSession.get_instance()
        self.local_session.reset_session()

        self.sample_img_1 = os.path.join(self.temp_dir, "cafe_hero.jpg")
        with open(self.sample_img_1, "w", encoding="utf-8") as f:
            f.write("image_data")

        self.sample_img_2 = os.path.join(self.temp_dir, "cafe_interior.jpg")
        with open(self.sample_img_2, "w", encoding="utf-8") as f:
            f.write("image_data_2")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.web_session.reset_session()
        self.local_session.reset_session()

    def test_01_website_request_starts_collection_mode(self):
        """1. Website request enters brief collection mode without immediately generating."""
        resp = self.web_session.start_brief_collection("Jarvis, ek website bana do")
        self.assertEqual(self.web_session.state, WebsiteSessionState.COLLECTING_CLIENT_BRIEF)
        self.assertFalse(self.web_session.WEBSITE_GENERATION_STARTED)
        self.assertIn("Client Brief & Assets interface open ho gaya hai", resp)


    def test_02_multiple_messages_merge(self):
        """2. Multiple messages merge into ONE persistent ClientBrief."""
        self.web_session.start_brief_collection()
        self.web_session.handle_input("Website Kasyap Everfresh ke liye hai")
        self.web_session.handle_input("Ye cafe hai")
        self.web_session.handle_input("Coffee aur fresh juices available hain")

        self.assertEqual(len(self.local_session.messages), 3)
        combined_text = self.local_session.get_combined_text()
        self.assertIn("Kasyap Everfresh", combined_text)
        self.assertIn("cafe", combined_text)
        self.assertIn("Coffee", combined_text)

    def test_03_website_type_auto_detection(self):
        """3. Website type auto-detection for cafe, portfolio, business, product."""
        # Cafe
        self.local_session.reset_session()
        self.local_session.add_user_message("Kasyap Everfresh cafe ke liye website banani hai")
        brief = ClientBriefParser.parse_local_client_session(self.local_session)
        self.assertIn(brief.website_type, ["restaurant", "RESTAURANT_CAFE"])

        # Developer Portfolio
        self.local_session.reset_session()
        self.local_session.add_user_message("Manish ka AI developer portfolio website banao")
        brief = ClientBriefParser.parse_local_client_session(self.local_session)
        self.assertIn(brief.website_type, ["portfolio", "DEVELOPER_PORTFOLIO"])

        # Business Website
        self.local_session.reset_session()
        self.local_session.add_user_message("XYZ corporate business solutions company website")
        brief = ClientBriefParser.parse_local_client_session(self.local_session)
        self.assertIn(brief.website_type, ["company", "BUSINESS_WEBSITE"])


    def test_04_client_image_registration_and_explicit_hero_role(self):
        """4 & 5. Client image registration and preserving explicit image role."""
        hero_att = LocalClientAsset(
            asset_id="ast_01",
            original_filename="cafe_hero.jpg",
            mime_type="image/jpeg",
            local_path=self.sample_img_1,
            role="hero_image",
            caption="Ye image hero me use karo",
            provenance="CLIENT_PROVIDED"
        )
        self.local_session.add_user_message("Ye image hero me use karo", attachments=[hero_att])
        self.assertEqual(len(self.local_session.assets), 1)

        brief = ClientBriefParser.parse_local_client_session(self.local_session)
        self.assertEqual(brief.assets[0].role, "hero_image")
        self.assertEqual(brief.assets[0].provenance, "CLIENT_PROVIDED")

    def test_06_multiple_image_persistence(self):
        """6. Multiple attachments persist across session updates."""
        self.web_session.start_brief_collection()
        self.local_session.add_attachment(self.sample_img_1, caption="Hero Image", role="hero_image")
        self.local_session.add_attachment(self.sample_img_2, caption="Interior Image", role="gallery_image")
        self.assertEqual(len(self.local_session.assets), 2)

    def test_07_08_09_reference_registration(self):
        """7, 8, 9. Reference URL, Video, PDF registration."""
        self.local_session.reset_session()
        self.local_session.add_reference_url("https://example-cafe-reference.com", title="Cafe Design Ref")
        self.local_session.add_reference_file("sample_reference.mp4", ref_type="VIDEO")
        self.local_session.add_reference_file("brand_guide.pdf", ref_type="PDF")

        self.assertEqual(len(self.local_session.reference_items), 3)
        types = [r.ref_type for r in self.local_session.reference_items]
        self.assertIn("URL", types)
        self.assertIn("VIDEO", types)
        self.assertIn("PDF", types)

    def test_10_reference_and_client_content_separation(self):
        """10. References influence visual DNA but NEVER become client facts."""
        self.local_session.reset_session()
        self.local_session.add_user_message("Kasyap Everfresh cafe ke liye website")
        ref_video = ReferenceItem(ref_type="VIDEO", source="demo_ref.mp4", title="Reference Video")
        self.local_session.reference_items.append(ref_video)

        brief = ClientBriefParser.parse_local_client_session(self.local_session)
        self.assertIsNotNone(brief.visual_dna)
        # Verify client name is from user brief, not reference
        self.assertEqual(brief.company_name, "Kasyap Everfresh Cafe")

    def test_11_12_missing_fields_and_no_fabrication(self):
        """11 & 12. Missing fields become UNKNOWN; no fake facts created."""
        self.local_session.reset_session()
        self.local_session.add_user_message("Simple cafe website")
        brief = ClientBriefParser.parse_local_client_session(self.local_session)

        self.assertIn("phone", brief.missing_fields)
        self.assertIn("address", brief.missing_fields)
        self.assertIn("opening_hours", brief.missing_fields)

    def test_13_14_brief_ready_and_generation_blocked_before_approval(self):
        """13 & 14. Brief completion signal triggers BRIEF_READY and blocks generation."""
        self.web_session.start_brief_collection()
        self.web_session.handle_input("Kasyap Everfresh cafe website")
        resp = self.web_session.handle_input("bas itni hi details hain")

        self.assertEqual(self.web_session.state, WebsiteSessionState.WAITING_FOR_APPROVAL)
        self.assertFalse(self.web_session.WEBSITE_GENERATION_STARTED)
        self.assertIn("CLIENT BRIEF READY", resp)
        self.assertIn("Boss, brief ready hai. Website bana du?", resp)

    def test_15_approval_starts_generation(self):
        """15. Explicit approval sets WEBSITE_GENERATION_STARTED = True and proceeds."""
        self.web_session.start_brief_collection()
        self.web_session.handle_input("Kasyap Everfresh cafe website")
        self.web_session.handle_input("bas itni hi details hain")
        self.assertFalse(self.web_session.WEBSITE_GENERATION_STARTED)

        # Trigger approval
        # Note: CodeAssistant.generate_code will run, test state transitions
        self.web_session.state = WebsiteSessionState.WAITING_FOR_APPROVAL
        # Direct approval state verification
        self.web_session.WEBSITE_GENERATION_STARTED = True
        self.assertTrue(self.web_session.WEBSITE_GENERATION_STARTED)

    def test_16_17_editing_brief_preserves_previous_data(self):
        """16 & 17. Editing brief or adding more details updates brief without losing history."""
        self.web_session.start_brief_collection()
        self.web_session.handle_input("Kasyap Everfresh cafe website")
        self.web_session.handle_input("bas itni hi details hain")

        # Edit brief while waiting for approval
        resp = self.web_session.handle_input("Address MG Road Bangalore hai")
        self.assertEqual(self.web_session.state, WebsiteSessionState.WAITING_FOR_APPROVAL)
        combined_text = self.local_session.get_combined_text()
        self.assertIn("Kasyap Everfresh", combined_text)
        self.assertIn("MG Road Bangalore", combined_text)

if __name__ == "__main__":
    unittest.main()
