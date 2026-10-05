"""
tests/test_whatsapp_agent.py
Unit Test Suite for JARVIS WhatsApp Automation Subpackage.
Tests provider abstraction, contact resolution, ambiguity handling,
composition, confirmation enforcement, broadcast safety, and phone number masking.
"""

import unittest
from tools.whatsapp.whatsapp_models import WhatsAppContact, WhatsAppMessage, mask_phone_number
from tools.whatsapp.whatsapp_provider import MockWhatsAppProvider, WhatsAppCloudAPIProvider, WhatsAppWebComputerControlProvider
from tools.whatsapp.contact_resolver import ContactResolver
from tools.whatsapp.message_composer import WhatsAppMessageComposer
from tools.whatsapp.whatsapp_service import WhatsAppService
from tools.whatsapp.whatsapp_confirmation import WhatsAppConfirmationManager
from tools.whatsapp.whatsapp_agent import WhatsAppAgent
from agent.task_model import TaskModel, StepModel, TaskType

class TestWhatsAppAgent(unittest.TestCase):

    def setUp(self):
        self.service = WhatsAppService.get_instance()
        self.conf_mgr = WhatsAppConfirmationManager.get_instance()
        self.conf_mgr.clear()
        self.resolver = ContactResolver.get_instance()
        self.service.active_contact = None
        self.service.active_body = None

    def tearDown(self):
        self.conf_mgr.clear()

    def test_01_phone_number_masking(self):
        raw_phone = "+919876543210"
        masked = mask_phone_number(raw_phone)
        self.assertNotIn("987654", masked)
        self.assertEqual(masked, "+91******3210")

    def test_02_contact_resolution_single(self):
        res = self.resolver.resolve_contact("Mom")
        self.assertTrue(res.success)
        self.assertFalse(res.is_ambiguous)
        self.assertEqual(res.contact.display_name, "Mom")

    def test_03_contact_resolution_ambiguity(self):
        res = self.resolver.resolve_contact("Rahul")
        self.assertFalse(res.success)
        self.assertTrue(res.is_ambiguous)
        self.assertGreaterEqual(len(res.matching_contacts), 2)
        self.assertIn("2 contacts mile hain", res.message)

    def test_04_message_composition(self):
        msg_body = WhatsAppMessageComposer.compose_from_nl("Rahul ko bol main 10 minute late aaunga")
        self.assertEqual(msg_body, "Main 10 minute late aaunga")

    def test_05_send_requires_confirmation(self):
        prompt = self.service.process_whatsapp_request("Mom ko bol main ghar aa raha hoon", request_id="req_wa_05")
        self.assertIn("Boss", prompt)
        self.assertIn("Mom", prompt)
        self.assertTrue(self.conf_mgr.has_pending_confirmation())

    def test_06_send_rejection_flow(self):
        self.service.process_whatsapp_request("Mom ko bol main ghar aa raha hoon", request_id="req_wa_06")
        self.assertTrue(self.conf_mgr.has_pending_confirmation())

        resp = self.service.execute_confirmed_action("Nahi")
        self.assertIn("cancel kar diya", resp)
        self.assertFalse(self.conf_mgr.has_pending_confirmation())

    def test_07_send_approval_flow(self):
        self.service.process_whatsapp_request("Mom ko bol main ghar aa raha hoon", request_id="req_wa_07")
        self.assertTrue(self.conf_mgr.has_pending_confirmation())

        resp = self.service.execute_confirmed_action("Haan")
        self.assertIn("sent to Mom", resp)
        self.assertFalse(self.conf_mgr.has_pending_confirmation())

    def test_08_multi_recipient_broadcast_safety(self):
        c1 = WhatsAppContact(contact_id="c1", display_name="User 1", phone_number_masked="+91******1111")
        c2 = WhatsAppContact(contact_id="c2", display_name="User 2", phone_number_masked="+91******2222")
        prompt, pending = self.conf_mgr.register_pending_message("req_bc", [c1, c2], "Meeting postponed")
        self.assertIn("2 contacts ko send hoga", prompt)
        self.assertTrue(pending.is_broadcast)

    def test_09_whatsapp_agent_task_handler(self):
        agent = WhatsAppAgent.get_instance()
        task = TaskModel(
            task_id="t_wa_01",
            request_id="req_wa_01",
            user_request="Mom ko WhatsApp karo bol main free hoon",
            normalized_goal="Mom ko WhatsApp karo bol main free hoon",
            task_type=TaskType.WHATSAPP
        )
        step = StepModel(
            step_id="t_wa_01_s1",
            task_id="t_wa_01",
            name="WhatsApp Action",
            description="Process WhatsApp message",
            agent_id="whatsapp_agent"
        )
        result = agent.handle_task(task, step)
        self.assertTrue(result.success)
        self.assertIn("Mom", str(result.result))

if __name__ == "__main__":
    unittest.main()
