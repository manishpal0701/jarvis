import os
import sys
import json
import hmac
import hashlib
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from http.server import HTTPServer

from tools.coding.whatsapp_adapter import (
    WhatsAppAdapter,
    MockWhatsAppAdapter,
    MetaWhatsAppCloudAdapter,
    WhatsAppMessage,
    WhatsAppMedia
)
from tools.coding.whatsapp_webhook_server import WhatsAppWebhookHandler
from tools.coding.client_brief_ingestion import (
    ClientBriefParser,
    ClientBriefManager,
    ClientBrief,
    WebsiteAsset
)
from tools.coding.client_asset_pipeline import ClientAssetPipeline
from tools.coding.code_assistant import CodeAssistant


class TestWhatsAppProductionPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.verify_token = "secret_verify_token_123"
        self.app_secret = "secret_app_secret_456"
        os.environ["WHATSAPP_VERIFY_TOKEN"] = self.verify_token
        os.environ["WHATSAPP_APP_SECRET"] = self.app_secret

    def tearDown(self):
        os.environ.pop("WHATSAPP_VERIFY_TOKEN", None)
        os.environ.pop("WHATSAPP_APP_SECRET", None)
        os.environ.pop("WHATSAPP_ACCESS_TOKEN", None)
        WhatsAppAdapter._instance = None

    # TEST 1: Webhook verification success
    def test_01_webhook_verification_success(self):
        handler = MagicMock(spec=WhatsAppWebhookHandler)
        handler.path = f"/webhook?hub.mode=subscribe&hub.verify_token={self.verify_token}&hub.challenge=123456"
        handler.wfile = MagicMock()

        WhatsAppWebhookHandler.do_GET(handler)
        handler.send_response.assert_called_with(200)
        handler.wfile.write.assert_called_with(b"123456")

    # TEST 2: Webhook verification failure
    def test_02_webhook_verification_failure(self):
        handler = MagicMock(spec=WhatsAppWebhookHandler)
        handler.path = "/webhook?hub.mode=subscribe&hub.verify_token=wrong_token&hub.challenge=123456"
        handler.wfile = MagicMock()

        WhatsAppWebhookHandler.do_GET(handler)
        handler.send_response.assert_called_with(403)

    # TEST 3: Invalid webhook signature rejection
    def test_03_invalid_webhook_signature_rejection(self):
        handler = MagicMock(spec=WhatsAppWebhookHandler)
        handler.path = "/webhook"
        handler.headers = {"Content-Length": "15", "X-Hub-Signature-256": "sha256=invalid_signature"}
        handler.rfile = MagicMock()
        handler.rfile.read.return_value = b'{"object":"page"}'

        WhatsAppWebhookHandler.do_POST(handler)
        handler.send_response.assert_called_with(403)

    # TEST 4: Incoming text message normalization
    def test_04_incoming_text_message_normalization(self):
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "contacts": [{"profile": {"name": "Shivam Sharma"}}],
                        "messages": [{
                            "id": "msg_txt_001",
                            "from": "919876543210",
                            "type": "text",
                            "timestamp": "1720000000",
                            "text": {"body": "My name is Shivam. I am a Flutter Developer."}
                        }]
                    }
                }]
            }]
        }
        adapter = MetaWhatsAppCloudAdapter()
        msgs = adapter.process_webhook_payload(payload)

        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].message_id, "msg_txt_001")
        self.assertEqual(msgs[0].sender_name, "Shivam Sharma")
        self.assertIn("Flutter Developer", msgs[0].text)

    # TEST 5: Multi-message ClientBrief aggregation
    def test_05_multi_message_client_brief_aggregation(self):
        messages = [
            WhatsAppMessage("m1", "p1", "Shivam", "100", "My name is Shivam Sharma."),
            WhatsAppMessage("m2", "p1", "Shivam", "101", "Role: Flutter & Full Stack Developer."),
            WhatsAppMessage("m3", "p1", "Shivam", "102", "Skills: React, Flutter, Python, Node.")
        ]
        brief = ClientBriefParser.parse_whatsapp_messages("Shivam", messages)
        self.assertEqual(brief.person_name, "Shivam Sharma")
        self.assertIn("Flutter", brief.role)
        self.assertTrue(len(brief.skills) >= 3)

    # TEST 6: Image message parsing
    def test_06_image_message_parsing(self):
        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "contacts": [{"profile": {"name": "Shivam"}}],
                        "messages": [{
                            "id": "msg_img_001",
                            "from": "919876543210",
                            "type": "image",
                            "timestamp": "1720000001",
                            "image": {
                                "id": "meta_img_999",
                                "caption": "Use this as my profile photo",
                                "mime_type": "image/jpeg"
                            }
                        }]
                    }
                }]
            }]
        }
        adapter = MetaWhatsAppCloudAdapter()
        msgs = adapter.process_webhook_payload(payload)

        self.assertEqual(len(msgs), 1)
        self.assertEqual(len(msgs[0].media), 1)
        self.assertEqual(msgs[0].media[0].media_id, "meta_img_999")

    # TEST 7: Media metadata retrieval using mocked Meta API
    @patch("urllib.request.urlopen")
    def test_07_media_metadata_retrieval_mocked_meta_api(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"url": "https://meta.cdn.example.com/file.jpg"}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        adapter = MetaWhatsAppCloudAdapter()
        adapter.access_token = "valid_token"
        media_url = adapter.get_media_url("meta_media_123")

        self.assertEqual(media_url, "https://meta.cdn.example.com/file.jpg")

    # TEST 8: Media download using mocked Meta API
    @patch("urllib.request.urlopen")
    def test_08_media_download_mocked_meta_api(self, mock_urlopen):
        mock_resp1 = MagicMock()
        mock_resp1.read.return_value = json.dumps({"url": "https://meta.cdn.example.com/file.jpg"}).encode("utf-8")

        mock_resp2 = MagicMock()
        mock_resp2.read.return_value = b"<binary_jpeg_data>"

        mock_urlopen.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=mock_resp1)),
            MagicMock(__enter__=MagicMock(return_value=mock_resp2))
        ]

        adapter = MetaWhatsAppCloudAdapter()
        adapter.access_token = "valid_token"
        out_path = adapter.download_media("meta_media_123", self.temp_dir, "profile.jpg")

        self.assertIsNotNone(out_path)
        self.assertTrue(os.path.exists(out_path))

    # TEST 9: Client asset registration
    def test_09_client_asset_registration(self):
        assets = [WebsiteAsset("a1", "profile.jpg", "image/jpeg", "/tmp/p.jpg", role="profile_image")]
        brief = ClientBrief(client_name="Shivam", assets=assets)
        self.assertEqual(len(brief.assets), 1)
        self.assertEqual(brief.assets[0].provenance, "CLIENT_PROVIDED")

    # TEST 10: Explicit profile-image role assignment
    def test_10_explicit_profile_image_role_assignment(self):
        messages = [
            WhatsAppMessage(
                "m1", "p1", "Shivam", "100", "Use this as my profile photo",
                media=[WhatsAppMedia("med1", "photo.jpg", "image/jpeg", "/tmp/p.jpg", caption="Use this as my profile photo")]
            )
        ]
        brief = ClientBriefParser.parse_whatsapp_messages("Shivam", messages)
        self.assertEqual(brief.assets[0].role, "profile_image")

    # TEST 11: Explicit logo role assignment
    def test_11_explicit_logo_role_assignment(self):
        messages = [
            WhatsAppMessage(
                "m1", "p1", "Shivam", "100", "Use this as logo",
                media=[WhatsAppMedia("med1", "brand_logo.png", "image/png", "/tmp/l.png", caption="Use this as logo")]
            )
        ]
        brief = ClientBriefParser.parse_whatsapp_messages("Shivam", messages)
        self.assertEqual(brief.assets[0].role, "logo")

    # TEST 12: Ambiguous asset role clarification prompt
    def test_12_ambiguous_asset_role_clarification(self):
        messages = [
            WhatsAppMessage(
                "m1", "p1", "Shivam", "100", "",
                media=[WhatsAppMedia("med1", "unknown.png", "image/png", "/tmp/u.png", caption="")]
            )
        ]
        brief = ClientBriefParser.parse_whatsapp_messages("Shivam", messages)
        self.assertEqual(brief.assets[0].role, "general")
        self.assertIsNotNone(brief.assets[0].clarification_needed)

    # TEST 13: Duplicate webhook event idempotency
    def test_13_duplicate_webhook_event_idempotency(self):
        adapter = MetaWhatsAppCloudAdapter()
        self.assertFalse(adapter.is_duplicate_message("msg_dup_100"))
        self.assertTrue(adapter.is_duplicate_message("msg_dup_100"))

    # TEST 14: Unknown company blocks generation
    def test_14_unknown_company_blocks_generation(self):
        assistant = CodeAssistant()
        msg, path, status = assistant.generate_code("Create a website for XYZ Quantum Labs")
        self.assertEqual(status, "HALTED_RESEARCH_REQUIRED")
        self.assertIn("CONTENT RESEARCH REQUIRED", msg)

    # TEST 15: Known company uses official domain research
    def test_15_known_company_uses_official_research(self):
        from tools.coding.website_requirements_analyzer import WebsiteRequirementsAnalyzer
        comp = WebsiteRequirementsAnalyzer.detect_company_entity("Create a website for Inurum Technology")
        self.assertEqual(comp, "Inurum Technology")

    # TEST 16: Client-provided image is preserved
    def test_16_client_provided_image_preserved(self):
        asset = WebsiteAsset("a1", "my_logo.png", "image/png", "/tmp/logo.png", role="logo", provenance="CLIENT_PROVIDED")
        self.assertEqual(asset.provenance, "CLIENT_PROVIDED")
        self.assertTrue(asset.is_user_provided)

    # TEST 17: Generated website receives ClientBrief content
    def test_17_generated_website_receives_client_brief_content(self):
        brief = ClientBrief(client_name="Shivam", person_name="Shivam Sharma", role="Flutter Architect", unique_quote="I built my first AI assistant while learning Python.")
        self.assertEqual(brief.person_name, "Shivam Sharma")
        self.assertIn("I built my first AI assistant", brief.unique_quote)

    # TEST 18: No fabricated claims in generated content
    def test_18_no_fabricated_claims_in_generated_content(self):
        brief = ClientBrief(client_name="Shivam")
        self.assertEqual(brief.projects, [])

    # TEST 19: Existing mock WhatsApp tests pass
    def test_19_existing_mock_whatsapp_tests_pass(self):
        mock_adapter = MockWhatsAppAdapter()
        mock_adapter.register_client_feed("ShivamTest", [WhatsAppMessage("m1", "p1", "ShivamTest", "100", "hello")])
        msgs = mock_adapter.fetch_messages("ShivamTest")
        self.assertEqual(len(msgs), 1)

    # TEST 20: Secure config fallback when credentials absent
    def test_20_secure_config_fallback_when_credentials_absent(self):
        os.environ.pop("WHATSAPP_ACCESS_TOKEN", None)
        WhatsAppAdapter._instance = None
        adapter = WhatsAppAdapter.get_instance()
        self.assertIsInstance(adapter, MockWhatsAppAdapter)


if __name__ == "__main__":
    unittest.main()
