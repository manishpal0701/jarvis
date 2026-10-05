"""
tools/whatsapp/whatsapp_agent.py
WhatsApp Agent for JARVIS Agent Orchestrator.
Wraps WhatsAppService, implements task handlers for TaskType.WHATSAPP, and returns AgentResult.
"""

import time
import re
import logging
from typing import Any, Dict, Optional

from agent.agent_result import AgentResult, AgentResultStatus
from agent.task_model import TaskModel, StepModel
from tools.whatsapp.whatsapp_service import WhatsAppService
from tools.whatsapp.whatsapp_provider import MockWhatsAppProvider
from tools.whatsapp.contact_resolver import ContactResolutionStatus

logger = logging.getLogger("WhatsAppAgent")

class WhatsAppAgent:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = WhatsAppAgent()
        return cls._instance

    def __init__(self):
        self.service = WhatsAppService.get_instance()

    def handle_task(self, task: TaskModel, step: StepModel) -> AgentResult:
        start_t = time.time()
        query = task.normalized_goal or task.user_request
        print(f"[WHATSAPP_AGENT] task_id={task.task_id} query='{query}'", flush=True)

        try:
            from tools.computer.confirmation_manager import ConfirmationManager
            c_mgr = ConfirmationManager.get_instance()

            # 1. Handle confirmation execution if user responded to prompt
            if self.service.conf_mgr.has_pending_confirmation():
                if c_mgr.is_negative_response(query):
                    res_str = self.service.execute_confirmed_action(query)
                    dur = (time.time() - start_t) * 1000.0
                    return AgentResult(
                        success=False,
                        task_id=task.task_id,
                        agent_id="whatsapp_agent",
                        status=AgentResultStatus.CANCELLED,
                        result=res_str,
                        duration_ms=dur
                    )
                elif c_mgr.is_affirmative_response(query):
                    meta = task.metadata or {}
                    if isinstance(self.service.provider, MockWhatsAppProvider) and not meta.get("allow_mock", False):
                        res_str = "Boss, WhatsApp integration configured or authenticated nahi hai."
                        dur = (time.time() - start_t) * 1000.0
                        return AgentResult(
                            success=False,
                            task_id=task.task_id,
                            agent_id="whatsapp_agent",
                            status=AgentResultStatus.NOT_IMPLEMENTED,
                            result=res_str,
                            duration_ms=dur
                        )

                    res_str = self.service.execute_confirmed_action(query)
                    dur = (time.time() - start_t) * 1000.0
                    is_success = "sent" in res_str.lower() or "successfully" in res_str.lower()
                    return AgentResult(
                        success=is_success,
                        task_id=task.task_id,
                        agent_id="whatsapp_agent",
                        status=AgentResultStatus.SUCCESS if is_success else AgentResultStatus.FAILURE,
                        result=res_str,
                        duration_ms=dur
                    )

            # 2. Process initial WhatsApp request
            res_str = self.service.process_whatsapp_request(query, request_id=task.request_id)

            # Check if pending confirmation was registered
            if self.service.conf_mgr.has_pending_confirmation():
                dur = (time.time() - start_t) * 1000.0
                return AgentResult(
                    success=False,
                    task_id=task.task_id,
                    agent_id="whatsapp_agent",
                    status=AgentResultStatus.WAITING_FOR_CONFIRMATION,
                    result=res_str,
                    duration_ms=dur
                )

            # Check if contact is ambiguous or not found or provider unavailable
            if "contacts mile hain" in res_str:
                dur = (time.time() - start_t) * 1000.0
                return AgentResult(
                    success=False,
                    task_id=task.task_id,
                    agent_id="whatsapp_agent",
                    status=AgentResultStatus.AMBIGUOUS,
                    result=res_str,
                    duration_ms=dur
                )

            if "available nahi hai" in res_str or "service unavailable" in res_str:
                dur = (time.time() - start_t) * 1000.0
                return AgentResult(
                    success=False,
                    task_id=task.task_id,
                    agent_id="whatsapp_agent",
                    status=AgentResultStatus.PROVIDER_UNAVAILABLE,
                    result=res_str,
                    duration_ms=dur
                )

            if "authentication required" in res_str or "auth required" in res_str:
                dur = (time.time() - start_t) * 1000.0
                return AgentResult(
                    success=False,
                    task_id=task.task_id,
                    agent_id="whatsapp_agent",
                    status=AgentResultStatus.AUTH_REQUIRED,
                    result=res_str,
                    duration_ms=dur
                )

            if "contact nahi mila" in res_str or "missing" in res_str:
                dur = (time.time() - start_t) * 1000.0
                return AgentResult(
                    success=False,
                    task_id=task.task_id,
                    agent_id="whatsapp_agent",
                    status=AgentResultStatus.FAILURE,
                    result=res_str,
                    duration_ms=dur
                )

            # Default fallback execution result
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id="whatsapp_agent",
                status=AgentResultStatus.FAILURE,
                result=res_str,
                duration_ms=dur
            )

        except Exception as e:
            dur = (time.time() - start_t) * 1000.0
            logger.error(f"WhatsAppAgent task handling failed: {e}")
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id="whatsapp_agent",
                status=AgentResultStatus.FAILURE,
                error=str(e),
                duration_ms=dur
            )
