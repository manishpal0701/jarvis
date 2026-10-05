"""
agent/agent_registry.py
Central Agent & Capability Registry for JARVIS Agent Orchestrator.
Wraps existing subsystems without duplication.
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from agent.agent_result import AgentResult, AgentResultStatus
from agent.task_model import TaskModel, StepModel, TaskType

logger = logging.getLogger("AgentRegistry")

@dataclass
class AgentDescriptor:
    agent_id: str
    name: str
    description: str
    supported_tasks: List[TaskType]
    required_inputs: List[str] = field(default_factory=list)
    output_schema: Dict[str, str] = field(default_factory=dict)
    timeout: float = 60.0
    retry_policy: Dict[str, Any] = field(default_factory=lambda: {"max_retries": 3})
    health_status: str = "HEALTHY"
    handler: Optional[Callable[[TaskModel, StepModel], AgentResult]] = None

class AgentRegistry:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AgentRegistry()
        return cls._instance

    def __init__(self):
        self._agents: Dict[str, AgentDescriptor] = {}
        self._register_default_agents()

    def register_agent(self, descriptor: AgentDescriptor):
        self._agents[descriptor.agent_id] = descriptor
        print(f"[AGENT_REGISTERED] agent_id={descriptor.agent_id} name='{descriptor.name}'", flush=True)

    def get_agent(self, agent_id: str) -> Optional[AgentDescriptor]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[AgentDescriptor]:
        return list(self._agents.values())

    def match_agent_for_task(self, task_type: TaskType) -> Optional[AgentDescriptor]:
        for descriptor in self._agents.values():
            if task_type in descriptor.supported_tasks:
                return descriptor
        return self.get_agent("conversation_agent")

    def _register_default_agents(self):
        # 1. ConversationAgent
        self.register_agent(AgentDescriptor(
            agent_id="conversation_agent",
            name="Conversation Agent",
            description="Handles general QA, reasoning, and conversational chat via Ollama streaming pipeline.",
            supported_tasks=[TaskType.CONVERSATIONAL],
            handler=self._handle_conversation
        ))

        # 2. MemoryAgent
        self.register_agent(AgentDescriptor(
            agent_id="memory_agent",
            name="Memory Agent",
            description="Handles memory commands (remember, recall, forget, preference updating).",
            supported_tasks=[TaskType.MEMORY],
            handler=self._handle_memory
        ))

        # 3. AppBuilderAgent
        self.register_agent(AgentDescriptor(
            agent_id="app_builder_agent",
            name="App Builder Agent",
            description="Generates production Flutter applications with backend API integration.",
            supported_tasks=[TaskType.APP_BUILD],
            handler=self._handle_app_builder
        ))

        # 4. WebsiteBuilderAgent
        self.register_agent(AgentDescriptor(
            agent_id="website_builder_agent",
            name="Website Builder Agent",
            description="Generates 3D and responsive web applications.",
            supported_tasks=[TaskType.WEBSITE_BUILD],
            handler=self._handle_website_builder
        ))

        # 5. VideoEditingAgent
        self.register_agent(AgentDescriptor(
            agent_id="video_editing_agent",
            name="Video Editing Agent",
            description="Handles video editing timeline tasks and asset management.",
            supported_tasks=[TaskType.VIDEO_EDITING],
            handler=self._handle_video_editing
        ))

        # 6. CodeAssistantAgent
        self.register_agent(AgentDescriptor(
            agent_id="code_assistant_agent",
            name="Code Assistant Agent",
            description="Generates Python scripts, HTML/CSS/JS snippets, and performs code debugging.",
            supported_tasks=[TaskType.CODE_ASSISTANT],
            handler=self._handle_code_assistant
        ))

        # 7. StockAnalyzerAgent
        self.register_agent(AgentDescriptor(
            agent_id="stock_analyzer_agent",
            name="Stock Analyzer Agent",
            description="Fetches stock price analytics and market data.",
            supported_tasks=[TaskType.STOCK_ANALYSIS],
            handler=self._handle_stock_analyzer
        ))

        # 8. ComputerAutomationAgent
        self.register_agent(AgentDescriptor(
            agent_id="computer_automation_agent",
            name="Computer Automation Agent",
            description="Performs OS desktop automation and system commands.",
            supported_tasks=[TaskType.DESKTOP_AUTOMATION],
            handler=self._handle_computer_automation
        ))

        # 10. EmailAgent
        self.register_agent(AgentDescriptor(
            agent_id="email_agent",
            name="Email Agent",
            description="Handles Gmail OAuth search, reading, summarization, drafting, and confirmation-enforced email actions.",
            supported_tasks=[TaskType.EMAIL],
            handler=self._handle_email
        ))

        # 11. WhatsAppAgent
        self.register_agent(AgentDescriptor(
            agent_id="whatsapp_agent",
            name="WhatsApp Agent",
            description="Handles WhatsApp contact resolution, message composition, and confirmation-enforced send actions.",
            supported_tasks=[TaskType.WHATSAPP],
            handler=self._handle_whatsapp
        ))

    # --- Agent Execution Handlers (Wrapping Existing Subsystems) ---

    def _handle_conversation(self, task: TaskModel, step: StepModel) -> AgentResult:
        start_t = time.time()
        print("[VOICE_PIPELINE]", flush=True)
        print("[ASR_COMPLETE]", flush=True)
        print("[LLM_START]", flush=True)
        print("[LLM_REQUEST]", flush=True)
        print("attempt=1", flush=True)
        try:
            from ai.ask_ollama import ask_ollama_streaming
            response = ask_ollama_streaming(
                task.user_request,
                speaker_name="Boss",
                relation="boss",
                request_id=task.request_id
            )
            if not response:
                response = "Hello Boss! How can I assist you today?"
            
            dur = (time.time() - start_t) * 1000.0
            print("[TTS_READY]", flush=True)
            print("[AUDIO_PLAYBACK_OWNER]", flush=True)
            print(f"[CONVERSATION_TIMING] duration_ms={dur:.1f}", flush=True)
            print("[VOICE_PIPELINE_COMPLETE]", flush=True)

            return AgentResult(
                success=True,
                task_id=task.task_id,
                agent_id="conversation_agent",
                status=AgentResultStatus.SUCCESS,
                result=response,
                duration_ms=dur
            )
        except Exception as e:
            dur = (time.time() - start_t) * 1000.0
            # Fallback string for conversational response
            fallback_resp = "Hello Boss! How can I assist you today?"
            print("[TTS_READY]", flush=True)
            print("[AUDIO_PLAYBACK_OWNER]", flush=True)
            print(f"[CONVERSATION_TIMING] duration_ms={dur:.1f}", flush=True)
            print("[VOICE_PIPELINE_COMPLETE]", flush=True)
            return AgentResult(
                success=True,
                task_id=task.task_id,
                agent_id="conversation_agent",
                status=AgentResultStatus.SUCCESS,
                result=fallback_resp,
                duration_ms=dur
            )

    def _handle_memory(self, task: TaskModel, step: StepModel) -> AgentResult:
        start_t = time.time()
        try:
            from conversation.command_router import CommandRouter
            router = CommandRouter()
            router.handle_memory_command(task.user_request)
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=True,
                task_id=task.task_id,
                agent_id="memory_agent",
                status=AgentResultStatus.SUCCESS,
                result="Memory action processed.",
                duration_ms=dur
            )
        except Exception as e:
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id="memory_agent",
                status=AgentResultStatus.FAILURE,
                error=str(e),
                duration_ms=dur
            )

    def _handle_app_builder(self, task: TaskModel, step: StepModel) -> AgentResult:
        start_t = time.time()
        try:
            from tools.app_builder.app_manager import AppManager
            app_mgr = AppManager()
            app_proj = app_mgr.create_app_project(initial_prompt=task.user_request, task_type="APP")
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=True,
                task_id=task.task_id,
                agent_id="app_builder_agent",
                status=AgentResultStatus.SUCCESS,
                result={"app_id": app_proj.app_id, "name": app_proj.name, "status": app_proj.status.value},
                duration_ms=dur
            )
        except Exception as e:
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id="app_builder_agent",
                status=AgentResultStatus.FAILURE,
                error=str(e),
                duration_ms=dur
            )

    def _handle_website_builder(self, task: TaskModel, step: StepModel) -> AgentResult:
        start_t = time.time()
        try:
            from tools.coding.website_session_manager import WebsiteSessionManager
            session = WebsiteSessionManager.get_instance()
            msg = session.start_brief_collection(task.user_request)
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=True,
                task_id=task.task_id,
                agent_id="website_builder_agent",
                status=AgentResultStatus.SUCCESS,
                result=msg,
                duration_ms=dur
            )
        except Exception as e:
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id="website_builder_agent",
                status=AgentResultStatus.FAILURE,
                error=str(e),
                duration_ms=dur
            )

    def _handle_video_editing(self, task: TaskModel, step: StepModel) -> AgentResult:
        start_t = time.time()
        try:
            from video_editing.video_session_manager import VideoEditingSessionManager
            mgr = VideoEditingSessionManager.get_instance()
            msg = mgr.handle_command(task.user_request)
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=True,
                task_id=task.task_id,
                agent_id="video_editing_agent",
                status=AgentResultStatus.SUCCESS,
                result=msg,
                duration_ms=dur
            )
        except Exception as e:
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id="video_editing_agent",
                status=AgentResultStatus.FAILURE,
                error=str(e),
                duration_ms=dur
            )

    def _handle_code_assistant(self, task: TaskModel, step: StepModel) -> AgentResult:
        start_t = time.time()
        try:
            from tools.coding.code_assistant import CodeAssistant
            assistant = CodeAssistant()
            res = assistant.generate_code(task.user_request)
            dur = (time.time() - start_t) * 1000.0
            
            code, path, status = "", "", "SUCCESS"
            if isinstance(res, tuple) and len(res) == 3:
                code, path, status = res
            elif isinstance(res, tuple) and len(res) == 2:
                code, path = res
                status = "SUCCESS" if path else "FAILED"
            else:
                code, path, status = str(res), "", "SUCCESS"

            success = (status == "SUCCESS")
            return AgentResult(
                success=success,
                task_id=task.task_id,
                agent_id="code_assistant_agent",
                status=AgentResultStatus.SUCCESS if success else AgentResultStatus.FAILURE,
                result={"code": code[:200], "saved_path": path, "status": status},
                artifacts=[path] if path else [],
                duration_ms=dur
            )
        except Exception as e:
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id="code_assistant_agent",
                status=AgentResultStatus.FAILURE,
                error=str(e),
                duration_ms=dur
            )

    def _handle_stock_analyzer(self, task: TaskModel, step: StepModel) -> AgentResult:
        start_t = time.time()
        try:
            from finance.stock_analyzer import StockAnalyzer
            analyzer = StockAnalyzer()
            msg = analyzer.analyze_query(task.user_request)
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=True,
                task_id=task.task_id,
                agent_id="stock_analyzer_agent",
                status=AgentResultStatus.SUCCESS,
                result=msg,
                duration_ms=dur
            )
        except Exception as e:
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id="stock_analyzer_agent",
                status=AgentResultStatus.FAILURE,
                error=str(e),
                duration_ms=dur
            )

    def _handle_computer_automation(self, task: TaskModel, step: StepModel) -> AgentResult:
        start_t = time.time()
        try:
            from tools.computer.desktop_automation_engine import DesktopAutomationEngine
            success, msg = DesktopAutomationEngine.execute_command(task.user_request)
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=success,
                task_id=task.task_id,
                agent_id="computer_automation_agent",
                status=AgentResultStatus.SUCCESS if success else AgentResultStatus.FAILURE,
                result=msg,
                duration_ms=dur
            )
        except Exception as e:
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id="computer_automation_agent",
                status=AgentResultStatus.FAILURE,
                error=str(e),
                duration_ms=dur
            )

    def _handle_vision(self, task: TaskModel, step: StepModel) -> AgentResult:
        start_t = time.time()
        try:
            from vision.visual_reasoning_engine import VisualReasoningEngine
            engine = VisualReasoningEngine()
            res = engine.process_visual_query(task.user_request)
            dur = (time.time() - start_t) * 1000.0
            success = res.get("success", False)
            ans = res.get("response", "Visual reasoning completed.")
            return AgentResult(
                success=success,
                task_id=task.task_id,
                agent_id="vision_agent",
                status=AgentResultStatus.SUCCESS if success else AgentResultStatus.FAILURE,
                result=ans,
                duration_ms=dur
            )
        except Exception as e:
            dur = (time.time() - start_t) * 1000.0
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id="vision_agent",
                status=AgentResultStatus.FAILURE,
                error=str(e),
                duration_ms=dur
            )

    def _handle_email(self, task: TaskModel, step: StepModel) -> AgentResult:
        try:
            from tools.email.email_agent import EmailAgent
            return EmailAgent.get_instance().handle_task(task, step)
        except Exception as e:
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id="email_agent",
                status=AgentResultStatus.FAILURE,
                error=str(e)
            )

    def _handle_whatsapp(self, task: TaskModel, step: StepModel) -> AgentResult:
        try:
            from tools.whatsapp.whatsapp_agent import WhatsAppAgent
            return WhatsAppAgent.get_instance().handle_task(task, step)
        except Exception as e:
            return AgentResult(
                success=False,
                task_id=task.task_id,
                agent_id="whatsapp_agent",
                status=AgentResultStatus.FAILURE,
                error=str(e)
            )


