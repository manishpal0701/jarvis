"""
tools/computer/safety_validator.py
Safety Validator and Risk Classifier for JARVIS Phase 5 Computer Control.
Classifies action risk levels (LOW, MEDIUM, HIGH, CRITICAL), enforces confirmation policy,
masks sensitive credential input ([SECRET_INPUT]), and evaluates command execution safety.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from tools.computer.action_model import Action, ActionPlan, ActionType, RiskLevel

logger = logging.getLogger("SafetyValidator")

# Common patterns for secret credentials to mask
SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|secret|token|password|auth[_-]?header|bearer)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{8,})["\']?'),
    re.compile(r'sk-[a-zA-Z0-9]{20,}'),
    re.compile(r'ghp_[a-zA-Z0-9]{36}'),
    re.compile(r'eyJ[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*'),  # JWT
    re.compile(r'(?i)password\s*=\s*[^\s]+'),
]

# Destructive keyword patterns requiring HIGH/CRITICAL risk confirmation
DESTRUCTIVE_KEYWORDS = [
    "delete file", "delete folder", "permanently delete", "remove directory",
    "rmdir", "rm -rf", "del /s", "del /f", "format ", "format c:",
    "uninstall", "registry", "regedit", "taskkill /f /im system",
    "password change", "reset password", "financial", "payment", "buy now",
    "send email", "send message", "publish"
]


class SafetyValidationResult:
    def __init__(
        self,
        is_safe: bool = True,
        risk_level: RiskLevel = RiskLevel.LOW,
        requires_confirmation: bool = False,
        confirmation_message: Optional[str] = None,
        sanitized_parameters: Optional[Dict[str, Any]] = None,
        reason: str = "Safe"
    ):
        self.is_safe = is_safe
        self.risk_level = risk_level
        self.requires_confirmation = requires_confirmation
        self.confirmation_message = confirmation_message
        self.sanitized_parameters = sanitized_parameters or {}
        self.reason = reason


class SafetyValidator:
    def __init__(self):
        pass

    def validate_action(self, action: Action) -> SafetyValidationResult:
        """Validates a single Action and determines risk level and confirmation requirement."""
        risk_level = self.classify_action_risk(action)
        requires_conf = risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

        # Sanitize parameters for sensitive inputs
        sanitized_params = self._sanitize_parameters(action.parameters)

        conf_msg = None
        if requires_conf:
            target_desc = action.target.semantic_label if action.target else action.action_type.value
            conf_msg = f"Boss, ye action ('{target_desc}', Risk: {risk_level.value}) system or data modify kar sakti hai. Kya main proceed karu?"

        return SafetyValidationResult(
            is_safe=True,
            risk_level=risk_level,
            requires_confirmation=requires_conf,
            confirmation_message=conf_msg,
            sanitized_parameters=sanitized_params,
            reason=f"Validated with risk level {risk_level.value}"
        )

    def validate_plan(self, plan: ActionPlan) -> SafetyValidationResult:
        """Validates an ActionPlan and returns overall risk classification and confirmation requirements."""
        max_risk = RiskLevel.LOW
        requires_conf = False
        conf_msgs = []

        for action in plan.actions:
            val_res = self.validate_action(action)
            if self._risk_rank(val_res.risk_level) > self._risk_rank(max_risk):
                max_risk = val_res.risk_level
            if val_res.requires_confirmation:
                requires_conf = True
                if val_res.confirmation_message:
                    conf_msgs.append(val_res.confirmation_message)

        plan.risk_level = max_risk
        plan.requires_confirmation = requires_conf

        summary_msg = "\n".join(conf_msgs) if conf_msgs else None

        return SafetyValidationResult(
            is_safe=True,
            risk_level=max_risk,
            requires_confirmation=requires_conf,
            confirmation_message=summary_msg,
            reason=f"Plan overall risk level: {max_risk.value}"
        )

    def classify_action_risk(self, action: Action) -> RiskLevel:
        """Classifies the RiskLevel of an action based on action type and parameters."""
        a_type = action.action_type
        params = action.parameters or {}
        text = str(params.get("text", "")).lower()
        command = str(params.get("command", "")).lower()

        # Check for CRITICAL actions
        if any(kw in text or kw in command for kw in ["financial", "payment", "buy now", "format ", "regedit"]):
            return RiskLevel.CRITICAL

        # Check for HIGH risk actions
        if any(kw in text or kw in command for kw in DESTRUCTIVE_KEYWORDS):
            return RiskLevel.HIGH

        if a_type in [ActionType.OPEN_APPLICATION, ActionType.FOCUS_WINDOW, ActionType.SWITCH_WINDOW, ActionType.SCROLL, ActionType.MOVE]:
            return RiskLevel.LOW

        if a_type in [ActionType.TYPE, ActionType.KEY_PRESS, ActionType.HOTKEY, ActionType.CLICK, ActionType.DOUBLE_CLICK, ActionType.RIGHT_CLICK]:
            if "delete" in text or "rm " in command or "del " in command:
                return RiskLevel.HIGH
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def mask_sensitive_data(self, text: str) -> str:
        """Masks sensitive credentials, tokens, and passwords as [SECRET_INPUT]."""
        if not text:
            return ""
        filtered = text
        for pattern in SECRET_PATTERNS:
            filtered = pattern.sub("[SECRET_INPUT]", filtered)
        return filtered

    def _sanitize_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizes parameter dict by masking sensitive data strings."""
        sanitized = {}
        for k, v in params.items():
            if isinstance(v, str):
                if any(sec_kw in k.lower() for sec_kw in ["password", "secret", "token", "api_key", "key"]):
                    sanitized[k] = "[SECRET_INPUT]"
                else:
                    sanitized[k] = self.mask_sensitive_data(v)
            else:
                sanitized[k] = v
        return sanitized

    def _risk_rank(self, risk: RiskLevel) -> int:
        ranks = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}
        return ranks.get(risk, 1)
