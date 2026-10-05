"""
tools/email/email_agent.py
Email Agent for JARVIS Agent Orchestrator.
Wraps EmailService, implements task handlers for TaskType.EMAIL, and returns AgentResult.
"""

import time
import logging
from typing import Any, Dict, Optional

from agent.agent_result import AgentResult, AgentResultStatus
from agent.task_model import TaskModel, StepModel
from tools.email.email_service import EmailService

logger = logging.getLogger("EmailAgent")

class EmailAgent:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = EmailAgent()
        return cls._instance

    def __init__(self):
        self.service = EmailService.get_instance()

    def handle_task(self, task: TaskModel, step: StepModel) -> AgentResult:
        start_t = time.time()
        query = task.normalized_goal or task.user_request
        q_lower = query.lower().strip()

        print(f"[EMAIL_AGENT] task_id={task.task_id} query='{query}'", flush=True)

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
                        agent_id="email_agent",
                        status=AgentResultStatus.CANCELLED,
                        result=res_str,
                        duration_ms=dur
                    )
                elif c_mgr.is_affirmative_response(query):
                    # Check OAuth auth status before sending
                    if not self.service.client.auth_mgr.is_authenticated() and not task.metadata.get("allow_mock", False):
                        res_str = "Boss, Gmail OAuth authentication required before sending emails."
                        dur = (time.time() - start_t) * 1000.0
                        return AgentResult(
                            success=False,
                            task_id=task.task_id,
                            agent_id="email_agent",
                            status=AgentResultStatus.AUTH_REQUIRED,
                            result=res_str,
                            duration_ms=dur
                        )

                    res_str = self.service.execute_confirmed_action(query)
                    dur = (time.time() - start_t) * 1000.0
                    is_success = "sent" in res_str.lower() or "successfully" in res_str.lower() or "moved to trash" in res_str.lower()
                    return AgentResult(
                        success=is_success,
                        task_id=task.task_id,
                        agent_id="email_agent",
                        status=AgentResultStatus.SUCCESS if is_success else AgentResultStatus.FAILURE,
                        result=res_str,
                        duration_ms=dur
                    )

            # 2. Handle initial requests
            if any(kw in q_lower for kw in ["send email", "send mail", "email bhejo", "send kar do", "mail send"]):
                prompt = self.service.prepare_send(request_id=task.request_id)
                dur = (time.time() - start_t) * 1000.0
                return AgentResult(
                    success=False,
                    task_id=task.task_id,
                    agent_id="email_agent",
                    status=AgentResultStatus.WAITING_FOR_CONFIRMATION,
                    result=prompt,
                    duration_ms=dur
                )

            if any(kw in q_lower for kw in ["summary", "summarize", "kis baare", "important points"]):
                res_str = self.service.summarize_email()
            elif any(kw in q_lower for kw in ["reply draft", "draft reply", "draft karo"]):
                res_str = self.service.create_draft_reply(request_id=task.request_id)
            elif any(kw in q_lower for kw in ["open email", "read email", "email kholo", "email dikhao"]):
                res_str = self.service.read_email()
            else:
                res_str = self.service.search_and_format(query)

            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=True,
                task_id=task.task_id,
                agent_id="email_agent",
                status=AgentResultStatus.SUCCESS,
                result=res_str,
                duration_ms=dur
            )

        except Exception as e:
            dur = (time.time() - start_t) * 1000.0
            logger.error(f"EmailAgent task handling failed: {e}")
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id="email_agent",
                status=AgentResultStatus.FAILURE,
                error=str(e),
                duration_ms=dur
            )
