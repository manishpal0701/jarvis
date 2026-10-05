"""
tools/app_builder/app_workspace_manager.py
Phase 2.2 & Phase 2.19 — Workspace Manager & Persistence Engine for App Builder projects.
Creates isolated project workspaces under `JARVIS App Projects/<Project_Name>_<app_id_short>/`.
Saves project states to `data/app_builder_projects.json` to enable recovery upon restart.
"""
import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from tools.app_builder.app_model import AppProject, AppBrief, AppState

logger = logging.getLogger("AppWorkspaceManager")

DATA_DIR = os.path.join(os.getcwd(), "data")
PROJECTS_PERSISTENCE_FILE = os.path.join(DATA_DIR, "app_builder_projects.json")
DEFAULT_WORKSPACE_ROOT = os.path.join(os.getcwd(), "JARVIS App Projects")


class AppWorkspaceManager:
    """
    Manages isolated project workspaces for JARVIS App Builder projects.
    Structure:
    JARVIS App Projects/
        <Project_Name>_<app_id_short>/
            frontend/
            backend/
            project.json
            development_plan.json
            brief.json
            logs/
            tests/
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or DEFAULT_WORKSPACE_ROOT
        os.makedirs(self.workspace_root, exist_ok=True)
        os.makedirs(DATA_DIR, exist_ok=True)

    @property
    def base_workspace_dir(self) -> str:
        return self.workspace_root

    def create_workspace(self, app_project: AppProject, development_plan: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Creates an isolated directory structure for the app project.
        """
        raw_name = (app_project.name or "AppProject").strip().replace(" ", "_")
        clean_name = "".join(c for c in raw_name if c.isalnum() or c in ("_", "-"))
        clean_name = re.sub(r"_+", "_", clean_name).strip("_")
        if not clean_name:
            clean_name = "AppProject"
        app_id_short = app_project.app_id[:8]
        folder_name = f"{clean_name}_{app_id_short}"

        project_dir = os.path.abspath(os.path.join(self.workspace_root, folder_name))
        frontend_dir = os.path.join(project_dir, "frontend")
        backend_dir = os.path.join(project_dir, "backend")
        logs_dir = os.path.join(project_dir, "logs")
        tests_dir = os.path.join(project_dir, "tests")

        for d in [project_dir, frontend_dir, backend_dir, logs_dir, tests_dir]:
            os.makedirs(d, exist_ok=True)

        app_project.workspace_path = project_dir
        app_project.frontend_path = frontend_dir
        app_project.backend_path = backend_dir
        if development_plan:
            app_project.development_plan = development_plan

        # Write project.json, brief.json, development_plan.json
        self.save_project_files(app_project)

        logger.info(f"Created workspace for app '{app_project.name}' (id={app_project.app_id}) at '{project_dir}'")
        return {
            "workspace_path": project_dir,
            "frontend_path": frontend_dir,
            "backend_path": backend_dir,
            "logs_path": logs_dir,
            "tests_path": tests_dir
        }

    def save_project_files(self, app_project: AppProject):
        """
        Writes project.json, brief.json, architecture_plan.json, flutter_plan.json, node_plan.json,
        api_contract.json, database_plan.json, and development_plan.json into project workspace directory.
        """
        if not app_project.workspace_path or not os.path.exists(app_project.workspace_path):
            return

        plan = app_project.development_plan or {}

        proj_file = os.path.join(app_project.workspace_path, "project.json")
        brief_file = os.path.join(app_project.workspace_path, "brief.json")
        spec_file = os.path.join(app_project.workspace_path, "app_build_spec.json")
        arch_file = os.path.join(app_project.workspace_path, "architecture_plan.json")
        flutter_file = os.path.join(app_project.workspace_path, "flutter_plan.json")
        node_file = os.path.join(app_project.workspace_path, "node_plan.json")
        api_file = os.path.join(app_project.workspace_path, "api_contract.json")
        db_file = os.path.join(app_project.workspace_path, "database_plan.json")
        dev_plan_file = os.path.join(app_project.workspace_path, "development_plan.json")

        try:
            with open(proj_file, "w", encoding="utf-8") as f:
                json.dump(app_project.to_dict(), f, indent=2)

            with open(brief_file, "w", encoding="utf-8") as f:
                json.dump(app_project.brief.to_dict(), f, indent=2)

            with open(spec_file, "w", encoding="utf-8") as f:
                spec_dict = app_project.build_spec.to_dict() if getattr(app_project, "build_spec", None) else (plan.get("build_spec") or {})
                json.dump(spec_dict, f, indent=2)

            with open(arch_file, "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=2)

            with open(flutter_file, "w", encoding="utf-8") as f:
                json.dump(plan.get("flutter_plan") or plan.get("flutter") or {}, f, indent=2)

            with open(node_file, "w", encoding="utf-8") as f:
                json.dump(plan.get("node_plan") or plan.get("node") or {}, f, indent=2)

            with open(api_file, "w", encoding="utf-8") as f:
                json.dump(plan.get("api_contract") or {}, f, indent=2)

            with open(db_file, "w", encoding="utf-8") as f:
                json.dump(plan.get("database_schema") or {}, f, indent=2)

            with open(dev_plan_file, "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=2)

            logger.info(f"Persisted Phase 3 plan files (brief, spec, arch, flutter, node, api, db) in workspace '{app_project.workspace_path}'")
        except Exception as ex:
            logger.error(f"Failed writing workspace project files for {app_project.app_id}: {ex}")

    @staticmethod
    def save_state(active_app: Optional[AppProject], queue: List[AppProject], history: List[AppProject]):
        """
        Persists active_app, queue, and history into data/app_builder_projects.json.
        """
        payload = {
            "active_app": active_app.to_dict() if active_app else None,
            "queue": [q.to_dict() for q in queue],
            "history": [h.to_dict() for h in history]
        }
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            tmp_file = PROJECTS_PERSISTENCE_FILE + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            os.replace(tmp_file, PROJECTS_PERSISTENCE_FILE)
            logger.debug("Successfully persisted AppManager state to app_builder_projects.json")
        except Exception as ex:
            logger.error(f"Failed to persist AppManager state: {ex}")

    @staticmethod
    def load_state() -> Dict[str, Any]:
        """
        Loads persisted state from data/app_builder_projects.json if file exists.
        """
        if not os.path.exists(PROJECTS_PERSISTENCE_FILE):
            return {"active_app": None, "queue": [], "history": []}

        try:
            with open(PROJECTS_PERSISTENCE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            active_app = AppProject.from_dict(data["active_app"]) if data.get("active_app") else None
            queue = [AppProject.from_dict(q) for q in data.get("queue", [])]
            history = [AppProject.from_dict(h) for h in data.get("history", [])]

            logger.info(f"Recovered state from persistence file: active={active_app.app_id if active_app else None}, queue={len(queue)}, history={len(history)}")
            return {
                "active_app": active_app,
                "queue": queue,
                "history": history
            }
        except Exception as ex:
            logger.error(f"Failed to load state from persistence file: {ex}")
            return {"active_app": None, "queue": [], "history": []}
