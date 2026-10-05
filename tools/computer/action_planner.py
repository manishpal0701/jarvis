"""
tools/computer/action_planner.py
Intelligent Action Planner for JARVIS Phase 5 Computer Control.
Converts natural language user requests into structured ActionPlans,
resolving Phase 1 conversation context ("isme", "ab", "ye"), Phase 4 visual targets,
and integrating with Phase 2 Agent Orchestrator state machine & bounded recovery.
"""

import re
import time
import logging
from typing import Any, Dict, List, Optional, Tuple

from tools.computer.action_model import Action, ActionPlan, ActionStatus, ActionTarget, ActionType, RiskLevel
from tools.computer.target_resolver import TargetResolver
from tools.computer.safety_validator import SafetyValidator
from conversation.conversation_manager import ConversationManager

logger = logging.getLogger("ActionPlanner")


class ActionPlanner:
    def __init__(
        self,
        target_resolver: Optional[TargetResolver] = None,
        safety_validator: Optional[SafetyValidator] = None
    ):
        self.target_resolver = target_resolver or TargetResolver()
        self.safety_validator = safety_validator or SafetyValidator()
        self.conversation_manager = ConversationManager.get_instance()

    def create_plan_from_request(
        self,
        user_request: str,
        request_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> ActionPlan:
        """
        Translates a natural language request into a structured ActionPlan.
        Resolves Phase 1 contextual pronouns ('isme', 'ab', 'ye') and targets.
        """
        clean_req = re.sub(r"(?i)^(jarvis[,:]?\s*)", "", user_request.strip()).strip()

        # Step 1: Resolve Phase 1 Contextual references ("isme", "ab", "ye")
        resolved_request, active_app = self._resolve_context_references(clean_req)
        user_intent = resolved_request

        # Check for compound actions (e.g., "chrome kholo aur youtube search karo")
        if re.search(r"\s+(?:aur|and|then|phir)\s+", resolved_request.lower()):
            parts = [p.strip() for p in re.split(r"\s+(?:aur|and|then|phir)\s+", resolved_request, flags=re.IGNORECASE) if p.strip()]
            if len(parts) > 1:
                actions: List[Action] = []
                for part in parts:
                    sub_actions = self._build_actions_for_single_request(part, active_app)
                    actions.extend(sub_actions)
                plan = ActionPlan(
                    request_id=request_id or f"req_{time.strftime('%H%M%S')}",
                    task_id=task_id,
                    user_intent=user_intent,
                    actions=actions
                )
                self.safety_validator.validate_plan(plan)
                return plan

        actions = self._build_actions_for_single_request(resolved_request, active_app)
        plan = ActionPlan(
            request_id=request_id or f"req_{time.strftime('%H%M%S')}",
            task_id=task_id,
            user_intent=user_intent,
            actions=actions
        )
        self.safety_validator.validate_plan(plan)
        return plan

    def _build_actions_for_single_request(self, req: str, active_app: Optional[str]) -> List[Action]:
        req_lower = req.lower().strip()
        actions: List[Action] = []

        # ─── Case 1: Application Launch / Focus / Switch ──────────────────────
        is_open_app = (
            any(req_lower.startswith(kw) for kw in ["open ", "launch ", "start ", "khol ", "kholo ", "chalao ", "chala do "])
            or any(kw in req_lower for kw in ["kholo", "khol do", "open karo", "chalao"])
        )
        if is_open_app:
            app_name = re.sub(r"(?i)^(open|launch|start|khol|kholo|chalao|chala do)\s+", "", req).strip()
            app_name = re.sub(r"(?i)\s+(kholo|khol do|open karo|chalao)$", "", app_name).strip()
            # Check for "open X and write Y"
            type_match = re.search(r"(?i)^(.*)\s+and\s+(type|write)\s+(.*)$", app_name)
            if type_match:
                app_target = type_match.group(1).strip()
                text_content = type_match.group(3).strip().strip("'\"")

                act1 = Action(
                    action_type=ActionType.OPEN_APPLICATION,
                    parameters={"app_name": app_target},
                    target=ActionTarget(semantic_label=app_target)
                )
                act2 = Action(
                    action_type=ActionType.TYPE,
                    parameters={"text": text_content, "target_app": app_target, "submit": True},
                    target=ActionTarget(semantic_label=f"text input in {app_target}")
                )
                actions.extend([act1, act2])
            else:
                act = Action(
                    action_type=ActionType.OPEN_APPLICATION,
                    parameters={"app_name": app_name},
                    target=ActionTarget(semantic_label=app_name)
                )
                actions.append(act)

        elif any(kw in req_lower for kw in ["switch to", "switch karo", "focus ", "switch "]):
            app_name = re.sub(r"(?i)^(switch to|switch karo|focus|switch)\s+", "", req).strip()
            act = Action(
                action_type=ActionType.FOCUS_WINDOW,
                parameters={"app_name": app_name},
                target=ActionTarget(semantic_label=app_name)
            )
            actions.append(act)

        # ─── Case 2: Scrolling ───────────────────────────────────────────────
        elif "scroll" in req_lower:
            amount = -300 if any(kw in req_lower for kw in ["down", "neeche", "niche"]) else 300
            act = Action(
                action_type=ActionType.SCROLL,
                parameters={"amount": amount},
                target=ActionTarget(semantic_label="scroll area")
            )
            actions.append(act)

        # ─── Case 3: Text Typing ──────────────────────────────────────────────
        elif any(req_lower.startswith(kw) for kw in ["type ", "write ", "write: ", "type: ", "enter text "]):
            text_content = re.sub(r"(?i)^(type|write|write:|type:|enter text)\s+", "", req).strip().strip("'\"")
            submit_flag = any(kw in req_lower for kw in ["and send", "and submit", "and enter"])
            target_app_explicit = active_app if ("in " in req_lower or "isme" in req_lower) else None
            act = Action(
                action_type=ActionType.TYPE,
                parameters={"text": text_content, "target_app": target_app_explicit, "submit": submit_flag},
                target=ActionTarget(semantic_label="active text field")
            )
            actions.append(act)

        # ─── Case 4: Click Element ───────────────────────────────────────────
        elif "click" in req_lower or "dabao" in req_lower or "press button" in req_lower:
            target_label = re.sub(r"(?i)^(click|click on|dabao|press button|ispe click karo)\s+", "", req).strip()
            if not target_label or target_label == req:
                target_label = "button"

            # Resolve target spatial coordinates using Phase 4 Vision
            res_result = self.target_resolver.resolve_target(target_label)
            act = Action(
                action_type=ActionType.CLICK,
                target=res_result.target,
                confidence=res_result.confidence,
                parameters={"semantic_label": target_label}
            )
            actions.append(act)

        # ─── Fallback Generic Action ──────────────────────────────────────────
        else:
            act = Action(
                action_type=ActionType.CLICK,
                parameters={"query": req},
                target=ActionTarget(semantic_label=req)
            )
            actions.append(act)

        return actions

    def _resolve_context_references(self, request: str) -> Tuple[str, Optional[str]]:
        """
        Uses Phase 1 ConversationManager to resolve pronouns 'isme', 'ab', 'ye'.
        Returns (resolved_request_string, active_app_name).
        """
        active_entity = getattr(self.conversation_manager, "active_entity", None) or "Notepad"

        resolved = request
        req_lower = request.lower()

        if any(pronoun in req_lower for pronoun in ["isme", "ab isme", "is me"]):
            resolved = re.sub(r"(?i)\bisme\b", f"in {active_entity}", resolved)
            resolved = re.sub(r"(?i)\bis me\b", f"in {active_entity}", resolved)

        return resolved, active_entity
