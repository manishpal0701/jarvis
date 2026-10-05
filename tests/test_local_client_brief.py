import os
import shutil
import tempfile
import unittest

from tools.coding.local_client_brief import LocalClientBriefSession, LocalClientAsset, LocalClientChatMessage
from tools.coding.client_brief_ingestion import ClientBriefParser, WebsiteAsset
from tools.coding.client_asset_pipeline import ClientAssetPipeline
from tools.coding.code_assistant import CodeAssistant

class TestLocalClientBrief(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_hero_path = os.path.join(self.temp_dir, "kasyap_cafe_hero.jpg")
        with open(self.sample_hero_path, "w", encoding="utf-8") as f:
            f.write("<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'></svg>")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        LocalClientBriefSession.get_instance().reset_session()

    def test_01_kasyap_everfresh_local_brief_extraction(self):
        """
        Test 1: Ingests 3 local chat messages & hero image attachment for Kasyap Everfresh Cafe.
        Verifies brief extraction, explicit role assignment (hero_image), provenance (CLIENT_PROVIDED),
        and zero external API dependencies.
        """
        session = LocalClientBriefSession.get_instance()
        session.reset_session()

        session.add_user_message("Kasyap Everfresh Cafe ke liye ek website banani hai.")
        session.add_user_message("Website premium aur attractive honi chahiye.")

        hero_att = LocalClientAsset(
            asset_id="att_001",
            original_filename="kasyap_cafe_hero.jpg",
            mime_type="image/jpeg",
            local_path=self.sample_hero_path,
            role="unknown",
            caption="Ye image client ne di hai, ise hero section me use karna.",
            provenance="CLIENT_PROVIDED"
        )
        session.add_user_message("Ye image client ne di hai, ise hero section me use karna.", attachments=[hero_att])

        self.assertTrue(session.is_ready)
        self.assertEqual(len(session.messages), 3)
        self.assertEqual(len(session.assets), 1)

        brief = ClientBriefParser.parse_local_client_session(session)

        self.assertIn("Kasyap Everfresh", brief.company_name)
        self.assertIn("RESTAURANT", brief.website_type.upper())
        self.assertEqual(len(brief.assets), 1)
        self.assertEqual(brief.assets[0].role, "hero_image")
        self.assertEqual(brief.assets[0].provenance, "CLIENT_PROVIDED")
        self.assertEqual(brief.source_metadata["source"], "LOCAL_CLIENT_BRIEF")

    def test_02_asset_pipeline_copy_and_provenance(self):
        """
        Verifies that uploaded client assets copy directly to public/assets/client/
        and bind relative web URLs (/assets/client/...) with CLIENT_PROVIDED provenance.
        """
        session = LocalClientBriefSession.get_instance()
        session.reset_session()

        att = LocalClientAsset(
            asset_id="att_002",
            original_filename="kasyap_cafe_hero.jpg",
            mime_type="image/jpeg",
            local_path=self.sample_hero_path,
            role="hero_image",
            provenance="CLIENT_PROVIDED"
        )
        session.add_user_message("Hero photo", attachments=[att])
        brief = ClientBriefParser.parse_local_client_session(session)

        proj_dir = os.path.join(self.temp_dir, "cafe_workspace")
        os.makedirs(proj_dir, exist_ok=True)

        bindings = ClientAssetPipeline.process_and_copy_assets(brief, proj_dir)
        dest_file = os.path.join(proj_dir, "public", "assets", "client", "kasyap_cafe_hero.jpg")

        self.assertTrue(os.path.exists(dest_file))
        self.assertIn("/assets/client/kasyap_cafe_hero.jpg", bindings["hero_image"])

    def test_03_negative_incomplete_brief_halt(self):
        """
        Test 2: Critical Negative Test.
        Attempts website generation for 'XYZ company' without providing brief details or chat messages.
        Must halt with CLIENT_BRIEF_INCOMPLETE = TRUE and HALTED_BRIEF_INCOMPLETE status.
        """
        session = LocalClientBriefSession.get_instance()
        session.reset_session()

        assistant = CodeAssistant()
        msg, path, status = assistant.generate_code("Create a website for XYZ company")

        self.assertEqual(status, "HALTED_BRIEF_INCOMPLETE")
        self.assertIn("CLIENT BRIEF INCOMPLETE", msg)

if __name__ == "__main__":
    unittest.main()
