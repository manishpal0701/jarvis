"""
tools/app_builder/app_manager.py
Thread-safe singleton manager for App Builder projects, brief state management, project queue, and persistence.
"""
import threading
import logging
from typing import Dict, Any, List, Optional

from tools.app_builder.app_model import AppProject, AppBrief, AppState
from tools.app_builder.app_brief_merger import AppBriefMerger
from tools.app_builder.app_workspace_manager import AppWorkspaceManager

logger = logging.getLogger("AppManager")


class AppManager:
    _instance = None
    _lock = threading.RLock()


    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AppManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.active_app: Optional[AppProject] = None
        self.queue: List[AppProject] = []
        self.history: List[AppProject] = []
        self._initialized = True
        self._load_persisted_state()

    def _load_persisted_state(self):
        """Loads state from data/app_builder_projects.json upon initialization."""
        try:
            persisted = AppWorkspaceManager.load_state()
            self.active_app = persisted.get("active_app")
            self.queue = persisted.get("queue", [])
            self.history = persisted.get("history", [])

            if self.active_app and self.active_app.status not in [AppState.COMPLETED, AppState.FAILED, AppState.CANCELLED]:
                logger.info(f"Resetting non-terminal active project app_id={self.active_app.app_id} status={self.active_app.status} on startup")
                self.active_app.status = AppState.FAILED
                self.history.append(self.active_app)
                self.active_app = None
                self._save_persisted_state()
        except Exception as ex:
            logger.error(f"Failed loading persisted state in AppManager: {ex}")

    def _save_persisted_state(self):
        """Persists current state to data/app_builder_projects.json."""
        try:
            AppWorkspaceManager.save_state(self.active_app, self.queue, self.history)
        except Exception as ex:
            logger.error(f"Failed persisting state in AppManager: {ex}")

    def reset(self):
        """Resets the manager state (useful for tests)."""
        with self._lock:
            self.active_app = None
            self.queue.clear()
            self.history.clear()
            self._save_persisted_state()

    def get_active_app(self) -> Optional[AppProject]:
        with self._lock:
            return self.active_app

    def get_queue(self) -> List[AppProject]:
        with self._lock:
            return list(self.queue)

    def get_all_apps(self) -> List[Dict[str, Any]]:
        with self._lock:
            all_apps = []
            if self.active_app:
                all_apps.append(self.active_app.to_dict())
            for app in self.queue:
                all_apps.append(app.to_dict())
            for app in self.history:
                all_apps.append(app.to_dict())
            return all_apps

    def get_app_by_id(self, app_id: str) -> Optional[AppProject]:
        with self._lock:
            if self.active_app and self.active_app.app_id == app_id:
                return self.active_app
            for app in self.queue:
                if app.app_id == app_id:
                    return app
            for app in self.history:
                if app.app_id == app_id:
                    return app
            return None

    def broadcast_event(self, event_type: str, app: AppProject, message: str = "", extra: Optional[Dict[str, Any]] = None):
        """Broadcasts WebSocket event via api.websocket.jarvis.broadcast_sync if available."""
        payload = {
            "type": event_type,
            "app_id": app.app_id,
            "status": app.status.value if isinstance(app.status, AppState) else str(app.status),
            "progress": app.progress,
            "message": message,
            "project": app.to_dict()
        }
        if extra:
            payload.update(extra)

        try:
            from api.websocket.jarvis import broadcast_sync
            broadcast_sync(payload)
        except Exception as ex:
            logger.debug(f"Broadcast notice (WS not active or testing): {ex}")

    def create_app_project(
        self,
        name: str = "",
        description: str = "",
        initial_prompt: str = "",
        task_type: str = "APP",
        request_id: Optional[str] = None
    ) -> AppProject:
        """
        Creates an APP or secondary queued project.
        If no active app exists (or active app is finished/failed/cancelled), sets as active app.
        Otherwise, adds the new app to the project queue.
        """
        with self._lock:
            is_active_busy = (
                self.active_app is not None and
                self.active_app.status not in [AppState.COMPLETED, AppState.FAILED, AppState.CANCELLED]
            )

            if not is_active_busy:
                new_project = AppProject(
                    name=name,
                    description=description,
                    status=AppState.WAITING_FOR_BRIEF,
                    progress=0,
                    task_type=task_type,
                    queued_request=initial_prompt,
                    request_id=request_id
                )
                if initial_prompt and task_type == "APP":
                    AppBriefMerger.merge_brief(new_project.brief, new_text=initial_prompt)
                    if not new_project.name and new_project.brief.name:
                        new_project.name = new_project.brief.name

                    is_sufficient, _ = AppBriefMerger.is_brief_sufficient(new_project.brief)
                    if is_sufficient:
                        new_project.status = AppState.BRIEF_READY
                        new_project.approved_for_code_generation = True
                        self.active_app = new_project
                        self._save_persisted_state()
                        self.broadcast_event("app_project_created", new_project, message="App project created with complete initial brief")
                        self.broadcast_event("app_brief_ready", new_project, message="App brief is complete and ready for development")
                        logger.info(f"Created active APP project app_id={new_project.app_id} status=BRIEF_READY from complete initial brief")
                        self.start_app_development(new_project.app_id, request_id=request_id)
                        return new_project

                self.active_app = new_project
                self._save_persisted_state()
                self.broadcast_event("app_project_created", new_project, message="App project created")
                self.broadcast_event("app_brief_requested", new_project, message="Awaiting app brief from chat")
                logger.info(f"Created active APP project app_id={new_project.app_id} status=WAITING_FOR_BRIEF")
                return new_project
            else:
                queued_project = AppProject(
                    name=name,
                    description=description,
                    status=AppState.QUEUED,
                    progress=0,
                    task_type=task_type,
                    queued_request=initial_prompt,
                    request_id=request_id
                )
                if initial_prompt and task_type == "APP":
                    AppBriefMerger.merge_brief(queued_project.brief, new_text=initial_prompt)
                    if not queued_project.name and queued_project.brief.name:
                        queued_project.name = queued_project.brief.name

                self.queue.append(queued_project)
                self._save_persisted_state()
                self.broadcast_event("app_queued", queued_project, message=f"Task added to queue ({task_type})")
                logger.info(f"Queued secondary task project app_id={queued_project.app_id} status=QUEUED type={task_type}")
                return queued_project

    def update_app_brief(
        self,
        app_id: str,
        new_text: str = "",
        references: Optional[List[Dict[str, Any]]] = None,
        images: Optional[List[str]] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Optional[AppProject]:
        """
        Merges new requirements/references/images into an existing APP project brief.
        If architecture plan already exists, invalidates and updates plan if requirements change.
        """
        with self._lock:
            target_app = self.get_app_by_id(app_id)
            if not target_app:
                return None

            if request_id:
                target_app.request_id = request_id

            AppBriefMerger.merge_brief(
                target_app.brief,
                new_text=new_text,
                references=references,
                images=images,
                raw_payload=raw_payload
            )

            if target_app.brief.name:
                target_app.name = target_app.brief.name
            if target_app.brief.description and not target_app.description:
                target_app.description = target_app.brief.description

            if target_app.status == AppState.WAITING_FOR_BRIEF:
                target_app.status = AppState.BRIEF_COLLECTING

            # Requirement Invalidation Check (Phase 3.14)
            if target_app.development_plan and "architecture_hash" in target_app.development_plan:
                from tools.app_builder.app_requirements_analyzer import AppRequirementsAnalyzer
                from tools.app_builder.architecture_planner import ArchitecturePlanner
                from tools.app_builder.app_development_planner import AppDevelopmentPlanner

                new_analyzed = AppRequirementsAnalyzer.analyze(target_app.brief)
                new_hash = ArchitecturePlanner.compute_architecture_hash(new_analyzed)
                old_hash = target_app.development_plan.get("architecture_hash")

                if new_hash != old_hash:
                    current_brief_ver = target_app.development_plan.get("brief_version", 1) + 1
                    logger.info(f"Requirement change detected for app_id={app_id}. Invalidating old architecture plan (hash {old_hash[:8]} -> {new_hash[:8]}).")
                    new_plan = AppDevelopmentPlanner.generate_plan(target_app.brief, app_id=app_id, brief_version=current_brief_ver)
                    target_app.development_plan = new_plan
                    target_app.approved_for_code_generation = False
                    if target_app.workspace_path:
                        AppWorkspaceManager().save_project_files(target_app)
                    self.broadcast_event("app_plan_invalidated", target_app, message="Architecture plan re-generated due to requirement update")

            target_app.update_timestamp()
            self._save_persisted_state()
            self.broadcast_event("app_brief_updated", target_app, message="App brief updated")
            logger.info(f"Updated brief for app_id={app_id} status={target_app.status.value}")
            return target_app

    def approve_architecture_and_start(self, app_id: str, sync_execution: bool = False, request_id: Optional[str] = None) -> Optional[AppProject]:
        """
        Grants explicit user approval for Phase 3 Architecture Plan and starts Phase 4 development.
        """
        with self._lock:
            target_app = self.get_app_by_id(app_id)
            if not target_app:
                return None

            if request_id:
                target_app.request_id = request_id

            target_app.approved_for_code_generation = True
            logger.info(f"Phase 3 Architecture Plan APPROVED by user for app_id={app_id}")
            self.broadcast_event("app_architecture_approved", target_app, message="Architecture plan approved by user")

        return self.start_app_development(app_id, sync_execution=sync_execution, request_id=request_id)

    def start_app_development(self, app_id: str, sync_execution: bool = False, request_id: Optional[str] = None) -> Optional[AppProject]:
        """
        Initiates app development pipeline for target app.
        Launches pipeline execution asynchronously or synchronously (for tests).
        """
        with self._lock:
            target_app = self.get_app_by_id(app_id)
            if not target_app:
                return None

            if request_id:
                target_app.request_id = request_id

            target_app.status = AppState.STARTING
            target_app.progress = 5
            target_app.update_timestamp()
            self._save_persisted_state()
            self.broadcast_event("app_started", target_app, message="Starting app development")

        req_id = target_app.request_id
        if sync_execution:
            from tools.app_builder.app_orchestrator import AppDevelopmentOrchestrator
            orchestrator = AppDevelopmentOrchestrator(request_id=req_id)
            orchestrator.execute_pipeline(target_app)
        else:
            def _run():
                from tools.app_builder.app_orchestrator import AppDevelopmentOrchestrator
                orchestrator = AppDevelopmentOrchestrator(request_id=req_id)
                orchestrator.execute_pipeline(target_app)

            thread = threading.Thread(target=_run, daemon=True)
            thread.start()

        return target_app

    def update_app_status(
        self,
        app_id: str,
        new_status: AppState,
        progress: Optional[int] = None,
        message: str = ""
    ) -> Optional[AppProject]:
        """
        Updates project status & progress, broadcasting corresponding WS event.
        Handles queue advancement when active app reaches COMPLETED.
        """
        with self._lock:
            target_app = self.get_app_by_id(app_id)
            if not target_app:
                return None

            target_app.status = new_status if isinstance(new_status, AppState) else AppState(new_status)
            if progress is not None:
                target_app.progress = progress
            target_app.update_timestamp()

            event_map = {
                AppState.BRIEF_READY: "app_brief_ready",
                AppState.PLANNING: "app_planning",
                AppState.STARTING: "app_started",
                AppState.CODING_FRONTEND: "app_frontend_started",
                AppState.CODING_BACKEND: "app_backend_started",
                AppState.BUILDING: "app_building",
                AppState.TESTING: "app_testing",
                AppState.DEBUGGING: "app_debugging",
                AppState.COMPLETED: "app_completed",
                AppState.FAILED: "app_failed",
            }
            event_type = event_map.get(target_app.status, "app_progress")
            self.broadcast_event(event_type, target_app, message=message or f"App status updated to {target_app.status.value}")

            # Queue advancement logic on COMPLETED
            if target_app.status == AppState.COMPLETED:
                if self.active_app and self.active_app.app_id == app_id:
                    self.history.append(self.active_app)
                    self.active_app = None

                    # Advance queue if any
                    if self.queue:
                        next_app = self.queue.pop(0)
                        if next_app.task_type == "APP":
                            next_app.status = AppState.WAITING_FOR_BRIEF
                            self.active_app = next_app
                            self.broadcast_event("app_started", next_app, message="Next app from queue is now active")
                            self.broadcast_event("app_brief_requested", next_app, message="Send app brief in chat")
                            logger.info(f"Advanced queue: app_id={next_app.app_id} is now active")

            self._save_persisted_state()
            return target_app
