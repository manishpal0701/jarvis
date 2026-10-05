"""
agent/task_planner.py
Proportional Task Planner for JARVIS Agent Orchestrator.
Converts user requests into executable, dependency-aware task plans.
Integrates Phase 1 Conversation Intelligence context and Memory 2.0 user preferences.
"""

import uuid
import time
import re

from agent.task_model import TaskModel, StepModel, TaskType, TaskPriority
from conversation.conversation_manager import ConversationManager
from memory.memory_manager import MemoryManager

class TaskPlanner:
    """
    Task Planner generating proportional plans based on user goal complexity.
    """
    def __init__(self):
        self._conv = ConversationManager.get_instance()
        self._mem = MemoryManager()

    def generate_plan(self, user_request: str, request_id: str = None) -> TaskModel:
        req_id = request_id or f"req_{uuid.uuid4().hex[:8]}"
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        # Resolve Phase 1 context and active entity
        resolved_info = self._conv.process_and_resolve_input(user_request)
        effective_query = resolved_info.get("resolved_text", user_request)

        # Retrieve Phase 1 user preferences
        user_mems = self._mem.recall(effective_query, limit=3)
        preferences_summary = [m.get("content", "") for m in user_mems if m.get("content")]

        # Classify task type and complexity
        task_type, is_complex = self._classify_task(effective_query)
        priority = TaskPriority.HIGH if is_complex else TaskPriority.NORMAL

        task = TaskModel(
            task_id=task_id,
            request_id=req_id,
            user_request=user_request,
            normalized_goal=effective_query,
            task_type=task_type,
            priority=priority,
            status="CREATED",
            metadata={
                "context_resolved": resolved_info,
                "user_preferences": preferences_summary
            }
        )

        # Generate proportional step graph
        steps = self._build_steps(task, effective_query, task_type, is_complex)
        task.steps = steps
        task.total_steps = len(steps)

        print(f"[TASK_PLANNER] task_id={task_id} type={task_type.value} steps={len(steps)} complex={is_complex}", flush=True)
        return task

    def _classify_task(self, query: str) -> tuple[TaskType, bool]:
        text = query.lower().strip()

        # 1. App Builder Intent
        from tools.app_builder.app_intent_router import AppIntentRouter
        if AppIntentRouter.is_app_build_intent(query) or "flutter" in text or "expense tracker app" in text or "task manager app" in text:
            is_complex = any(w in text for w in ["backend", "fastapi", "auth", "search", "dark mode", "database", "production", "full", "complete"])
            return TaskType.APP_BUILD, is_complex

        # 2. Website Builder Intent
        if any(kw in text for kw in ["create website", "build website", "make website", "website bana"]):
            is_complex = any(w in text for w in ["database", "fullstack", "custom", "3d"])
            return TaskType.WEBSITE_BUILD, is_complex

        # 3. Video Editing Intent
        from video_editing.video_intent_router import classify_video_intent, INTENT_GENERAL_CONVERSATION
        v_intent = classify_video_intent(query).get("intent")
        if v_intent != INTENT_GENERAL_CONVERSATION:
            return TaskType.VIDEO_EDITING, False

        # 4. Memory Commands
        if any(kw in text for kw in ["remember that", "forget that", "recall", "what framework do i"]):
            return TaskType.MEMORY, False

        # 5. Stock Analytics
        if any(kw in text for kw in ["stock price", "share price", "stock analysis"]):
            return TaskType.STOCK_ANALYSIS, False

        # 6. Email Intent
        if any(kw in text for kw in ["unread emails", "gmail", "email check", "email search", "email send", "reply draft", "email kholo", "email dikhao", "mail send", "send mail", "send email"]):
            return TaskType.EMAIL, False

        # 7. WhatsApp Intent
        if any(kw in text for kw in ["whatsapp", "message bhejo", "ko message", "whatsapp karo"]):
            return TaskType.WHATSAPP, False

        # 8. Desktop Automation Intent
        from tools.computer.desktop_automation_engine import DesktopAutomationEngine
        if DesktopAutomationEngine.is_desktop_command(query):
            return TaskType.DESKTOP_AUTOMATION, False

        # 9. Code Assistant
        if any(kw in text for kw in ["write script", "python script", "calculator code", "write html"]):
            return TaskType.CODE_ASSISTANT, False

        # Default Conversational
        return TaskType.CONVERSATIONAL, False

    def _build_steps(self, task: TaskModel, query: str, task_type: TaskType, is_complex: bool) -> list[StepModel]:
        # 1. Simple Conversational or Single-Turn Tasks
        if task_type == TaskType.CONVERSATIONAL:
            return [
                StepModel(
                    step_id=f"{task.task_id}_s1",
                    task_id=task.task_id,
                    name="Conversational Response",
                    description="Generate conversational response via Ollama streaming engine",
                    agent_id="conversation_agent",
                    status="READY"
                )
            ]

        if task_type == TaskType.EMAIL:
            return [
                StepModel(
                    step_id=f"{task.task_id}_s1",
                    task_id=task.task_id,
                    name="Email Agent Action",
                    description="Execute Gmail search, read, draft, or confirmation-enforced email action",
                    agent_id="email_agent",
                    status="READY"
                )
            ]

        if task_type == TaskType.WHATSAPP:
            return [
                StepModel(
                    step_id=f"{task.task_id}_s1",
                    task_id=task.task_id,
                    name="WhatsApp Agent Action",
                    description="Execute WhatsApp contact resolution, composition, or confirmation-enforced send action",
                    agent_id="whatsapp_agent",
                    status="READY"
                )
            ]

        if task_type == TaskType.MEMORY:
            return [
                StepModel(
                    step_id=f"{task.task_id}_s1",
                    task_id=task.task_id,
                    name="Memory Command Execution",
                    description="Execute memory store/recall/forget operation",
                    agent_id="memory_agent",
                    status="READY"
                )
            ]

        if task_type == TaskType.STOCK_ANALYSIS:
            return [
                StepModel(
                    step_id=f"{task.task_id}_s1",
                    task_id=task.task_id,
                    name="Stock Analysis Query",
                    description="Fetch stock telemetry and market analysis",
                    agent_id="stock_analyzer_agent",
                    status="READY"
                )
            ]

        if task_type == TaskType.DESKTOP_AUTOMATION:
            return [
                StepModel(
                    step_id=f"{task.task_id}_s1",
                    task_id=task.task_id,
                    name="Desktop Automation Execution",
                    description="Execute OS desktop command",
                    agent_id="computer_automation_agent",
                    status="READY"
                )
            ]

        if task_type == TaskType.VIDEO_EDITING:
            return [
                StepModel(
                    step_id=f"{task.task_id}_s1",
                    task_id=task.task_id,
                    name="Video Editing Command",
                    description="Execute video editing timeline operation",
                    agent_id="video_editing_agent",
                    status="READY"
                )
            ]

        if task_type == TaskType.CODE_ASSISTANT:
            return [
                StepModel(
                    step_id=f"{task.task_id}_s1",
                    task_id=task.task_id,
                    name="Code Generation",
                    description="Generate script/code via Code Assistant",
                    agent_id="code_assistant_agent",
                    status="READY"
                )
            ]

        # 2. Multi-step Complex App / Website Build Tasks
        if task_type in {TaskType.APP_BUILD, TaskType.WEBSITE_BUILD}:
            if not is_complex:
                return [
                    StepModel(
                        step_id=f"{task.task_id}_s1",
                        task_id=task.task_id,
                        name="Project Build Execution",
                        description=f"Execute {task_type.value} creation workflow",
                        agent_id="app_builder_agent" if task_type == TaskType.APP_BUILD else "website_builder_agent",
                        status="READY"
                    )
                ]

            # Multi-step dependency graph for complex builds
            s1_id = f"{task.task_id}_s1"
            s2_id = f"{task.task_id}_s2"
            s3_id = f"{task.task_id}_s3"
            s4_id = f"{task.task_id}_s4"
            s5_id = f"{task.task_id}_s5"

            agent_id = "app_builder_agent" if task_type == TaskType.APP_BUILD else "website_builder_agent"

            step1 = StepModel(
                step_id=s1_id,
                task_id=task.task_id,
                name="Requirements & Architecture Spec",
                description="Analyze requirements, domain brief, and design architecture plan",
                agent_id=agent_id,
                status="READY"
            )

            step2 = StepModel(
                step_id=s2_id,
                task_id=task.task_id,
                name="Frontend Generation",
                description="Generate Flutter UI components / Web layout",
                agent_id=agent_id,
                status="CREATED",
                dependencies=[s1_id]
            )

            step3 = StepModel(
                step_id=s3_id,
                task_id=task.task_id,
                name="Backend API Generation",
                description="Generate Node.js / FastAPI endpoints and database schemas",
                agent_id=agent_id,
                status="CREATED",
                dependencies=[s1_id]
            )

            step4 = StepModel(
                step_id=s4_id,
                task_id=task.task_id,
                name="API Integration & Wiring",
                description="Connect frontend state management to backend endpoints",
                agent_id=agent_id,
                status="CREATED",
                dependencies=[s2_id, s3_id]
            )

            step5 = StepModel(
                step_id=s5_id,
                task_id=task.task_id,
                name="Build & Runtime Verification",
                description="Execute static analysis, build verification, and preview check",
                agent_id=agent_id,
                status="CREATED",
                dependencies=[s4_id]
            )

            return [step1, step2, step3, step4, step5]

        # Default Fallback
        return [
            StepModel(
                step_id=f"{task.task_id}_s1",
                task_id=task.task_id,
                name="Task Execution",
                description="Execute request",
                agent_id="conversation_agent",
                status="READY"
            )
        ]
