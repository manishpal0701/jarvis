import re
import sys
import logging
import webbrowser

logger = logging.getLogger("CommandRouter")

# Ensure UTF-8 output encoding for Windows stdout/stderr
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

class CommandRouter:
    """
    Unified Command Router for Jarvis.
    Maps user input to system tools, feature subpackages, or Ollama conversational AI.
    """

    def __init__(self, speech_coordinator=None, speak_callback=None):
        if speech_coordinator is None:
            try:
                from conversation.conversation_engine import ConversationEngine
                engine = ConversationEngine()
                if hasattr(engine, "speech_coordinator") and engine.speech_coordinator:
                    speech_coordinator = engine.speech_coordinator
            except Exception:
                pass
        self.speech_coordinator = speech_coordinator
        self.speak_callback = speak_callback
        self._code_assistant = None
        self._stock_analyzer = None
        self._face_recognizer = None

    def _speak(self, text: str, request_id: str = None):
        if not text:
            return
        text_str = str(text)
        if self.speak_callback:
            try:
                self.speak_callback(text_str)
            except Exception as e:
                print(f"[CommandRouter Speak Callback Error]: {e}", flush=True)

        coordinator = self.speech_coordinator
        if not coordinator:
            try:
                from conversation.conversation_engine import ConversationEngine
                engine = ConversationEngine()
                if hasattr(engine, "speech_coordinator") and engine.speech_coordinator:
                    coordinator = engine.speech_coordinator
            except Exception:
                pass

        if coordinator:
            try:
                coordinator.speak(text_str, wait=False, request_id=request_id)
            except Exception as e:
                print(f"[CommandRouter TTS Error]: {e}", flush=True)
        else:
            try:
                print(f"Jarvis: {text_str}", flush=True)
            except Exception:
                print(f"Jarvis: {text_str.encode('ascii', 'ignore').decode('ascii')}", flush=True)

    def _on_ollama_chunk(self, text: str):
        """Callback for Ollama streaming chunks to capture text output without triggering duplicate TTS."""
        if not text:
            return
        text_str = str(text)
        if self.speak_callback:
            try:
                self.speak_callback(text_str)
            except Exception as e:
                print(f"[CommandRouter Speak Callback Error]: {e}", flush=True)
        else:
            try:
                print(f"Jarvis: {text_str}", flush=True)
            except Exception:
                pass

    def get_code_assistant(self):
        if self._code_assistant is None:
            from tools.coding.code_assistant import CodeAssistant
            self._code_assistant = CodeAssistant()
        return self._code_assistant

    def get_stock_analyzer(self):
        if self._stock_analyzer is None:
            try:
                from finance.stock_analyzer import StockAnalyzer
                self._stock_analyzer = StockAnalyzer()
            except Exception as e:
                print(f"StockAnalyzer import error: {e}")
        return self._stock_analyzer

    def get_face_recognizer(self):
        if self._face_recognizer is None:
            try:
                from vision.face_recognize import FaceRecognizer
                self._face_recognizer = FaceRecognizer()
            except Exception as e:
                print(f"FaceRecognizer import error: {e}")
        return self._face_recognizer

    def is_status_query(self, cmd: str) -> bool:
        cmd_lower = cmd.lower().strip()
        status_keywords = [
            "kitna kaam hua", "kitna progress", "kaha tak pahuchi", "kahan tak pahunchi",
            "kaha tak hua", "progress kya hai", "status kya hai", "website ready",
            "website ready hai", "website ka kya hua", "abhi kya ho raha hai",
            "kya website complete ho gayi", "website bani", "build status",
            "task status", "what is the status", "how is the build",
            "kitna time lagega", "progress update"
        ]
        return any(kw in cmd_lower for kw in status_keywords)

    def is_unattended_request(self, cmd: str) -> bool:
        cmd_lower = cmd.lower().strip()
        unattended_keywords = [
            "ghoom ke aata", "ghoom kar aata", "ghoomne jaa", "baad me dekhunga",
            "baad mein dekhunga", "main chala", "mai chala", "leave for a bit",
            "step out", "going out"
        ]
        return any(kw in cmd_lower for kw in unattended_keywords)

    def is_hosting_task(self, cmd: str) -> bool:
        cmd_lower = cmd.lower()
        host_keywords = [
            "isko host karo", "isko host krdo", "website host", "permanently deploy",
            "permanently host", "website live kar do", "website live krdo",
            "host this website", "host karo", "deploy website", "is website ko host"
        ]
        return any(kw in cmd_lower for kw in host_keywords)

    def is_coding_task(self, cmd: str) -> bool:
        cmd_lower = cmd.lower().strip()
        
        # 1. Explicit creation / build imperatives
        build_patterns = [
            r"\b(bana|banaa)\s*(do|banao)\b",
            r"\b(create|make|build|generate|write)\s+.*(website|web|page|site|app|script|program|code|calculator)\b",
            r"\b(website|app|script|program)\s+(bana|banaa|create|build|make)\b",
            r"\b(python|html|css|javascript)\s+(script|program|app|code)\b"
        ]
        has_explicit_build = any(re.search(pat, cmd_lower) for pat in build_patterns)
        if has_explicit_build:
            return True

        # 2. Q&A / Conversational phrasing check
        qa_phrases = [
            "what is", "what are", "explain", "can i", "how to", "tell me", "who is",
            "why is", "how does", "what can", "i'm tired", "i am tired", "thank you",
            "thanks", "good morning", "hello", "hi jarvis", "how are you"
        ]
        is_qa_phrasing = any(phrase in cmd_lower for phrase in qa_phrases)
        if is_qa_phrasing:
            return False

        # 3. Secondary creation keywords fallback
        coding_keywords = [
            "create website", "build website", "make website", "create script",
            "write script", "create app", "write code", "generate code"
        ]
        return any(kw in cmd_lower for kw in coding_keywords)

    def is_memory_command(self, cmd: str) -> bool:
        cmd_lower = cmd.lower().strip()
        memory_keywords = [
            "remember that", "remember my", "remember i", "jarvis, remember", "jarvis remember",
            "forget that", "forget my", "forget today's conversation", "forget history", "jarvis, forget",
            "forget this conversation context", "forget conversation context", "start fresh", "new task",
            "start new task", "clear context", "clear history",
            "what do you remember", "what framework do i prefer", "what do you know about me",
            "recall my", "show my memories"
        ]
        return any(kw in cmd_lower for kw in memory_keywords) or (cmd_lower.startswith("remember ") or cmd_lower.startswith("forget "))

    def handle_memory_command(self, command: str):
        cmd_lower = command.lower().strip()
        from memory.memory_manager import MemoryManager

        # 1. Reset short-term conversation context & active task/entity
        reset_keywords = [
            "forget today's conversation", "clear history", "forget this conversation context",
            "forget conversation context", "start fresh", "new task", "start new task", "clear context"
        ]
        if any(kw in cmd_lower for kw in reset_keywords):
            from conversation.conversation_manager import ConversationManager
            ConversationManager.get_instance().reset_context()
            self._speak("Short-term conversation context reset. Ready for a new task, Boss.")
            return


        # 2. Forget command
        if "forget" in cmd_lower:
            target = re.sub(r"(?i)^(?:jarvis,?\s*)?forget\s*(?:that|my|about)?\s*", "", command).strip()
            if not target:
                target = command
            success = MemoryManager().forget(target)
            if success:
                self._speak("Matching memory removed, Boss.")
            else:
                self._speak("No matching stored memory found to forget.")
            return

        # 3. Recall command
        if "what do you remember" in cmd_lower or "what framework do i" in cmd_lower or "recall" in cmd_lower or "show my memories" in cmd_lower:
            target = re.sub(r"(?i)^(?:jarvis,?\s*)?(?:what do you remember|what framework do i|recall|show my memories)\s*(?:about|my)?\s*", "", command).strip()
            memories = MemoryManager().recall(target if target else None, limit=5)
            if memories:
                summary_lines = []
                for m in memories:
                    c = m.get("content", "")
                    if c:
                        summary_lines.append(c)
                resp = "Here is what I remember: " + "; ".join(summary_lines)
                self._speak(resp)
            else:
                self._speak("No stored memory available for that query, Boss.")
            return

        # 4. Remember command
        if "remember" in cmd_lower:
            content_to_remember = re.sub(r"(?i)^(?:jarvis,?\s*)?remember\s*(?:that)?\s*", "", command).strip()
            if not content_to_remember:
                content_to_remember = command

            # Check if key = value preference structure (e.g. "I prefer Flutter" -> key=preferred_framework)
            key = None
            value = None
            if "prefer " in content_to_remember.lower():
                val_match = re.search(r"(?i)prefer\s+([a-zA-Z0-9_\-\. ]+)", content_to_remember)
                if val_match:
                    value = val_match.group(1).strip().strip(".")
                    key = "preferred_framework" if any(f in value.lower() for f in ["flutter", "react", "vue", "python", "dart"]) else "user_preference"
            elif "favorite " in content_to_remember.lower():
                val_match = re.search(r"(?i)favorite\s+([a-zA-Z0-9_\-\. ]+)\s+is\s+([a-zA-Z0-9_\-\. ]+)", content_to_remember)
                if val_match:
                    key = f"favorite_{val_match.group(1).strip()}"
                    value = val_match.group(2).strip().strip(".")

            mem_id, status_msg = MemoryManager().remember(content_to_remember, category="user", key=key, value=value, source="explicit_user")
            if mem_id:
                self._speak("Memory stored successfully, Boss.")
            else:
                self._speak(f"Could not store memory: {status_msg}")
            return

    def is_datetime_query(self, cmd: str) -> bool:
        cmd_lower = cmd.lower().strip()

        # Strict regex matching for explicit datetime questions
        dt_patterns = [
            r"^\s*(what\s+time\s+is\s+it|what\s+is\s+the\s+time|current\s+time|time\s+kya\s+hua|time\s+kya\s+hai|kitne\s+baje\s+hain|kitne\s+baje\s+hai)\s*$",
            r"^\s*(what\s+is\s+today's\s+date|what\s+is\s+the\s+date|today's\s+date|aaj\s+ki\s+date|aaj\s+konsi\s+date\s+hai|aaj\s+kya\s+date\s+hai|current\s+date)\s*$",
            r"^\s*(what\s+day\s+is\s+today|aaj\s+konsa\s+din\s+hai|aaj\s+kya\s+din\s+hai|what\s+year\s+is\s+it|what\s+year\s+are\s+we\s+in|current\s+year|konsa\s+saal\s+hai)\s*$"
        ]

        if any(re.search(pat, cmd_lower) for pat in dt_patterns):
            return True

        dt_keywords = [
            "what time is it", "what is the time", "current time", "time kya hua", "time kya hai",
            "kitne baje hain", "kitne baje hai", "what is today's date", "what is the date",
            "today's date", "aaj ki date", "aaj konsi date hai", "aaj kya date hai", "aaj date kya", "aaj date", "current date",
            "what day is today", "aaj konsa din hai", "aaj kya din hai", "what year is it",
            "what year are we in", "current year", "konsa saal hai"
        ]

        # Multi-word feature briefs (>12 words) containing "time" or "date" are app prompts, not datetime queries
        words = cmd_lower.split()
        if len(words) > 12:
            return False

        return any(kw in cmd_lower for kw in dt_keywords)

    def is_vision_query(self, cmd: str) -> bool:
        cmd_lower = cmd.lower().strip()
        vision_patterns = [
            r"screen\s*(dekho|pe|par|check|ko|dekh)",
            r"(look|see|check|read|explain)\s*.*screen",
            r"what\s*.*on\s*my\s*screen",
            r"(ye|is|this)\s*error\s*(kya|kyu|kahan|dekho|explain)",
            r"terminal\s*error\s*dekho",
            r"screen\s*pe\s*jo\s*code\s*hai",
            r"code\s*(ko\s*)?explain\s*karo"
        ]
        if any(re.search(pat, cmd_lower) for pat in vision_patterns):
            return True
        vision_keywords = [
            "screen dekho", "screen pe kya hai", "what is on screen", "what is on my screen",
            "look at screen", "check screen", "ye error kya hai", "is error ko dekho",
            "explain error", "error dekho", "explain screen", "screen reader"
        ]
        return any(kw in cmd_lower for kw in vision_keywords)

    def handle_datetime_query(self, command: str, request_id: str = None):
        from datetime import datetime
        now = datetime.now()
        cmd_lower = command.lower().strip()

        if any(kw in cmd_lower for kw in ["time", "kitne baje", "baje hain", "baje hai", "what time is it"]):
            time_str = now.strftime("%I:%M %p").lstrip("0")
            self._speak(f"It's {time_str}, Boss.", request_id=request_id)
        elif any(kw in cmd_lower for kw in ["year", "saal", "what year", "current year"]):
            year_str = str(now.year)
            self._speak(f"We are in the year {year_str}, Boss.", request_id=request_id)
        elif any(kw in cmd_lower for kw in ["day", "din", "what day", "today's day"]):
            day_str = now.strftime("%A")
            self._speak(f"Today is {day_str}, Boss.", request_id=request_id)
        else:
            date_str = now.strftime("%B %d, %Y")
            self._speak(f"Today is {date_str}, Boss.", request_id=request_id)

    def process_user_input(self, text: str, source: str = "voice", request_id: str = None) -> str:
        """
        Unified input handler for both voice/STT and ChatPanel commands.
        Logs telemetry source metadata, normalizes text, strips optional wake word prefix for chat,
        and delegates to route_command with source parameter.
        """
        if not text or not text.strip() or text == "None":
            return ""

        raw_text = text.strip()
        print(f"[INPUT] source={source} text=\"{raw_text}\"", flush=True)

        if source == "chat":
            print(f"[CHAT_INPUT] status=RECEIVED text=\"{raw_text}\"", flush=True)
            print(f"[CHAT_INPUT] status=PROCESSING text=\"{raw_text}\"", flush=True)

        cleaned_text = raw_text
        if source == "chat" and cleaned_text.lower().startswith("jarvis"):
            stripped = re.sub(r"(?i)^jarvis[,:]?\s*", "", cleaned_text).strip()
            if stripped:
                cleaned_text = stripped

        try:
            self.route_command(cleaned_text, source=source, request_id=request_id)
            if source == "chat":
                print(f"[CHAT_INPUT] status=COMPLETED text=\"{raw_text}\"", flush=True)
        except Exception as ex:
            if source == "chat":
                print(f"[CHAT_INPUT] status=FAILED error=\"{ex}\"", flush=True)
            raise ex

        return cleaned_text

    def route_command(self, query: str, source: str = "voice", sync_execution: bool = False, request_id: str = None):
        """Processes and routes user commands with deterministic priority and telemetry."""
        if not query or query.strip() == "" or query == "None":
            return

        command = query.strip()
        command_lower = command.lower()
        import uuid
        request_id = request_id or f"req_{uuid.uuid4().hex[:8]}"

        try:
            print(f"[CONVERSATION_REQUEST] request_id={request_id} query=\"{command}\"", flush=True)
            print(f"[APP_ROUTER] input_source={source} text=\"{command}\"", flush=True)
            logger.info(f"[APP_ROUTER] input_source={source} text=\"{command}\"")
        except Exception:
            pass

        from speech.voice_session_manager import VoiceSessionManager
        from speech.voice_config import VoiceConfig
        # Pass the original request_id into start_session so VSM uses it — do NOT overwrite it.
        # VoiceSessionManager.start_session() already stores the passed request_id on the session.
        vsession = VoiceSessionManager.get_instance().start_session(user_request=command, source=source, request_id=request_id)
        # Preserve original request_id; only fall back to session's if none was provided
        if not request_id:
            request_id = vsession.request_id

        # Priority 0A: Explicit Task Cancellation Interception ("Stop this task", "Cancel task")
        if any(phrase in command_lower for phrase in VoiceConfig.EXPLICIT_CANCEL_TASK_PHRASES):
            try:
                from agent.agent_orchestrator import AgentOrchestrator
                AgentOrchestrator.get_instance().request_cancellation()
            except Exception:
                pass
            if self.speech_coordinator:
                self.speech_coordinator.interrupt_speech(reason="user_cancel_task", request_id=request_id)
            self._speak("Boss, active task cancel kar diya gaya hai.", request_id=request_id)
            return

        # Priority 0B: Explicit Stop Speech Only Interception ("Stop", "Ruko", "Chup", "Stop talking")
        if command_lower in VoiceConfig.EXPLICIT_STOP_PHRASES or any(command_lower.startswith(p + " ") for p in VoiceConfig.EXPLICIT_STOP_PHRASES):
            print(f"[STOP_SPEECH_TRIGGERED] query=\"{command}\"", flush=True)
            if self.speech_coordinator:
                self.speech_coordinator.interrupt_speech(reason="user_stop_speaking", request_id=request_id)
            return

        # Priority 0C: Pending Safety Confirmation Interception
        from tools.email.email_confirmation import EmailConfirmationManager
        from tools.whatsapp.whatsapp_confirmation import WhatsAppConfirmationManager
        from tools.computer.confirmation_manager import ConfirmationManager

        conf_mgr = ConfirmationManager.get_instance()
        is_response_term = conf_mgr.is_affirmative_response(command) or conf_mgr.is_negative_response(command)

        email_conf = EmailConfirmationManager.get_instance()
        if email_conf.has_pending_confirmation():
            if is_response_term:
                from tools.email.email_service import EmailService
                msg = EmailService.get_instance().execute_confirmed_action(command)
                self._speak(msg, request_id=request_id)
                return
            else:
                email_conf.clear()

        wa_conf = WhatsAppConfirmationManager.get_instance()
        if wa_conf.has_pending_confirmation():
            if is_response_term:
                from tools.whatsapp.whatsapp_service import WhatsAppService
                msg = WhatsAppService.get_instance().execute_confirmed_action(command)
                self._speak(msg, request_id=request_id)
                return
            else:
                wa_conf.clear()

        if conf_mgr.has_pending_confirmation():
            if is_response_term:
                from tools.computer.desktop_automation_engine import DesktopAutomationEngine
                success, msg = DesktopAutomationEngine.execute_command(command)
                self._speak(msg, request_id=request_id)
                return
            else:
                conf_mgr.clear()

        from core.performance_profiler import PerformanceProfiler
        PerformanceProfiler.start_request(request_id)
        PerformanceProfiler.mark("ROUTING_START")

        from tools.app_builder.app_intent_router import AppIntentRouter
        from tools.app_builder.app_manager import AppManager
        from tools.app_builder.app_model import AppState
        from tools.app_builder.app_brief_merger import AppBriefMerger

        app_mgr = AppManager()
        active_app = app_mgr.get_active_app()
        is_app_active_busy = (active_app and active_app.status not in [AppState.COMPLETED, AppState.FAILED, AppState.CANCELLED])

        # Priority 1: Active App Approval & Brief Collection Interception
        if active_app and active_app.status in [AppState.WAITING_FOR_APPROVAL, AppState.BRIEF_READY]:
            print(f"[APP_STATE]\napp_id={active_app.app_id}\nstate=WAITING_FOR_APPROVAL", flush=True)
            logger.info(f"[APP_STATE] app_id={active_app.app_id} state=WAITING_FOR_APPROVAL")

            approval_terms = [
                "yes", "start", "start development", "haan", "haan start karo",
                "proceed", "continue", "build it", "approve", "ok", "okay",
                "sure", "banao", "do it", "make it", "build", "haan start",
                "app build karo", "start building", "start app build"
            ]

            is_approval = any(
                command_lower == term or
                command_lower.startswith(f"{term} ") or
                command_lower.endswith(f" {term}") or
                f" {term} " in command_lower
                for term in approval_terms
            )

            if is_approval:
                print(f"[APP_RUNTIME] stage=APPROVAL_RECEIVED status=APPROVED", flush=True)
                print(f"[APP_RUNTIME] stage=IMPLEMENTATION_STARTING", flush=True)
                print(f"[APP_STATE]\napp_id={active_app.app_id}\nstate=IMPLEMENTING", flush=True)
                logger.info("[APP_RUNTIME] stage=APPROVAL_RECEIVED status=APPROVED")
                logger.info("[APP_RUNTIME] stage=IMPLEMENTATION_STARTING")
                logger.info(f"[APP_STATE] app_id={active_app.app_id} state=IMPLEMENTING")

                app_mgr.approve_architecture_and_start(active_app.app_id, sync_execution=sync_execution)
                self._speak("Got it Boss. Architecture plan approved. Starting Flutter frontend and Node.js backend development.")
                return

            if any(kw in command_lower for kw in ["no", "cancel", "stop", "mat karo"]):
                app_mgr.update_app_status(active_app.app_id, AppState.CANCELLED)
                self._speak("Boss, app development request cancel kar diya gaya hai.")
                return

        if active_app and active_app.status in [AppState.WAITING_FOR_BRIEF, AppState.BRIEF_COLLECTING]:
            if "website" in command_lower and any(kw in command_lower for kw in ["bana", "create", "build"]):
                app_mgr.create_app_project(name="Website Task", initial_prompt=command, task_type="WEBSITE")
                self._speak("Okay Boss. App complete hone ke baad website build start karunga. Website ka brief chat me de dena.")
                return

            if any(term in command_lower for term in ["start app build", "start development", "app build karo", "start building"]):
                print(f"[APP_ROUTER] state={active_app.status.value} action=START_DEVELOPMENT_TRIGGER", flush=True)
                app_mgr.update_app_status(active_app.app_id, AppState.BRIEF_READY)
                app_mgr.start_app_development(active_app.app_id, sync_execution=sync_execution)
                self._speak("Got it Boss. Main Flutter frontend aur Node.js backend ke saath build start kar raha hoon.")
                return

            # Merge brief information from chat message
            print(f"[APP_ROUTER] state={active_app.status.value} action=APP_BRIEF_CONTINUATION", flush=True)
            logger.info(f"[APP_ROUTER] state={active_app.status.value} action=APP_BRIEF_CONTINUATION")
            updated = app_mgr.update_app_brief(active_app.app_id, new_text=command)
            if updated:
                from tools.app_builder.app_requirements_analyzer import AppRequirementsAnalyzer
                analyzed = AppRequirementsAnalyzer.analyze(updated.brief)
                print(f"[APP_BRIEF] received_full_brief=true", flush=True)
                brief_len = len(getattr(updated.brief, "full_text", "") or command)
                print(f"[APP_BRIEF] app_name={updated.brief.name} domain={analyzed.get('domain')} backend_required={analyzed.get('needs_backend')} brief_length={brief_len} requirements_count={len(updated.brief.features)}", flush=True)
                logger.info(f"[APP_BRIEF] received_full_brief=true app_name={updated.brief.name} domain={analyzed.get('domain')} backend_required={analyzed.get('needs_backend')} brief_length={brief_len} requirements_count={len(updated.brief.features)}")

                is_sufficient, missing_msg = AppBriefMerger.is_brief_sufficient(updated.brief)
                if is_sufficient and len(updated.brief.features) > 0:
                    app_mgr.update_app_status(active_app.app_id, AppState.BRIEF_READY)
                    app_mgr.start_app_development(active_app.app_id, sync_execution=sync_execution)
                    self._speak("Got it Boss. Main Flutter frontend aur Node.js backend ke saath build start kar raha hoon.")
                    return
                else:
                    self._speak("Details note kar li hain, Boss.")
                    return

        # Priority 2: App Build Intent Interception (New Project Request)
        if AppIntentRouter.is_app_build_intent(command):
            print(f"[APP_ROUTER] input_source={source} intent=APP_BUILD reason=explicit_app_creation_request", flush=True)
            logger.info(f"[APP_ROUTER] input_source={source} intent=APP_BUILD reason=explicit_app_creation_request")
            app_proj = app_mgr.create_app_project(initial_prompt=command, task_type="APP")
            if app_proj.status == AppState.QUEUED:
                msg = "Okay Boss. Current app complete hone ke baad new app build start karunga."
            elif app_proj.status in [AppState.BRIEF_READY, AppState.STARTING, AppState.PLANNING]:
                msg = f"Got it Boss. Creating {app_proj.name or 'app'} with Flutter frontend and Node.js backend. Starting architecture plan."
            else:
                msg = "Okay Boss. App ka naam, features, requirements aur design references chat me likh do. Main uske according app banaunga."
            self._speak(msg)
            return

        # Priority 3: Instant System Date & Time Interception
        if self.is_datetime_query(command_lower):
            print(f"[APP_ROUTER] input_source={source} intent=TIME reason=datetime_query", flush=True)
            logger.info(f"[APP_ROUTER] input_source={source} intent=TIME reason=datetime_query")
            self.handle_datetime_query(command, request_id=request_id)
            PerformanceProfiler.mark("DIRECT_COMMAND_EXECUTION_TIME")
            PerformanceProfiler.report()
            return

        # Priority 3B: Vision & Screen Analysis Interception
        if self.is_vision_query(command_lower):
            print(f"[APP_ROUTER] input_source={source} intent=VISION reason=vision_query", flush=True)
            logger.info(f"[APP_ROUTER] input_source={source} intent=VISION reason=vision_query")
            try:
                from vision.visual_reasoning_engine import VisualReasoningEngine
                engine = VisualReasoningEngine()
                res = engine.process_visual_query(command)
                ans = res.get("response", "Screen analysis completed.")
                self._speak(ans, request_id=request_id)
            except Exception as e:
                logger.error(f"[CommandRouter Vision Error]: {e}")
                self._speak("Screen analysis me problem aayi, Boss.", request_id=request_id)
            PerformanceProfiler.mark("DIRECT_COMMAND_EXECUTION_TIME")
            PerformanceProfiler.report()
            return

        # Priority 4: Desktop Computer Automation Engine Guard
        from tools.computer.desktop_automation_engine import DesktopAutomationEngine
        from tools.computer.sleep_control import SleepController
        if DesktopAutomationEngine.is_desktop_command(command):
            print(f"[APP_ROUTER] input_source={source} intent=DESKTOP_AUTOMATION", flush=True)
            is_sleep = SleepController.is_sleep_command(command)
            # Pass request_id so the original ID is preserved through execution → response
            success, response_msg = DesktopAutomationEngine.execute_command(command, request_id=request_id)
            if response_msg:
                self._speak(response_msg, request_id=request_id)
            PerformanceProfiler.mark("DIRECT_COMMAND_EXECUTION_TIME")
            PerformanceProfiler.report()

            if is_sleep:
                try:
                    from conversation.conversation_engine import ConversationEngine
                    engine = ConversationEngine()
                    if engine and hasattr(engine, "sleep_manager"):
                        engine.sleep_manager.go_to_sleep(reason="user_request")
                except Exception:
                    pass
                SleepController.execute_sleep_action()
            return

        # Priority 5: Active Website Brief Session Routing Guard
        from tools.coding.website_session_manager import WebsiteSessionManager
        web_session = WebsiteSessionManager.get_instance()
        if web_session.is_active():
            res_text = web_session.handle_input(command)
            self._speak(res_text)
            return

        # Priority 6: Active Video Editing Session Guard
        from video_editing.video_session_manager import VideoEditingSessionManager
        video_session = VideoEditingSessionManager.get_instance()
        if video_session.is_active():
            res_text = video_session.handle_command(command, self.speech_coordinator)
            if res_text:
                self._speak(res_text)
            return

        # Priority 7: High-Priority Video Intent Interception
        from video_editing.video_intent_router import classify_video_intent, INTENT_GENERAL_CONVERSATION
        v_intent_info = classify_video_intent(command)
        if v_intent_info.get("intent") != INTENT_GENERAL_CONVERSATION:
            res_text = video_session.handle_command(command, self.speech_coordinator)
            if res_text:
                self._speak(res_text)
            return

        # Priority 8: Initial Website Creation Trigger Interception
        assistant_checker = self.get_code_assistant()
        if assistant_checker and assistant_checker.classify_coding_mode(command) == "WEBSITE_BUILD" and not web_session.WEBSITE_GENERATION_STARTED:
            if is_app_active_busy:
                app_mgr.create_app_project(name="Website Task", initial_prompt=command, task_type="WEBSITE")
                self._speak("Okay Boss. App complete hone ke baad website build start karunga. Website ka brief chat me de dena.")
                return
            else:
                init_msg = web_session.start_brief_collection(command)
                self._speak(init_msg)
                return

        # Priority 9: Explicit Memory Commands Interception
        if self.is_memory_command(command_lower):
            self.handle_memory_command(command)
            return

        # Priority 10: Task Status Query Interception
        if self.is_status_query(command_lower):
            if active_app and active_app.status not in [AppState.COMPLETED, AppState.FAILED, AppState.CANCELLED]:
                app_name = active_app.name or "App"
                if active_app.status == AppState.CODING_FRONTEND:
                    self._speak(f"Boss, main {app_name} ka Flutter frontend bana raha hoon.")
                elif active_app.status == AppState.CODING_BACKEND:
                    self._speak(f"Boss, main {app_name} ka Node.js backend bana raha hoon.")
                elif active_app.status == AppState.PLANNING:
                    self._speak(f"Boss, main {app_name} ki architecture planning kar raha hoon.")
                elif active_app.status in [AppState.WAITING_FOR_BRIEF, AppState.BRIEF_COLLECTING]:
                    self._speak(f"Boss, main {app_name} ki requirements aur brief chat se collect kar raha hoon.")
                else:
                    self._speak(f"Boss, {app_name} ki development active hai.")
                return

            from core.task_orchestrator import TaskOrchestrator
            progress_msg = TaskOrchestrator.get_instance().get_natural_progress_summary()
            self._speak(progress_msg)
            return

        # Priority 11: Permanent Hosting Command
        if self.is_hosting_task(command_lower):
            assistant = self.get_code_assistant()
            if assistant:
                res = assistant.deploy_active_website()
                msg = res.get("message") or res.get("error") or "Hosting process completed."
                self._speak(msg)
                return

        # Priority 12: Strict Web Launch Commands (exact phrase match to prevent false positives)
        if re.search(r"^\s*(?:open|launch)\s+google\s*$", command_lower):
            self._speak("Opening Google")
            webbrowser.open("https://google.com")
            return

        if re.search(r"^\s*(?:open|launch)\s+youtube\s*$", command_lower):
            self._speak("Opening YouTube")
            webbrowser.open("https://youtube.com")
            return

        if re.search(r"^\s*(?:open|launch)\s+spotify\s*$", command_lower):
            self._speak("Opening Spotify")
            webbrowser.open("https://spotify.com")
            return

        # 2. Stock Analyzer
        if any(term in command_lower for term in ["stock price", "stock analysis", "share price"]):
            analyzer = self.get_stock_analyzer()
            if analyzer:
                res = analyzer.analyze_query(command)
                self._speak(res)
                return

        # 3. Face Recognition
        if any(term in command_lower for term in ["who am i", "recognize me", "face recognize", "recognize face"]):
            recognizer = self.get_face_recognizer()
            if recognizer:
                res = recognizer.recognize_current_user()
                self._speak(res)
                return

        # 4. Code Assistant & Website Builder
        if self.is_coding_task(command_lower):
            assistant = self.get_code_assistant()
            if assistant:
                if self.is_unattended_request(command_lower):
                    self._speak("Okay Boss, aap ghoom ke aao. Main tab tak website build kar deta hoon. Wapas aoge tab preview ready milega.")
                else:
                    self._speak("Sure Boss, working on the coding task.")
                res = assistant.generate_code(command)

                if isinstance(res, tuple) and len(res) == 3:
                    code, path, status = res
                elif isinstance(res, tuple) and len(res) == 2:
                    code, path = res
                    status = "SUCCESS" if path else "FAILED"
                else:
                    code, path, status = str(res), "", "FAILED"

                if status == "SUCCESS" and path:
                    self._speak(f"Coding task finished successfully. Saved to {path}")
                elif status == "HALTED_RESEARCH_REQUIRED":
                    self._speak("Boss, I couldn't verify enough official information for this company. Please provide the official website or company details.")
                elif status == "HALTED_AMBIGUOUS_COMPANY":
                    self._speak("Boss, multiple official companies match this name. Please provide the official website URL.")
                elif status == "FAILED":
                    self._speak(f"Boss, website generation failed. I found an error: {code[:100]}")
                return

        # Priority 13: Lightweight Conversational Fast Path or AgentOrchestrator
        try:
            from agent.task_planner import TaskPlanner
            from agent.task_model import TaskType
            planner = TaskPlanner()
            task_type, _ = planner._classify_task(command)

            if task_type == TaskType.CONVERSATIONAL:
                print(f"[FAST_PATH_CONVERSATIONAL] request_id={request_id} source={source} query=\"{command[:40]}\"", flush=True)
                from ai.ask_ollama import ask_ollama_streaming
                eff_coordinator = self.speech_coordinator if source == "voice" else None
                ask_ollama_streaming(
                    command,
                    speaker_name="Boss",
                    relation="boss",
                    speak_callback=self._on_ollama_chunk,
                    speech_coordinator=eff_coordinator,
                    request_id=request_id
                )
                return
        except Exception as e:
            print(f"[CommandRouter Fast Path Check Error]: {e}", flush=True)

        try:
            from agent.agent_orchestrator import AgentOrchestrator
            agent_result = AgentOrchestrator.get_instance().orchestrate(
                command,
                source=source,
                request_id=request_id
            )
            # If Orchestrator handled with a conversational string result, speak it (except for conversation_agent which streams dynamically)
            if agent_result and agent_result.result and isinstance(agent_result.result, str):
                if agent_result.agent_id != "conversation_agent":
                    self._speak(agent_result.result, request_id=request_id)
        except Exception as e:
            print(f"[CommandRouter Orchestrator Fallback Error]: {e}", flush=True)
            try:
                from ai.ask_ollama import ask_ollama_streaming
                eff_coordinator = self.speech_coordinator if source == "voice" else None
                ask_ollama_streaming(
                    command,
                    speaker_name="Boss",
                    relation="boss",
                    speak_callback=self._on_ollama_chunk,
                    speech_coordinator=eff_coordinator,
                    request_id=request_id
                )
            except Exception as ex:
                self._speak("I understood your query, but encountered an issue processing it.")

def route_command(query: str, source: str = "voice", sync_execution: bool = False, request_id: str = None):
    """Module-level entry point function for routing commands."""
    router = CommandRouter()
    return router.route_command(query, source=source, sync_execution=sync_execution, request_id=request_id)

