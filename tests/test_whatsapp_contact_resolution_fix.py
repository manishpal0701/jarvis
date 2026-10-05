"""
tests/test_whatsapp_contact_resolution_fix.py
Comprehensive unit test suite for JARVIS WhatsApp Contact Resolution, Provider Status Mapping,
and Natural Language Message Parsing fixes.
"""

import unittest
from tools.whatsapp.whatsapp_models import WhatsAppContact, WhatsAppMessage, WhatsAppStatus, ContactResolutionStatus, mask_phone_number
from tools.whatsapp.contact_resolver import ContactResolver, ContactResolutionResult, normalize_contact_name
from tools.whatsapp.message_composer import WhatsAppMessageComposer
from tools.whatsapp.whatsapp_service import WhatsAppService
from tools.whatsapp.whatsapp_agent import WhatsAppAgent
from tools.whatsapp.whatsapp_provider import MockWhatsAppProvider, WhatsAppProvider
from tools.whatsapp.whatsapp_confirmation import WhatsAppConfirmationManager
from agent.task_model import TaskModel, StepModel, TaskType
from agent.agent_result import AgentResultStatus


class UnavailableWhatsAppProvider(WhatsAppProvider):
    def is_available(self) -> bool:
        return False

    def send_message(self, contact, body):
        return False, "Provider unavailable", None

    def send_broadcast(self, contacts, body):
        return False, "Provider unavailable", []


class TestWhatsAppContactResolutionFix(unittest.TestCase):
    def setUp(self):
        WhatsAppConfirmationManager.get_instance().clear()
        self.service = WhatsAppService.get_instance()
        self.service.set_provider(MockWhatsAppProvider())
        self.service.active_contact = None
        self.service.active_body = None

    def tearDown(self):
        WhatsAppConfirmationManager.get_instance().clear()

    # ─── CONTACT NORMALIZATION TESTS (1–6) ──────────────────────────────────
    def test_01_normalization_rishabh(self):
        orig, norm = normalize_contact_name("Rishabh")
        self.assertEqual(norm, "rishabh")

    def test_02_normalization_rishabh_sir(self):
        orig, norm = normalize_contact_name("Rishabh sir")
        self.assertEqual(norm, "rishabh")

    def test_03_normalization_rishabh_ji(self):
        orig, norm = normalize_contact_name("Rishabh ji")
        self.assertEqual(norm, "rishabh")

    def test_04_normalization_rishabh_bhai(self):
        orig, norm = normalize_contact_name("Rishabh bhai")
        self.assertEqual(norm, "rishabh")

    def test_05_normalization_vanshu_ko(self):
        orig, norm = normalize_contact_name("Vanshu ko")
        self.assertEqual(norm, "vanshu")

    def test_06_normalization_mittar_ko(self):
        orig, norm = normalize_contact_name("Mittar ko")
        self.assertEqual(norm, "mittar")

    # ─── MESSAGE EXTRACTION TESTS (7–11) ───────────────────────────────────
    def test_07_extraction_hello_bhejo(self):
        rec, body = WhatsAppMessageComposer.parse_nl_request("Rishabh ko hello bhejo")
        self.assertEqual(rec.lower(), "rishabh")
        self.assertEqual(body, "Hello")

    def test_08_extraction_hello_message_karo(self):
        rec, body = WhatsAppMessageComposer.parse_nl_request("Rishabh ko hello message karo")
        self.assertEqual(rec.lower(), "rishabh")
        self.assertEqual(body, "Hello")

    def test_09_extraction_compound_rishabh_sir(self):
        rec, body = WhatsAppMessageComposer.parse_nl_request(
            "jarvis whatsapp pe Rishabh sir ko hello what are you doing message kar do"
        )
        self.assertEqual(rec.lower(), "rishabh sir")
        self.assertEqual(body, "Hello what are you doing")

    def test_10_extraction_ki_clause_vanshu(self):
        rec, body = WhatsAppMessageComposer.parse_nl_request(
            "vanshu ko whatsapp pe message karo ki game me aa"
        )
        self.assertEqual(rec.lower(), "vanshu")
        self.assertEqual(body, "Game me aa")

    def test_11_extraction_post_verb_mittar(self):
        rec, body = WhatsAppMessageComposer.parse_nl_request(
            "Mittar ko whatsapp pe message karo bhsdk"
        )
        self.assertEqual(rec.lower(), "mittar")
        self.assertEqual(body, "Bhsdk")

    # ─── STATUS MAPPING TESTS (12–17) ──────────────────────────────────────
    def test_12_status_contact_not_found(self):
        resolver = ContactResolver.get_instance()
        res = resolver.resolve_contact("NonexistentPerson999", computer_control_fallback=False)
        self.assertEqual(res.status, ContactResolutionStatus.CONTACT_NOT_FOUND)
        self.assertIn("naam ka WhatsApp contact nahi mila", res.message)

        # Verify WhatsAppAgent maps CONTACT_NOT_FOUND to FAILURE, NOT PROVIDER_UNAVAILABLE
        agent = WhatsAppAgent.get_instance()
        task = TaskModel(
            task_id="t_nf_1",
            request_id="r_nf_1",
            user_request="NonexistentPerson999 ko message karo ki hi",
            normalized_goal="NonexistentPerson999 ko message karo ki hi",
            task_type=TaskType.WHATSAPP
        )
        step = StepModel(step_id="t_nf_1_s1", task_id="t_nf_1", name="Action", description="Action step", agent_id="whatsapp_agent")
        result = agent.handle_task(task, step)
        self.assertEqual(result.status, AgentResultStatus.FAILURE)
        self.assertNotEqual(result.status, AgentResultStatus.PROVIDER_UNAVAILABLE)
        self.assertIn("naam ka WhatsApp contact nahi mila", result.result)

    def test_13_status_provider_unavailable(self):
        self.service.set_provider(UnavailableWhatsAppProvider())
        res_str = self.service.process_whatsapp_request("Rishabh ko hello bhejo")
        self.assertIn("WhatsApp contact service abhi available nahi hai", res_str)

        agent = WhatsAppAgent.get_instance()
        task = TaskModel(
            task_id="t_pu_1",
            request_id="r_pu_1",
            user_request="Rishabh ko hello bhejo",
            normalized_goal="Rishabh ko hello bhejo",
            task_type=TaskType.WHATSAPP
        )
        step = StepModel(step_id="t_pu_1_s1", task_id="t_pu_1", name="Action", description="Action step", agent_id="whatsapp_agent")
        result = agent.handle_task(task, step)
        self.assertEqual(result.status, AgentResultStatus.PROVIDER_UNAVAILABLE)

    def test_14_status_auth_required(self):
        res = ContactResolutionResult(
            status=ContactResolutionStatus.AUTH_REQUIRED,
            query="test",
            message="Boss, WhatsApp authentication required hai."
        )
        self.assertEqual(res.status, ContactResolutionStatus.AUTH_REQUIRED)
        self.assertEqual(res.error_code, "AUTH_REQUIRED")

    def test_15_status_ambiguous(self):
        resolver = ContactResolver.get_instance()
        res = resolver.resolve_contact("Rahul", computer_control_fallback=False)
        self.assertEqual(res.status, ContactResolutionStatus.AMBIGUOUS)
        self.assertTrue(res.is_ambiguous)
        self.assertGreaterEqual(len(res.matching_contacts), 2)

    def test_16_status_failed(self):
        res = ContactResolutionResult(
            status=ContactResolutionStatus.FAILED,
            query="test",
            message="Boss, WhatsApp contact resolution mein error aa gaya."
        )
        self.assertEqual(res.status, ContactResolutionStatus.FAILED)
        self.assertFalse(res.success)

    def test_17_status_success(self):
        resolver = ContactResolver.get_instance()
        res = resolver.resolve_contact("Rishabh", computer_control_fallback=False)
        self.assertEqual(res.status, ContactResolutionStatus.SUCCESS)
        self.assertTrue(res.success)
        self.assertEqual(res.resolved_name, "Rishabh")

    # ─── EXECUTION INTEGRITY TESTS (18–20) ──────────────────────────────────
    def test_18_no_false_success_on_initial_handling(self):
        agent = WhatsAppAgent.get_instance()
        task = TaskModel(
            task_id="t_fs_1",
            request_id="r_fs_1",
            user_request="Rishabh sir ko hello what are you doing message kar do",
            normalized_goal="Rishabh sir ko hello what are you doing message kar do",
            task_type=TaskType.WHATSAPP
        )
        step = StepModel(step_id="t_fs_1_s1", task_id="t_fs_1", name="Action", description="Action step", agent_id="whatsapp_agent")
        result = agent.handle_task(task, step)
        self.assertFalse(result.success)
        self.assertEqual(result.status, AgentResultStatus.WAITING_FOR_CONFIRMATION)

    def test_19_confirmation_required_before_send(self):
        agent = WhatsAppAgent.get_instance()
        task = TaskModel(
            task_id="t_cr_1",
            request_id="r_cr_1",
            user_request="Rishabh ko hello bhejo",
            normalized_goal="Rishabh ko hello bhejo",
            task_type=TaskType.WHATSAPP
        )
        step = StepModel(step_id="t_cr_1_s1", task_id="t_cr_1", name="Action", description="Action step", agent_id="whatsapp_agent")
        res1 = agent.handle_task(task, step)
        self.assertEqual(res1.status, AgentResultStatus.WAITING_FOR_CONFIRMATION)
        self.assertTrue(self.service.conf_mgr.has_pending_confirmation())

    def test_20_successful_send_requires_action_verification(self):
        agent = WhatsAppAgent.get_instance()
        # Stage 1: Register confirmation
        task1 = TaskModel(
            task_id="t_sv_1",
            request_id="r_sv_1",
            user_request="Rishabh ko hello bhejo",
            normalized_goal="Rishabh ko hello bhejo",
            task_type=TaskType.WHATSAPP
        )
        step1 = StepModel(step_id="t_sv_1_s1", task_id="t_sv_1", name="Action", description="Action step", agent_id="whatsapp_agent")
        agent.handle_task(task1, step1)

        # Stage 2: Confirm action with allow_mock metadata
        task2 = TaskModel(
            task_id="t_sv_1",
            request_id="r_sv_1",
            user_request="Haan send karo",
            normalized_goal="Haan send karo",
            task_type=TaskType.WHATSAPP,
            metadata={"allow_mock": True}
        )
        step2 = StepModel(step_id="t_sv_1_s2", task_id="t_sv_1", name="Confirm", description="Confirm step", agent_id="whatsapp_agent")
        res2 = agent.handle_task(task2, step2)

        self.assertTrue(res2.success)
        self.assertEqual(res2.status, AgentResultStatus.SUCCESS)
        self.assertIn("Message sent to Rishabh", res2.result)


if __name__ == "__main__":
    unittest.main()
