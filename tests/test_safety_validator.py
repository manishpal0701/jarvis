"""
tests/test_safety_validator.py
Unit tests for JARVIS Phase 5 SafetyValidator, Risk Classifier, and Credential Protection.
"""

import unittest
from tools.computer.action_model import Action, ActionPlan, ActionType, RiskLevel
from tools.computer.safety_validator import SafetyValidator


class TestSafetyValidator(unittest.TestCase):

    def setUp(self):
        self.validator = SafetyValidator()

    def test_low_risk_classification(self):
        action = Action(
            action_type=ActionType.OPEN_APPLICATION,
            parameters={"app_name": "Notepad"}
        )
        res = self.validator.validate_action(action)
        self.assertEqual(res.risk_level, RiskLevel.LOW)
        self.assertFalse(res.requires_confirmation)

    def test_medium_risk_classification(self):
        action = Action(
            action_type=ActionType.TYPE,
            parameters={"text": "Hello Boss"}
        )
        res = self.validator.validate_action(action)
        self.assertEqual(res.risk_level, RiskLevel.MEDIUM)
        self.assertFalse(res.requires_confirmation)

    def test_high_risk_destructive_action(self):
        action = Action(
            action_type=ActionType.TYPE,
            parameters={"text": "delete file permanently"}
        )
        res = self.validator.validate_action(action)
        self.assertEqual(res.risk_level, RiskLevel.HIGH)
        self.assertTrue(res.requires_confirmation)
        self.assertIsNotNone(res.confirmation_message)

    def test_critical_risk_action(self):
        action = Action(
            action_type=ActionType.TYPE,
            parameters={"text": "financial payment buy now"}
        )
        res = self.validator.validate_action(action)
        self.assertEqual(res.risk_level, RiskLevel.CRITICAL)
        self.assertTrue(res.requires_confirmation)

    def test_credential_masking(self):
        secret_text = "Here is my key: sk-abcdef1234567890abcdef1234 and password=Secret123!"
        masked = self.validator.mask_sensitive_data(secret_text)
        self.assertNotIn("sk-abcdef1234567890abcdef1234", masked)
        self.assertIn("[SECRET_INPUT]", masked)

    def test_parameter_sanitization(self):
        params = {
            "normal_text": "hello",
            "password": "MySuperSecretPassword",
            "api_key": "sk-1234567890abcdef12345678"
        }
        res = self.validator._sanitize_parameters(params)
        self.assertEqual(res["password"], "[SECRET_INPUT]")
        self.assertIn("[SECRET_INPUT]", res["api_key"])


if __name__ == "__main__":
    unittest.main()
