"""
tests/test_email_agent.py
Unit Test Suite for JARVIS Email Agent Subpackage.
Tests auth status, query translation, parsing, draft/send separation,
high-risk confirmation enforcement, approval/rejection, and secret redaction.
"""

import unittest
from tools.email.email_models import EmailMessage, EmailDraft, EmailSearchResult, mask_email_secrets
from tools.email.gmail_auth import GmailAuthManager
from tools.email.gmail_client import GmailClient
from tools.email.email_search import EmailSearchQueryTranslator
from tools.email.email_parser import EmailParser
from tools.email.email_formatter import EmailFormatter
from tools.email.email_service import EmailService
from tools.email.email_confirmation import EmailConfirmationManager
from tools.email.email_agent import EmailAgent
from agent.task_model import TaskModel, StepModel, TaskType

class TestEmailAgent(unittest.TestCase):

    def setUp(self):
        self.service = EmailService.get_instance()
        self.conf_mgr = EmailConfirmationManager.get_instance()
        self.conf_mgr.clear()
        self.service.active_message = None
        self.service.active_draft = None

    def tearDown(self):
        self.conf_mgr.clear()

    def test_01_auth_status(self):
        auth = GmailAuthManager.get_instance()
        auth.set_mock_authenticated("testuser@gmail.com")
        self.assertTrue(auth.is_authenticated())
        self.assertEqual(auth.get_account_email(), "testuser@gmail.com")

    def test_02_nl_query_translation(self):
        q1, limit1 = EmailSearchQueryTranslator.translate_nl_request("mere unread emails batao")
        self.assertIn("is:unread", q1)
        self.assertEqual(limit1, 5)

        q2, limit2 = EmailSearchQueryTranslator.translate_nl_request("Rahul ka last email dikhao")
        self.assertIn("from:rahul", q2)

        q3, limit3 = EmailSearchQueryTranslator.translate_nl_request("last 10 emails dikhao")
        self.assertEqual(limit3, 10)

    def test_03_bounded_body_extraction(self):
        payload = {
            "id": "test_msg_99",
            "snippet": "Test snippet",
            "labelIds": ["UNREAD"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "Sender <sender@example.com>"},
                    {"name": "Subject", "value": "Test Subject"}
                ],
                "body": {"data": "V2VsY29tZSB0byBKQVJWSVMgRW1haWwgQWdlbnQh"} # "Welcome to JARVIS Email Agent!"
            }
        }
        parsed = EmailParser.parse_raw_message(payload)
        self.assertEqual(parsed.message_id, "test_msg_99")
        self.assertIn("Welcome to JARVIS Email Agent!", parsed.body)

    def test_04_draft_creation_vs_send_separation(self):
        res = self.service.create_draft_reply(recipient="rahul@example.com", body="Draft reply content")
        self.assertIn("draft tayyar kar diya", res)
        self.assertIn("Email send nahi hua hai", res)
        self.assertIsNotNone(self.service.active_draft)
        self.assertEqual(self.service.active_draft.recipient, "rahul@example.com")

    def test_05_send_requires_confirmation(self):
        prompt = self.service.prepare_send(recipient="rahul@example.com", subject="Test", body="Hello", request_id="req_t5")
        self.assertIn("Boss", prompt)
        self.assertIn("rahul@example.com", prompt)
        self.assertTrue(self.conf_mgr.has_pending_confirmation())

    def test_06_send_rejection_flow(self):
        self.service.prepare_send(recipient="rahul@example.com", subject="Test", body="Hello", request_id="req_t6")
        self.assertTrue(self.conf_mgr.has_pending_confirmation())

        resp = self.service.execute_confirmed_action("Nahi")
        self.assertIn("cancel kar diya", resp)
        self.assertFalse(self.conf_mgr.has_pending_confirmation())

    def test_07_send_approval_flow(self):
        self.service.prepare_send(recipient="rahul@example.com", subject="Test", body="Hello", request_id="req_t7")
        self.assertTrue(self.conf_mgr.has_pending_confirmation())

        resp = self.service.execute_confirmed_action("Haan")
        self.assertIn("successfully", resp)
        self.assertFalse(self.conf_mgr.has_pending_confirmation())

    def test_08_secret_redaction(self):
        secret_text = "API Key: api_key=sk-1234567890abcdef1234567890 token=eyJhbGciOiJIUzI1NiJ9"
        masked = mask_email_secrets(secret_text)
        self.assertNotIn("sk-1234567890abcdef1234567890", masked)
        self.assertIn("[SECRET_INPUT]", masked)

    def test_09_email_agent_task_handler(self):
        agent = EmailAgent.get_instance()
        task = TaskModel(
            task_id="t_email_01",
            request_id="req_email_01",
            user_request="unread emails batao",
            normalized_goal="unread emails batao",
            task_type=TaskType.EMAIL
        )
        step = StepModel(
            step_id="t_email_01_s1",
            task_id="t_email_01",
            name="Email Action",
            description="Search unread emails",
            agent_id="email_agent"
        )
        result = agent.handle_task(task, step)
        self.assertTrue(result.success)
        self.assertIn("Boss", str(result.result))

if __name__ == "__main__":
    unittest.main()
