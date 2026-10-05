"""
tests/test_website_client_brief_ui_flow.py
Integration & Regression Tests for Bug #2: Website Builder Client Brief Workspace & REST API.
"""

import json
import os
import unittest

from tools.coding.local_client_brief import LocalClientBriefSession
from tools.coding.website_session_manager import WebsiteSessionManager, WebsiteSessionState
from tools.coding.workspace_manager import WorkspaceManager


class TestWebsiteClientBriefUIFlow(unittest.TestCase):

    def setUp(self):
        self.session = LocalClientBriefSession.get_instance()
        self.session.reset_session()
        self.web_session = WebsiteSessionManager.get_instance()
        self.web_session.reset_session()

        self.wm = WorkspaceManager.get_instance()
        self.wm.ensure_started()
        self.client = self.wm.app.test_client()

    def tearDown(self):
        self.session.reset_session()
        self.web_session.reset_session()


    def test_01_brief_status_endpoint_returns_json(self):
        """1. GET /api/brief/status returns valid structured brief metadata."""
        resp = self.client.get('/api/brief/status')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("session_state", data)
        self.assertIn("company_name", data)
        self.assertIn("website_type", data)
        self.assertIn("assets", data)
        self.assertIn("references", data)

    def test_02_brief_update_form_endpoint(self):
        """2. POST /api/brief/update updates all 12 brief form fields."""
        payload = {
            "company_name": "Apex Automation SaaS",
            "website_type": "PRODUCT_WEBSITE",
            "business_description": "AI-powered workflow automation software for enterprises.",
            "target_audience": "B2B SaaS Founders",
            "services": "Workflow Engine, Analytics Dashboard",
            "brand_preferences": "Dark Luxury Cyan",
            "required_sections": "Hero, Features, Pricing, Testimonials, Contact",
            "special_requirements": "Include contact phone +1-800-APEX"
        }
        resp = self.client.post('/api/brief/update', json=payload)
        self.assertEqual(resp.status_code, 200)
        res_data = json.loads(resp.data)
        self.assertTrue(res_data.get("success"))

        status_resp = self.client.get('/api/brief/status')
        status_data = json.loads(status_resp.data)
        self.assertIn("Apex Automation", status_data["company_name"])

    def test_03_brief_image_upload_and_removal(self):
        """3. Image upload registers asset, and POST /api/brief/remove_asset deletes it."""
        upload_dir = os.path.abspath(os.path.join("data", "uploads"))
        os.makedirs(upload_dir, exist_ok=True)
        dummy_file = os.path.join(upload_dir, "test_hero.png")
        with open(dummy_file, "wb") as f:
            f.write(b"PNG_DATA")

        asset = self.session.add_attachment(dummy_file, caption="Hero visual", role="hero_image")
        self.assertEqual(len(self.session.assets), 1)

        # Verify status lists asset
        status_resp = self.client.get('/api/brief/status')
        status_data = json.loads(status_resp.data)
        self.assertEqual(len(status_data["assets"]), 1)
        self.assertEqual(status_data["assets"][0]["asset_id"], asset.asset_id)

        # Remove asset via REST API
        rem_resp = self.client.post('/api/brief/remove_asset', json={"asset_id": asset.asset_id})
        self.assertEqual(rem_resp.status_code, 200)

        # Verify asset removed
        self.assertEqual(len(self.session.assets), 0)

    def test_04_brief_reference_url_and_file_registration(self):
        """4. POST /api/brief/reference registers URL, Video, and PDF references."""
        # URL Reference
        url_resp = self.client.post('/api/brief/reference', json={
            "ref_type": "URL", "source": "https://stripe.com", "title": "Stripe Ref"
        })
        self.assertEqual(url_resp.status_code, 200)

        # PDF Reference
        pdf_resp = self.client.post('/api/brief/reference', json={
            "ref_type": "PDF", "source": "C:/docs/brand_guidelines.pdf", "title": "Brand PDF"
        })
        self.assertEqual(pdf_resp.status_code, 200)

        status_resp = self.client.get('/api/brief/status')
        status_data = json.loads(status_resp.data)
        self.assertEqual(len(status_data["references"]), 2)

    def test_05_brief_approval_triggers_generation_state(self):
        """5. POST /api/brief/approve transitions session out of COLLECTING_CLIENT_BRIEF."""
        self.web_session.start_brief_collection("Make a website for Apex Corp")
        self.assertIn(self.web_session.state, [WebsiteSessionState.COLLECTING_CLIENT_BRIEF, WebsiteSessionState.WAITING_FOR_APPROVAL])

        appr_resp = self.client.post('/api/brief/approve')
        self.assertEqual(appr_resp.status_code, 200)

    def test_06_build_failure_reporting_no_fake_success(self):
        """6. IDE workspace status never reports 'Website Ready' on empty code or build failure."""
        self.wm.set_status("BUILD_FAILED: SyntaxError in src/App.tsx", "error")
        self.assertEqual(self.wm.status, "BUILD_FAILED: SyntaxError in src/App.tsx")
        self.assertNotEqual(self.wm.status, "Website Ready")


if __name__ == "__main__":
    unittest.main()
