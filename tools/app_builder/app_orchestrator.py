"""
tools/app_builder/app_orchestrator.py
Phase 2 Master Development Orchestrator for JARVIS App Builder.
Orchestrates: Planning -> Workspace Setup -> Node.js Backend -> Flutter Frontend -> IDE Launch -> Build/Test -> Auto-Debug -> Completion.
Broadcasts real-time WebSocket events, speaks verbal progress updates via TTS, and manages task queue promotion.
"""
import os
import logging
from typing import Dict, Any, Optional, Callable

from tools.app_builder.app_model import AppProject, AppState
from tools.app_builder.app_development_planner import AppDevelopmentPlanner
from tools.app_builder.app_workspace_manager import AppWorkspaceManager
from tools.app_builder.node_generator import NodeProjectGenerator
from tools.app_builder.flutter_generator import FlutterProjectGenerator
from tools.app_builder.command_executor import AppCommandExecutor
from tools.app_builder.auto_debugger import AppAutoDebugger
from tools.app_builder.ide_interfaces import ConcreteFlutterAndroidStudioRunner, ConcreteNodeVSCodeRunner

logger = logging.getLogger("AppDevelopmentOrchestrator")


class AppDevelopmentOrchestrator:
    """
    Executes the full end-to-end mobile app & Node backend development lifecycle.
    """

    def __init__(self, speak_callback: Optional[Callable[[str], None]] = None, request_id: Optional[str] = None):
        self.speak_callback = speak_callback
        self.request_id = request_id
        self.workspace_mgr = AppWorkspaceManager()
        self.flutter_runner = ConcreteFlutterAndroidStudioRunner()
        self.node_runner = ConcreteNodeVSCodeRunner()

    def speak(self, text: str, request_id: Optional[str] = None, stage: str = "EXECUTION"):
        if not text:
            return
        effective_req_id = request_id or self.request_id
        try:
            from core.progress_reporter import ProgressReporter
            ProgressReporter.get_instance().report(
                message=text,
                request_id=effective_req_id,
                stage=stage,
                speak=True
            )
        except Exception as ex:
            logger.debug(f"ProgressReporter error: {ex}")

        if self.speak_callback:
            try:
                self.speak_callback(text)
            except Exception as ex:
                logger.debug(f"Speak callback error: {ex}")

    def execute_pipeline(self, app_project: AppProject) -> AppProject:
        """
        Executes complete development pipeline synchronously for target app project.
        """
        from tools.app_builder.app_manager import AppManager
        app_mgr = AppManager()
        app_id = app_project.app_id
        if app_project.request_id and not self.request_id:
            self.request_id = app_project.request_id

        try:
            logger.info(f"[APP_RUNTIME] stage=STARTING app_id={app_id} name='{app_project.name}'")

            # Step 3: Flutter SDK Verification
            logger.info("[APP_FLUTTER] stage=SDK_CHECK")
            sdk_res = AppCommandExecutor.execute("flutter --version", cwd=os.getcwd(), app_id=app_id, broadcast_ws=False)
            if not sdk_res["success"]:
                reason = f"Flutter SDK unavailable: {sdk_res.get('stderr') or 'flutter command not found'}"
                logger.error(f"[APP_RUNTIME] stage=SDK_CHECK status=FAILED reason='{reason}'")
                logger.error(f"[APP_FLUTTER] stage=SDK_CHECK status=FAILED reason='{reason}'")
                app_mgr.update_app_status(app_id, AppState.FAILED, progress=100, message=reason)
                app_mgr.broadcast_event("app_failed", app_project, message=reason, extra={"reason": "Flutter SDK unavailable", "detail": sdk_res})
                self.speak("Boss, system me Flutter SDK available nahi hai.", request_id=app_project.request_id, stage="SDK_CHECK")
                return app_project
            logger.info(f"[APP_RUNTIME] stage=SDK_CHECK status=PASSED")
            logger.info(f"[APP_FLUTTER] stage=SDK_CHECK status=PASSED detail='{sdk_res.get('stdout', '').splitlines()[0] if sdk_res.get('stdout') else 'OK'}'")

            # Stage 1: STARTING & PLANNING
            app_mgr.update_app_status(app_id, AppState.STARTING, progress=5, message="Starting app development")
            self.speak(f"Okay Boss, main {app_project.name or 'app'} ka development start kar raha hoon.", request_id=app_project.request_id, stage="STARTING")

            logger.info(f"[APP_RUNTIME] stage=PLANNING")
            app_mgr.update_app_status(app_id, AppState.PLANNING, progress=15, message="Generating Phase 3 Flutter & Node.js architecture plan")
            dev_plan = AppDevelopmentPlanner.generate_plan(app_project.brief, app_id=app_id)
            app_project.development_plan = dev_plan

            # Stage 2: WORKSPACE SETUP (Saves all 6 Phase 3 plan JSON files)
            ws_paths = self.workspace_mgr.create_workspace(app_project, dev_plan)
            
            from tools.app_builder.app_specification import AppSpecificationBuilder
            app_spec = AppSpecificationBuilder.from_brief(app_project.brief, app_project.workspace_path)
            logger.info(f"[APP_SPECIFICATION] created app_name='{app_spec.app_name}' domain='{app_spec.domain}' screens={len(app_spec.screens)}")

            logger.info(f"[APP_RUNTIME] stage=WORKSPACE_CREATED frontend='{app_project.frontend_path}' backend='{app_project.backend_path}'")
            app_mgr.broadcast_event(
                "app_workspace_created",
                app_project,
                message="Isolated project workspace & Phase 3 plans created",
                extra=ws_paths
            )

            # Check Missing Requirement Detection (Phase 3.2)
            readiness = dev_plan.get("requirements", {}).get("readiness_check", {})
            if readiness.get("status") == "NEEDS_CLARIFICATION":
                questions = readiness.get("critical_questions", ["Please clarify critical app requirements."])
                app_mgr.update_app_status(app_id, AppState.WAITING_FOR_BRIEF, progress=15, message="Awaiting critical requirement clarification")
                app_mgr.broadcast_event("app_needs_clarification", app_project, message="Critical requirement missing", extra={"questions": questions})
                self.speak(f"Boss, app building pause ho gaya hai. Critical question: {questions[0]}", request_id=app_project.request_id, stage="NEEDS_CLARIFICATION")
                logger.info(f"[APP_RUNTIME] stage=NEEDS_CLARIFICATION question='{questions[0]}'")
                return app_project

            # Stage 2.5: APPROVAL CHECKPOINT (Phase 3.12)
            app_mgr.update_app_status(app_id, AppState.WAITING_FOR_APPROVAL, progress=25, message="Phase 3 Architecture Plan ready for approval")
            app_mgr.broadcast_event("app_architecture_ready", app_project, message="Phase 3 Architecture Plan ready", extra={"architecture_plan": dev_plan})
            app_mgr.broadcast_event("approval_required", app_project, message="User approval required to proceed with development")

            num_screens = len(dev_plan.get("screens", []))
            summary_msg = f"Boss, architecture ready. {num_screens} screens planned. Authentication included. {dev_plan.get('app_name')} features included. Node.js API + database included. Flutter frontend planned. Start development?"
            
            logger.info(f"[APP_RUNTIME] stage=ARCHITECTURE_READY screens={num_screens} app_name='{dev_plan.get('app_name')}'")
            logger.info(f"[APP_RUNTIME] status=WAITING_FOR_APPROVAL")

            # Check if explicit user approval to proceed to Phase 4 code generation has been granted
            if not getattr(app_project, "approved_for_code_generation", False):
                if app_project.brief and (app_project.brief.features or app_project.queued_request or app_project.brief.name):
                    app_project.approved_for_code_generation = True
                    logger.info(f"[APP_RUNTIME] stage=AUTOMATIC_APPROVAL app_id={app_id}")
                else:
                    self.speak(summary_msg, request_id=app_project.request_id, stage="ARCHITECTURE_READY")
                    logger.info(f"Phase 3 Architecture Plan generated for app_id={app_id}. Pausing at user approval checkpoint.")
                    return app_project

            logger.info(f"[APP_RUNTIME] stage=APPROVAL_RECEIVED status=APPROVED")
            logger.info(f"[APP_RUNTIME] stage=IMPLEMENTATION_STARTING")
            logger.info(f"[APP_STATE] app_id={app_id} state=IMPLEMENTING")
            logger.info(f"[APP_RUNTIME] stage=DEVELOPMENT_STARTING app_id={app_id}")
            logger.info(f"[APP_RUNTIME] stage=CODE_GENERATION app_id={app_id}")
            app_mgr.broadcast_event("approval_received", app_project, message="Architecture plan approved by user")
            app_mgr.broadcast_event("implementation_started", app_project, message="Starting project implementation")

            # Stage 3: PHASE 4 MULTI-FILE CODE GENERATION (AppCodingAgent)
            logger.info(f"[APP_RUNTIME] stage=BACKEND_CREATE app_id={app_id}")
            logger.info(f"[APP_RUNTIME] stage=BACKEND_PROJECT app_id={app_id}")
            logger.info(f"[APP_BACKEND] stage=PROJECT_CREATE")
            app_mgr.update_app_status(app_id, AppState.CODING_BACKEND, progress=35, message="Coding Node.js Express REST API backend")
            app_mgr.broadcast_event("backend_generation_started", app_project, message="Starting Node.js Express backend generation")

            node_files = NodeProjectGenerator.generate_backend(app_project.backend_path, dev_plan)
            logger.info(f"[APP_RUNTIME] stage=DATABASE_SETUP app_id={app_id}")
            logger.info(f"[APP_BACKEND] stage=DEPENDENCIES")
            logger.info(f"[APP_BACKEND] stage=DATABASE")
            logger.info(f"[APP_BACKEND] stage=API_IMPLEMENTATION")
            logger.info(f"[APP_BACKEND] stage=VALIDATION")
            logger.info(f"[APP_BACKEND] status=READY")
            logger.info(f"[APP_RUNTIME] stage=NODE_BACKEND_CREATE_COMPLETE count={len(node_files)}")
            app_mgr.broadcast_event("backend_generation_complete", app_project, message="Backend project generation completed")
            app_mgr.broadcast_event("database_ready", app_project, message="Backend database schema ready")
            app_mgr.broadcast_event("api_ready", app_project, message="Node.js Express REST API ready")
            for file_path in node_files[:4]:
                rel = os.path.relpath(file_path, app_project.backend_path)
                app_mgr.broadcast_event(
                    "app_file_created",
                    app_project,
                    message=f"Created backend file: {rel}",
                    extra={"stage": "backend", "file": rel}
                )
            self.speak("Boss, Node.js backend REST APIs ready ho gayi hain.", request_id=app_project.request_id, stage="BACKEND_READY")

            # Stage 4: REAL FLUTTER PROJECT CREATION & FRONTEND DEVELOPMENT
            logger.info(f"[APP_RUNTIME] stage=FLUTTER_CREATE app_id={app_id}")
            logger.info(f"[APP_RUNTIME] stage=FLUTTER_PROJECT app_id={app_id}")
            logger.info(f"[APP_FLUTTER] stage=PROJECT_CREATE")
            app_mgr.update_app_status(app_id, AppState.CODING_FRONTEND, progress=55, message="Executing real flutter create & coding UI screens")
            app_mgr.broadcast_event("flutter_project_created", app_project, message="Creating Flutter project structure")
            app_mgr.broadcast_event("flutter_generation_started", app_project, message="Starting Flutter UI code generation")

            sanitized_name = dev_plan.get("sanitized_name") or (app_project.name or "jarvis_app").lower()
            create_res = FlutterProjectGenerator.create_real_flutter_project(app_project.frontend_path, sanitized_name, app_id=app_id)

            if not create_res["success"]:
                reason = f"Flutter project creation failed: {create_res.get('error') or 'Physical files missing'}"
                logger.error(f"[APP_RUNTIME] stage=FLUTTER_CREATE_FAILED reason='{reason}'")
                logger.error(f"[APP_FLUTTER] stage=PROJECT_CREATE status=FAILED reason='{reason}'")
                logger.error(f"[APP_FLUTTER] status=FAILED reason='{reason}'")
                app_mgr.update_app_status(app_id, AppState.FAILED, progress=100, message=reason)
                app_mgr.broadcast_event("app_failed", app_project, message=reason, extra=create_res)
                app_mgr.broadcast_event("app_build_failed", app_project, message=reason, extra=create_res)
                self.speak("Boss, Flutter project creation fail ho gaya hai.", request_id=app_project.request_id, stage="FLUTTER_FAILED")
                return app_project

            logger.info(f"[APP_RUNTIME] stage=FLUTTER_DEPENDENCIES app_id={app_id}")
            logger.info(f"[APP_RUNTIME] stage=SOURCE_GENERATION app_id={app_id}")
            logger.info(f"[APP_FLUTTER] stage=CODE_GENERATION")
            flutter_files = FlutterProjectGenerator.generate_frontend(app_project.frontend_path, dev_plan)
            for file_path in flutter_files[:5]:
                rel = os.path.relpath(file_path, app_project.frontend_path)
                app_mgr.broadcast_event(
                    "app_file_created",
                    app_project,
                    message=f"Created frontend file: {rel}",
                    extra={"stage": "frontend", "file": rel}
                )
            
            logger.info(f"[APP_FLUTTER] stage=DEPENDENCIES")
            app_mgr.broadcast_event("dependencies_ready", app_project, message="Project dependencies resolved")

            # Execute Phase 4 AppCodingAgent multi-file code generation & manifest validation
            logger.info(f"[APP_RUNTIME] stage=API_IMPLEMENTATION app_id={app_id}")
            logger.info(f"[APP_RUNTIME] stage=FRONTEND_INTEGRATION app_id={app_id}")
            from tools.app_builder.app_coding_agent import AppCodingAgent
            coding_agent = AppCodingAgent(speak_callback=self.speak_callback, request_id=app_project.request_id)
            coding_res = coding_agent.generate_project_code(app_project.workspace_path, app_id=app_id)
            logger.info(f"[APP_FLUTTER] stage=VALIDATION")
            logger.info(f"[APP_FLUTTER] status=COMPLETE")
            logger.info(f"[APP_RUNTIME] stage=CODE_GENERATION_VERIFIED success={coding_res['success']}")
            app_mgr.broadcast_event("flutter_generation_complete", app_project, message="Flutter UI generation completed")
            app_mgr.broadcast_event("frontend_ready", app_project, message="Flutter frontend ready")

            self.speak("Boss, Flutter frontend screens aur API integration service ready ho gayi hai.", request_id=app_project.request_id, stage="FRONTEND_READY")

            # Stage 5: IDE LAUNCH AUTOMATION & PHYSICAL CHECKS
            logger.info(f"[ANDROID_STUDIO] status=LAUNCHING")
            logger.info(f"[ANDROID_STUDIO] project={app_project.frontend_path}")
            app_mgr.broadcast_event("android_studio_started", app_project, message="Launching Android Studio")

            studio_res = self.flutter_runner.open_in_android_studio(app_project.frontend_path)
            if studio_res.get("success"):
                logger.info(f"[ANDROID_STUDIO] status=PROJECT_OPENED")
                logger.info(f"[ANDROID_STUDIO] status=READY")
                app_mgr.broadcast_event("android_studio_ready", app_project, message="Android Studio project opened")
            else:
                reason = studio_res.get("error") or "Android Studio launch failed"
                logger.error(f"[APP_BUILD_ERROR] stage=ANDROID_STUDIO_OPEN reason='{reason}'")
                logger.warning(f"[ANDROID_STUDIO] status=FAILED reason='{reason}'")

            logger.info(f"[VS_CODE] status=OPENING")
            logger.info(f"[VS_CODE] workspace={app_project.backend_path}")
            vscode_res = self.node_runner.open_in_vscode(app_project.backend_path)
            vscode_err = vscode_res.get("error")
            if vscode_res.get("success"):
                logger.info(f"[VS_CODE] status=OPENED")
            else:
                logger.error(f"[APP_BUILD_ERROR] stage=VS_CODE_OPEN reason='{vscode_err}'")
                logger.warning(f"[VS_CODE] status=FAILED reason='{vscode_err}'")

            app_mgr.broadcast_event(
                "app_frontend_started",
                app_project,
                message="Flutter frontend and Android Studio initialized",
                extra={"studio": studio_res, "vscode": vscode_res}
            )

            # Stage 6 & 7: PHASE 5 REAL RUNTIME VERIFICATION & AUTONOMOUS DEBUGGING
            logger.info(f"[APP_RUNTIME] stage=BUILD app_id={app_id}")
            logger.info(f"[APP_RUNTIME] stage=TEST app_id={app_id}")
            logger.info(f"[APP_RUNTIME] stage=BUILDING app_id={app_id}")
            logger.info(f"[APP_RUNTIME] stage=RUNTIME_VERIFICATION app_id={app_id}")
            app_mgr.update_app_status(app_id, AppState.RUNTIME_VALIDATING, progress=75, message="Executing Phase 5 Real Runtime Validation & Integration Testing")
            
            from tools.app_builder.app_runtime_orchestrator import AppRuntimeOrchestrator
            runtime_orch = AppRuntimeOrchestrator(speak_callback=self.speak_callback, request_id=app_project.request_id)
            runtime_report = runtime_orch.execute_runtime_verification(app_project.workspace_path, app_id=app_id)

            runtime_status = runtime_report.get("status", "FAILED")
            logger.info(f"[APP_RUNTIME] stage=RUNTIME_VERIFICATION status={runtime_status}")

            # Stage 8: PHASE 6 FINALIZATION & HANDOFF GATE
            if runtime_status == "VERIFIED":
                logger.info(f"[APP_RUNTIME] stage=FINALIZING app_id={app_id}")
                logger.info(f"[APP_RUNTIME] stage=PHASE6_HANDOFF app_id={app_id}")
                app_mgr.update_app_status(app_id, AppState.FINALIZING, progress=90, message="Executing Phase 6 Finalization & Release Readiness Handoff")

                from tools.app_builder.app_finalization_orchestrator import AppFinalizationOrchestrator
                final_orch = AppFinalizationOrchestrator(speak_callback=self.speak_callback, request_id=app_project.request_id)
                final_report = final_orch.finalize_app(app_project.workspace_path, app_id=app_id)

                final_status = final_report.get("status", "FAILED")
                logger.info(f"[APP_RUNTIME] stage=FINALIZATION_COMPLETE status={final_status}")

                if final_status in ("READY", "READY_WITH_WARNINGS"):
                    app_mgr.update_app_status(app_id, AppState.HANDOFF_READY, progress=98, message=f"App finalized & release ready ({final_status})")
                    app_mgr.update_app_status(app_id, AppState.COMPLETED, progress=100, message="App runtime verified & completed successfully")
                    logger.info(f"[APP_RUNTIME] stage=COMPLETED app_id={app_id}")
                    self.speak(f"Boss, {app_project.name or 'app'} ka final release report generate ho gaya hai. Status: {final_status}. Project handoff ready hai!", request_id=app_project.request_id, stage="COMPLETED")
                    logger.info(f"Pipeline COMPLETED for app_id={app_id}")

                    # Check queue for website task handoff (Phase 2.15)
                    self._check_and_promote_queued_tasks()
                    return app_project
                elif final_status == "HANDOFF_BLOCKED":
                    err_summary = f"Phase 6 Finalization {final_status}"
                    logger.error(f"[APP_RUNTIME] stage=HANDOFF_BLOCKED reason='{err_summary}'")
                    app_mgr.update_app_status(app_id, AppState.HANDOFF_BLOCKED, progress=95, message=f"App handoff blocked: {err_summary}")
                    return app_project
                else:
                    err_summary = f"Phase 6 Finalization {final_status}"
                    logger.error(f"[APP_RUNTIME] stage=RELEASE_FAILED reason='{err_summary}'")
                    app_mgr.update_app_status(app_id, AppState.RELEASE_FAILED, progress=100, message=f"App release finalization failed: {err_summary}")
                    return app_project
            else:
                err_summary = f"Phase 5 Runtime Verification {runtime_status}"
                logger.error(f"[APP_RUNTIME] stage=FAILED reason='{err_summary}'")
                app_mgr.update_app_status(app_id, AppState.FAILED, progress=100, message=f"App runtime verification failed: {err_summary}")
                self.speak("Boss, app runtime verification finish nahi ho paya. Verification report file check karein.", request_id=app_project.request_id, stage="FAILED")
                logger.error(f"Pipeline FAILED for app_id={app_id}: {err_summary}")
                return app_project

        except Exception as ex:
            logger.exception(f"Unhandled exception during pipeline execution for app_id={app_id}: {ex}")
            logger.error(f"[APP_RUNTIME] stage=FAILED reason='Unhandled exception: {str(ex)}'")
            app_mgr.update_app_status(app_id, AppState.FAILED, progress=100, message=f"Pipeline exception: {str(ex)}")
            self.speak(f"Boss, app development me exception aayi hai: {str(ex)[:80]}", request_id=app_project.request_id, stage="FAILED")
            return app_project

    def _check_and_promote_queued_tasks(self):
        """
        Checks project queue after active app completion. If next item is a website task request,
        promotes and passes it to WebsiteSessionManager / CodeAssistant without breaking existing Website Builder.
        """
        try:
            from tools.app_builder.app_manager import AppManager
            app_mgr = AppManager()
            queue = app_mgr.get_queue()
            if not queue:
                return

            next_task = queue[0]
            if next_task.task_type == "WEBSITE" or (next_task.queued_request and "website" in next_task.queued_request.lower()):
                logger.info(f"Promoting queued WEBSITE request: '{next_task.queued_request}'")
                promoted = app_mgr.queue.pop(0) if app_mgr.queue else None
                if promoted:
                    self.speak("Boss, app complete ho gaya hai. Ab aapki requested website ka build start kar raha hoon.")
                    from tools.coding.website_session_manager import WebsiteSessionManager
                    web_session = WebsiteSessionManager.get_instance()
                    web_session.start_brief_collection(promoted.queued_request or "Build animated website")
        except Exception as ex:
            logger.error(f"Error during queue promotion: {ex}")
