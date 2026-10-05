"""
scratch/test_communication_acceptance.py
Mandatory Real-World Acceptance Test Suite for JARVIS Communication Feature Expansion.
Tests Scenarios A through R covering Email Agent, WhatsApp Automation, Context Resolution,
High-Risk Confirmations, Cross-Channel Operations, Stale Confirmation Protection, and Secret Redaction.
"""

import time
import unittest
from tools.email.email_models import EmailMessage, EmailDraft, mask_email_secrets
from tools.email.email_service import EmailService
from tools.email.email_confirmation import EmailConfirmationManager
from tools.whatsapp.whatsapp_models import WhatsAppContact, mask_phone_number
from tools.whatsapp.whatsapp_service import WhatsAppService
from tools.whatsapp.whatsapp_confirmation import WhatsAppConfirmationManager
from tools.whatsapp.contact_resolver import ContactResolver
from conversation.command_router import CommandRouter
from conversation.conversation_manager import ConversationManager

class TestCommunicationAcceptance(unittest.TestCase):

    def setUp(self):
        self.email_service = EmailService.get_instance()
        self.email_conf = EmailConfirmationManager.get_instance()
        self.email_conf.clear()

        self.wa_service = WhatsAppService.get_instance()
        self.wa_conf = WhatsAppConfirmationManager.get_instance()
        self.wa_conf.clear()

        self.conv = ConversationManager.get_instance()
        self.conv.reset_context()

        self.router = CommandRouter()

    # TEST A — EMAIL SEARCH
    def test_scenario_a_email_search(self):
        res = self.email_service.search_and_format("mere unread emails batao")
        self.assertIn("Boss", res)
        self.assertIn("emails", res)

    # TEST B — EMAIL READ
    def test_scenario_b_email_read(self):
        self.email_service.search_and_format("unread emails")
        res = self.email_service.read_email("msg_001")
        self.assertIn("From: Rahul Sharma", res)

    # TEST C — EMAIL SUMMARY
    def test_scenario_c_email_summary(self):
        self.email_service.read_email("msg_001")
        summary = self.email_service.summarize_email()
        self.assertIn("Rahul Sharma ka email", summary)
        self.assertIn("Summary:", summary)

    # TEST D — EMAIL DRAFT
    def test_scenario_d_email_draft(self):
        self.email_service.read_email("msg_001")
        res = self.email_service.create_draft_reply(recipient="rahul@example.com", body="I will review the documents")
        self.assertIn("draft tayyar kar diya", res)
        self.assertIn("Email send nahi hua hai", res)

    # TEST E — EMAIL SEND SAFETY
    def test_scenario_e_email_send_safety(self):
        self.email_service.read_email("msg_001")
        self.email_service.create_draft_reply(recipient="rahul@example.com", body="I will review")
        prompt = self.email_service.prepare_send(request_id="req_acc_e")
        self.assertIn("Boss", prompt)
        self.assertTrue(self.email_conf.has_pending_confirmation())

    # TEST F — EMAIL REJECTION
    def test_scenario_f_email_rejection(self):
        self.email_service.prepare_send(recipient="rahul@example.com", subject="Test", body="Body", request_id="req_acc_f")
        resp = self.email_service.execute_confirmed_action("Nahi")
        self.assertIn("cancel kar diya", resp)
        self.assertFalse(self.email_conf.has_pending_confirmation())

    # TEST G — EMAIL SEND
    def test_scenario_g_email_send(self):
        self.email_service.prepare_send(recipient="rahul@example.com", subject="Test", body="Body", request_id="req_acc_g")
        resp = self.email_service.execute_confirmed_action("Haan")
        self.assertIn("successfully", resp)

    # TEST H — WHATSAPP CONTACT
    def test_scenario_h_whatsapp_contact(self):
        res = ContactResolver.get_instance().resolve_contact("Mom")
        self.assertTrue(res.success)
        self.assertEqual(res.contact.display_name, "Mom")

    # TEST I — WHATSAPP AMBIGUITY
    def test_scenario_i_whatsapp_ambiguity(self):
        res = self.wa_service.process_whatsapp_request("Rahul ko WhatsApp karo")
        self.assertIn("2 contacts mile hain", res)
        self.assertFalse(self.wa_conf.has_pending_confirmation())

    # TEST J — WHATSAPP COMPOSE
    def test_scenario_j_whatsapp_compose(self):
        prompt = self.wa_service.process_whatsapp_request("Mom ko bol main 10 minute late aaunga", request_id="req_acc_j")
        self.assertIn("Mom", prompt)
        self.assertIn("10 minute late aaunga", prompt)

    # TEST K — WHATSAPP SEND SAFETY
    def test_scenario_k_whatsapp_send_safety(self):
        prompt = self.wa_service.process_whatsapp_request("Mom ko bol main ghar aa raha hoon", request_id="req_acc_k")
        self.assertIn("send karu", prompt)
        self.assertTrue(self.wa_conf.has_pending_confirmation())

    # TEST L — WHATSAPP REJECTION
    def test_scenario_l_whatsapp_rejection(self):
        self.wa_service.process_whatsapp_request("Mom ko bol main ghar aa raha hoon", request_id="req_acc_l")
        resp = self.wa_service.execute_confirmed_action("Nahi")
        self.assertIn("cancel kar diya", resp)
        self.assertFalse(self.wa_conf.has_pending_confirmation())

    # TEST M — WHATSAPP SEND
    def test_scenario_m_whatsapp_send(self):
        self.wa_service.process_whatsapp_request("Mom ko bol main ghar aa raha hoon", request_id="req_acc_m")
        resp = self.wa_service.execute_confirmed_action("Haan")
        self.assertIn("sent to Mom", resp)

    # TEST N — CONTEXT FOLLOW-UP
    def test_scenario_n_multi_turn_context(self):
        # Turn 1: Search email from Rahul
        self.email_service.search_and_format("Rahul ka email dikhao")
        self.assertIsNotNone(self.email_service.active_message)

        # Turn 2: Summarize
        summary = self.email_service.summarize_email()
        self.assertIn("Rahul Sharma ka email", summary)

        # Turn 3: Draft reply
        draft_msg = self.email_service.create_draft_reply()
        self.assertIn("draft tayyar kar diya", draft_msg)

    # TEST O — CROSS-CHANNEL SAFETY
    def test_scenario_o_cross_channel_safety(self):
        # User looks at email
        self.email_service.read_email("msg_001")
        # Then asks to send on WhatsApp
        prompt = self.wa_service.process_whatsapp_request("Mom ko WhatsApp kar do", request_id="req_acc_o")
        self.assertIn("Mom", prompt)
        self.assertTrue(self.wa_conf.has_pending_confirmation())

    # TEST P — STALE CONFIRMATION PROTECTION
    def test_scenario_p_stale_confirmation_protection(self):
        prompt, pending = self.email_conf.register_pending_email("req_old", "SEND", "old@example.com", "Old", "Body")
        # Simulate time passage > 120 seconds
        pending.created_at = time.time() - 130.0
        self.assertFalse(self.email_conf.has_pending_confirmation())

    # TEST Q — SECRET REDACTION AND PHONE MASKING
    def test_scenario_q_secret_redaction_and_masking(self):
        secret = "My token is ghp_1234567890abcdef1234567890abcdef1234"
        redacted = mask_email_secrets(secret)
        self.assertNotIn("ghp_1234567890abcdef1234567890abcdef1234", redacted)
        self.assertIn("[SECRET_INPUT]", redacted)

        phone = "+919876543210"
        masked = mask_phone_number(phone)
        self.assertEqual(masked, "+91******3210")

if __name__ == "__main__":
    unittest.main()
