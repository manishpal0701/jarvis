import os
import shutil
import tempfile
import unittest

from tools.coding.local_client_brief import LocalClientBriefSession, LocalClientAsset
from tools.coding.client_brief_ingestion import ClientBriefParser
from tools.coding.client_asset_pipeline import ClientAssetPipeline
from tools.coding.code_assistant import CodeAssistant

class TestNaturalWebsiteFlow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_hero_path = os.path.join(self.temp_dir, "client_photo.jpg")
        with open(self.sample_hero_path, "w", encoding="utf-8") as f:
            f.write("<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'></svg>")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        LocalClientBriefSession.get_instance().reset_session()

    def test_01_natural_conversation_trigger(self):
        assistant = CodeAssistant()
        msg, path, status = assistant.generate_code("Jarvis, ek website bana do")
        self.assertEqual(status, "CLIENT_BRIEF_CHAT_ACTIVATED")
        self.assertIn("Okay Boss", msg)

    def test_02_multi_message_merging(self):
        session = LocalClientBriefSession.get_instance()
        session.reset_session()
        session.add_user_message("Message 1: Company details")
        session.add_user_message("Message 2: Services & pricing")
        session.add_user_message("Message 3: Contact information")
        self.assertEqual(len(session.messages), 3)
        self.assertIn("Services & pricing", session.get_combined_text())

    def test_03_classify_portfolio(self):
        session = LocalClientBriefSession.get_instance()
        session.reset_session()
        session.add_user_message("Main full stack software developer hoon. Python, React aur Flutter projects build karta hoon.")
        brief = ClientBriefParser.parse_local_client_session(session)
        self.assertEqual(brief.website_type, "portfolio")

    def test_04_classify_business(self):
        session = LocalClientBriefSession.get_instance()
        session.reset_session()
        session.add_user_message("Humari corporate company AI solutions aur software consulting services provide karti hai.")
        brief = ClientBriefParser.parse_local_client_session(session)
        self.assertEqual(brief.website_type, "company")

    def test_05_classify_restaurant(self):
        session = LocalClientBriefSession.get_instance()
        session.reset_session()
        session.add_user_message("Ye hamari organic cafe ki details hain. Cold-pressed juices, espresso coffee, aur fresh bakery menu.")
        brief = ClientBriefParser.parse_local_client_session(session)
        self.assertEqual(brief.website_type, "restaurant")

    def test_06_classify_ecommerce(self):
        session = LocalClientBriefSession.get_instance()
        session.reset_session()
        session.add_user_message("Hum online clothes sell karte hain. Shop items, prices aur shopping cart features chahiye.")
        brief = ClientBriefParser.parse_local_client_session(session)
        self.assertEqual(brief.website_type, "e-commerce")

    def test_07_client_image_provenance_client_provided(self):
        session = LocalClientBriefSession.get_instance()
        session.reset_session()
        att = LocalClientAsset(
            asset_id="att_001",
            original_filename="logo.png",
            mime_type="image/png",
            local_path=self.sample_hero_path,
            provenance="CLIENT_PROVIDED"
        )
        session.add_user_message("Logo photo", attachments=[att])
        brief = ClientBriefParser.parse_local_client_session(session)
        self.assertEqual(brief.assets[0].provenance, "CLIENT_PROVIDED")

    def test_08_explicit_hero_role_assignment(self):
        session = LocalClientBriefSession.get_instance()
        session.reset_session()
        att = LocalClientAsset(
            asset_id="att_002",
            original_filename="cafe.jpg",
            mime_type="image/jpeg",
            local_path=self.sample_hero_path,
            role="unknown",
            caption="Ye image client ne di hai, ise hero section me use karna.",
            provenance="CLIENT_PROVIDED"
        )
        session.add_user_message("Ye image client ne di hai, ise hero section me use karna.", attachments=[att])
        brief = ClientBriefParser.parse_local_client_session(session)
        self.assertEqual(brief.assets[0].role, "hero_image")

    def test_09_no_images_creates_generated_asset_requirements(self):
        session = LocalClientBriefSession.get_instance()
        session.reset_session()
        session.add_user_message("Ye restaurant ki details hain, website bana do.")
        brief = ClientBriefParser.parse_local_client_session(session)
        reqs = getattr(brief, "generated_image_requirements", [])
        self.assertGreaterEqual(len(reqs), 1)

    def test_10_one_client_image_preserves_client_provided_and_adds_generated(self):
        session = LocalClientBriefSession.get_instance()
        session.reset_session()
        att = LocalClientAsset(
            asset_id="att_003",
            original_filename="logo.png",
            mime_type="image/png",
            local_path=self.sample_hero_path,
            role="logo",
            provenance="CLIENT_PROVIDED"
        )
        session.add_user_message("Ye logo image hai", attachments=[att])
        brief = ClientBriefParser.parse_local_client_session(session)
        reqs = getattr(brief, "generated_image_requirements", [])
        self.assertEqual(len(brief.assets), 1)
        self.assertEqual(brief.assets[0].role, "logo")
        self.assertGreaterEqual(len(reqs), 1)

    def test_11_generated_assets_tagged_generated(self):
        session = LocalClientBriefSession.get_instance()
        session.reset_session()
        session.add_user_message("Company details without images")
        brief = ClientBriefParser.parse_local_client_session(session)
        reqs = getattr(brief, "generated_image_requirements", [])
        for req in reqs:
            self.assertEqual(req["provenance"], "GENERATED")

    def test_12_zero_fabricated_contact_info(self):
        session = LocalClientBriefSession.get_instance()
        session.reset_session()
        session.add_user_message("Company brief details with zero phone numbers and zero physical location")
        brief = ClientBriefParser.parse_local_client_session(session)
        self.assertIn("phone", brief.missing_fields)
        self.assertIn("address", brief.missing_fields)

    def test_13_unknown_fields_preserved_as_unknown(self):
        session = LocalClientBriefSession.get_instance()
        session.reset_session()
        session.add_user_message("Cafe website brief without phone")
        brief = ClientBriefParser.parse_local_client_session(session)
        summary = session.get_pre_build_summary(brief)
        self.assertIn("UNKNOWN", summary)

    def test_14_no_hardcoded_kasyap_shivam_data(self):
        session = LocalClientBriefSession.get_instance()
        session.reset_session()
        session.add_user_message("Aura Threads fashion boutique website for luxury apparel")
        brief = ClientBriefParser.parse_local_client_session(session)
        self.assertNotIn("Kasyap", brief.company_name)
        self.assertNotIn("Shivam", brief.company_name)

    def test_15_existing_website_builder_unit_tests_pass(self):
        from tests.test_local_client_brief import TestLocalClientBrief
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLocalClientBrief)
        result = unittest.TextTestRunner(verbosity=0).run(suite)
        self.assertTrue(result.wasSuccessful())

if __name__ == "__main__":
    unittest.main()
