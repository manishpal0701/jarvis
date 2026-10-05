import os
import shutil
import tempfile
import unittest
from tools.coding.whatsapp_adapter import WhatsAppAdapter, WhatsAppMessage, WhatsAppMedia
from tools.coding.client_brief_ingestion import ClientBriefParser, ClientBriefManager, ClientBrief, WebsiteAsset
from tools.coding.client_asset_pipeline import ClientAssetPipeline
from tools.coding.code_assistant import CodeAssistant

class TestWhatsAppBriefIngestion(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_profile = os.path.join(self.temp_dir, "profile.jpg")
        self.sample_logo = os.path.join(self.temp_dir, "logo.png")
        self.sample_project = os.path.join(self.temp_dir, "project-01.png")

        # Create dummy image files
        for p in [self.sample_profile, self.sample_logo, self.sample_project]:
            with open(p, "w", encoding="utf-8") as f:
                f.write("<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'></svg>")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_whatsapp_multi_message_ingestion(self):
        """
        Test 1: Ingests 10+ WhatsApp messages and media attachments for client 'Shivam',
        verifying parsed profile fields, asset role assignments, and exact quote extraction.
        """
        messages = [
            WhatsAppMessage("m1", "+919876543210", "Shivam", "12:00", "bhai portfolio banana hai"),
            WhatsAppMessage("m2", "+919876543210", "Shivam", "12:01", "mera naam Shivam Sharma hai"),
            WhatsAppMessage("m3", "+919876543210", "Shivam", "12:02", "main Flutter & Full Stack developer hu"),
            WhatsAppMessage("m4", "+919876543210", "Shivam", "12:03", "skills: React, Flutter, Node, Python, TypeScript, Dart, OpenCV, Firebase"),
            WhatsAppMessage("m5", "+919876543210", "Shivam", "12:04", "project 1: Shivam Fitness App\nproject 2: AI Video Editing Agent"),
            WhatsAppMessage("m6", "+919876543210", "Shivam", "12:05", "Ye meri quote hai: 'I built my first AI assistant while learning Python.'"),
            WhatsAppMessage(
                "m7", "+919876543210", "Shivam", "12:06", "Ye meri profile photo hai",
                media=[WhatsAppMedia("med1", "profile.jpg", "image/jpeg", self.sample_profile, caption="profile photo")]
            ),
            WhatsAppMessage(
                "m8", "+919876543210", "Shivam", "12:07", "Ye mera brand logo hai",
                media=[WhatsAppMedia("med2", "logo.png", "image/png", self.sample_logo, caption="brand logo")]
            ),
            WhatsAppMessage(
                "m9", "+919876543210", "Shivam", "12:08", "Ye Shivam project ka screenshot hai",
                media=[WhatsAppMedia("med3", "project-01.png", "image/png", self.sample_project, caption="project screenshot")]
            )
        ]

        WhatsAppAdapter.get_instance().register_client_feed("Shivam", messages)
        fetched_msgs = WhatsAppAdapter.get_instance().fetch_messages("Shivam")
        self.assertEqual(len(fetched_msgs), 9)

        brief = ClientBriefParser.parse_whatsapp_messages("Shivam", fetched_msgs)
        ClientBriefManager.get_instance().register_brief(brief)

        self.assertEqual(brief.person_name, "Shivam Sharma")
        self.assertTrue("Flutter" in brief.role or "Full Stack" in brief.role)
        self.assertEqual(len(brief.assets), 3)

        # Asset role assertions
        roles = {a.role for a in brief.assets}
        self.assertIn("profile_image", roles)
        self.assertIn("logo", roles)
        self.assertIn("project_image", roles)

        # Quote assertion
        self.assertIn("I built my first AI assistant while learning Python", brief.unique_quote)

    def test_negative_unknown_company_halt(self):
        """
        Test 2: Critical Negative Test.
        Attempts website generation for unknown company 'XYZ Quantum Labs' with no public facts.
        Must return CONTENT_RESEARCH_REQUIRED = TRUE and block website generation.
        """
        assistant = CodeAssistant()
        msg, path, status = assistant.generate_code("Create a website for XYZ Quantum Labs")

        self.assertEqual(status, "HALTED_RESEARCH_REQUIRED")
        self.assertIn("CONTENT RESEARCH REQUIRED", msg)
        self.assertIn("XYZ Quantum Labs", msg)

    def test_asset_pipeline_copy_and_bind(self):
        """
        Test 3: Asset Priority Pipeline Test.
        Verifies copying client media into <project_dir>/public/assets/client/
        and generating valid relative web URLs (/assets/client/...).
        """
        assets = [
            WebsiteAsset("a1", "profile.jpg", "image/jpeg", self.sample_profile, role="profile_image"),
            WebsiteAsset("a2", "logo.png", "image/png", self.sample_logo, role="logo")
        ]
        brief = ClientBrief(client_name="Shivam", assets=assets)

        proj_dir = os.path.join(self.temp_dir, "shivam_site")
        os.makedirs(proj_dir, exist_ok=True)

        bindings = ClientAssetPipeline.process_and_copy_assets(brief, proj_dir)

        dest_profile = os.path.join(proj_dir, "public", "assets", "client", "profile.jpg")
        dest_logo = os.path.join(proj_dir, "public", "assets", "client", "logo.png")

        self.assertTrue(os.path.exists(dest_profile))
        self.assertTrue(os.path.exists(dest_logo))
        self.assertIn("/assets/client/profile.jpg", bindings["profile_image"])
        self.assertIn("/assets/client/logo.png", bindings["logo"])

if __name__ == "__main__":
    unittest.main()
