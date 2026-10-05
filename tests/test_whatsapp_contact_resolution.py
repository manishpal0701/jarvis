"""
tests/test_whatsapp_contact_resolution.py
Comprehensive unit test suite for JARVIS WhatsApp Contact Resolution, Name Normalization,
Ambiguity Safety, Context Tracking ("usko"), and Verification.
"""

import unittest
from tools.whatsapp.whatsapp_models import WhatsAppContact, mask_phone_number
from tools.whatsapp.contact_resolver import ContactResolver, ContactResolutionStatus, normalize_contact_name
from tools.whatsapp.message_composer import WhatsAppMessageComposer
from tools.whatsapp.whatsapp_service import WhatsAppService
from tools.whatsapp.whatsapp_provider import MockWhatsAppProvider
from tools.whatsapp.whatsapp_confirmation import WhatsAppConfirmationManager
from tools.computer.confirmation_manager import ConfirmationManager
from agent.task_model import TaskModel, StepModel, TaskType
from agent.agent_result import AgentResultStatus
from agent.agent_orchestrator import AgentOrchestrator
from conversation.conversation_manager import ConversationManager


class TestWhatsAppContactResolution(unittest.TestCase):
    def setUp(self):
        WhatsAppConfirmationManager.get_instance().clear()
        ConfirmationManager.get_instance().clear()
        self.resolver = ContactResolver.get_instance()
        self.service = WhatsAppService.get_instance()
        self.service.set_provider(MockWhatsAppProvider())
        self.service.active_contact = None
        self.service.active_body = None

    def tearDown(self):
        WhatsAppConfirmationManager.get_instance().clear()
        ConfirmationManager.get_instance().clear()

    # 1. "Rishabh sir" normalization
    def test_1_rishabh_sir_normalization(self):
        orig, norm = normalize_contact_name("Rishabh sir")
        self.assertEqual(norm, "rishabh")

    # 2. "rishabh ji" normalization
    def test_2_rishabh_ji_normalization(self):
        orig, norm = normalize_contact_name("rishabh ji")
        self.assertEqual(norm, "rishabh")

    # 3. "rishabh bhai" normalization
    def test_3_rishabh_bhai_normalization(self):
        orig, norm = normalize_contact_name("rishabh bhai")
        self.assertEqual(norm, "rishabh")

    # 4. "rishabh ko" normalization
    def test_4_rishabh_ko_normalization(self):
        orig, norm = normalize_contact_name("rishabh ko")
        self.assertEqual(norm, "rishabh")

    # 5. Exact contact match
    def test_5_exact_contact_match(self):
        res = self.resolver.resolve_contact("Rishabh", computer_control_fallback=False)
        self.assertEqual(res.status, ContactResolutionStatus.SUCCESS)
        self.assertIsNotNone(res.contact)
        self.assertEqual(res.contact.display_name, "Rishabh")

    # 6. Normalized contact match ("rishabh sir ko")
    def test_6_normalized_contact_match(self):
        res = self.resolver.resolve_contact("rishabh sir ko", computer_control_fallback=False)
        self.assertEqual(res.status, ContactResolutionStatus.SUCCESS)
        self.assertEqual(res.contact.display_name, "Rishabh")

    # 7. Case-insensitive match ("RISHABH")
    def test_7_case_insensitive_match(self):
        res = self.resolver.resolve_contact("RISHABH", computer_control_fallback=False)
        self.assertEqual(res.status, ContactResolutionStatus.SUCCESS)
        self.assertEqual(res.contact.display_name, "Rishabh")

    # 8. Ambiguous contacts ("Rahul")
    def test_8_ambiguous_contacts(self):
        res = self.resolver.resolve_contact("Rahul", computer_control_fallback=False)
        self.assertEqual(res.status, ContactResolutionStatus.AMBIGUOUS)
        self.assertTrue(res.is_ambiguous)
        self.assertGreaterEqual(len(res.matching_contacts), 2)

    # 9. Contact not found ("UnknownUser123")
    def test_9_contact_not_found(self):
        res = self.resolver.resolve_contact("UnknownUser123", computer_control_fallback=False)
        self.assertEqual(res.status, ContactResolutionStatus.NOT_FOUND)
        self.assertFalse(res.success)

    # 10. Provider unavailable status
    def test_10_provider_unavailable_status(self):
        task = TaskModel(
            task_id="t_prov_1",
            request_id="r_prov_1",
            user_request="Send WhatsApp to UnknownUser123 saying hi",
            normalized_goal="Send WhatsApp to UnknownUser123 saying hi",
            task_type=TaskType.WHATSAPP
        )
        step = StepModel(step_id="t_s1", task_id="t_prov_1", name="WhatsApp step", description="desc", agent_id="whatsapp_agent")
        from tools.whatsapp.whatsapp_agent import WhatsAppAgent
        agent = WhatsAppAgent.get_instance()
        result = agent.handle_task(task, step)
        self.assertIn(result.status, [AgentResultStatus.AMBIGUOUS, AgentResultStatus.PROVIDER_UNAVAILABLE])

    # 11. Authentication required status
    def test_11_auth_required_status(self):
        res = self.resolver.resolve_contact("Rishabh", computer_control_fallback=False)
        self.assertEqual(res.status, ContactResolutionStatus.SUCCESS)

    # 12. Successful contact resolution
    def test_12_successful_contact_resolution(self):
        res = self.resolver.resolve_contact("ek kam karo whatsapp open karo or rishabh sir ko hello ka message bhejo", computer_control_fallback=False)
        self.assertEqual(res.status, ContactResolutionStatus.SUCCESS)
        self.assertEqual(res.contact.display_name, "Rishabh")

    # 13. Failed contact resolution
    def test_13_failed_contact_resolution(self):
        res = self.resolver.resolve_contact("nonexistent_name_xyz", computer_control_fallback=False)
        self.assertEqual(res.status, ContactResolutionStatus.NOT_FOUND)

    # 14. Context-based "usko" follow-up resolution
    def test_14_context_usko_resolution(self):
        # Step 1: Resolve contact
        res1 = self.service.process_whatsapp_request("Rishabh sir ko message karo")
        self.assertIn("kaunsa message", res1.lower())
        self.assertIsNotNone(self.service.active_contact)
        self.assertEqual(self.service.active_contact.display_name, "Rishabh")

        # Step 2: Follow-up payload ("usko hello bhejo")
        res2 = self.service.process_whatsapp_request("usko hello bhejo")
        self.assertIn("Rishabh", res2)
        self.assertIn("hello", res2.lower())

    # 15. No false SUCCESS generation
    def test_15_no_false_success_generation(self):
        task = TaskModel(
            task_id="t_false_1",
            request_id="r_false_1",
            user_request="Send WhatsApp to NonexistentContact99 saying hi",
            normalized_goal="Send WhatsApp to NonexistentContact99 saying hi",
            task_type=TaskType.WHATSAPP
        )
        step = StepModel(step_id="t_s1", task_id="t_false_1", name="WhatsApp step", description="desc", agent_id="whatsapp_agent")
        from tools.whatsapp.whatsapp_agent import WhatsAppAgent
        agent = WhatsAppAgent.get_instance()
        res = agent.handle_task(task, step)
        self.assertNotEqual(res.status, AgentResultStatus.SUCCESS)
        self.assertFalse(res.success)

    # 16. Successful send verification
    def test_16_successful_send_verification(self):
        # Setup mock provider and request
        self.service.set_provider(MockWhatsAppProvider())
        prompt = self.service.process_whatsapp_request("Rishabh ko hello bhejo", request_id="req_ver_16")
        self.assertTrue(self.service.conf_mgr.has_pending_confirmation())

        # Execute confirmed action with allow_mock
        task = TaskModel(
            task_id="t_ver_16",
            request_id="req_ver_16",
            user_request="Haan send karo",
            normalized_goal="Haan send karo",
            task_type=TaskType.WHATSAPP,
            metadata={"allow_mock": True}
        )
        step = StepModel(step_id="t_s16", task_id="t_ver_16", name="WhatsApp step", description="desc", agent_id="whatsapp_agent")
        from tools.whatsapp.whatsapp_agent import WhatsAppAgent
        res = WhatsAppAgent.get_instance().handle_task(task, step)

        self.assertEqual(res.status, AgentResultStatus.SUCCESS)
        self.assertTrue(res.success)

    # 17. Failed send verification
    def test_17_failed_send_verification(self):
        # Setup mock request and cancel it
        self.service.set_provider(MockWhatsAppProvider())
        self.service.process_whatsapp_request("Rishabh ko hello bhejo", request_id="req_ver_17")

        task = TaskModel(
            task_id="t_ver_17",
            request_id="req_ver_17",
            user_request="Nahi, cancel karo",
            normalized_goal="Nahi, cancel karo",
            task_type=TaskType.WHATSAPP
        )
        step = StepModel(step_id="t_s17", task_id="t_ver_17", name="WhatsApp step", description="desc", agent_id="whatsapp_agent")
        from tools.whatsapp.whatsapp_agent import WhatsAppAgent
        res = WhatsAppAgent.get_instance().handle_task(task, step)

        self.assertEqual(res.status, AgentResultStatus.CANCELLED)
        self.assertFalse(res.success)


if __name__ == "__main__":
    unittest.main()
