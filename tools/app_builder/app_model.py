"""
tools/app_builder/app_model.py
Data models and state enums for the App Builder subsystem.
"""
from enum import Enum
import uuid
import datetime
from typing import Dict, Any, List, Optional


class AppState(str, Enum):
    CREATED = "CREATED"
    WAITING_FOR_BRIEF = "WAITING_FOR_BRIEF"
    BRIEF_COLLECTING = "BRIEF_COLLECTING"
    BRIEF_READY = "BRIEF_READY"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    PLANNING = "PLANNING"
    CODE_PLANNED = "CODE_PLANNED"
    QUEUED = "QUEUED"
    STARTING = "STARTING"
    CODING_FRONTEND = "CODING_FRONTEND"
    CODING_BACKEND = "CODING_BACKEND"
    INTEGRATING = "INTEGRATING"
    VALIDATING = "VALIDATING"
    BUILDING = "BUILDING"
    TESTING = "TESTING"
    DEBUGGING = "DEBUGGING"
    CODE_VERIFIED = "CODE_VERIFIED"
    RUNTIME_VALIDATING = "RUNTIME_VALIDATING"
    FLUTTER_BUILDING = "FLUTTER_BUILDING"
    NODE_STARTING = "NODE_STARTING"
    INTEGRATION_TESTING = "INTEGRATION_TESTING"
    ANDROID_BUILDING = "ANDROID_BUILDING"
    ANDROID_RUNNING = "ANDROID_RUNNING"
    RUNTIME_DEBUGGING = "RUNTIME_DEBUGGING"
    RUNTIME_VERIFIED = "RUNTIME_VERIFIED"
    RUNTIME_FAILED = "RUNTIME_FAILED"
    FINALIZING = "FINALIZING"
    FINAL_PROJECT_VERIFYING = "FINAL_PROJECT_VERIFYING"
    ARTIFACT_DISCOVERY = "ARTIFACT_DISCOVERY"
    RELEASE_PREPARING = "RELEASE_PREPARING"
    RELEASE_VALIDATING = "RELEASE_VALIDATING"
    HANDOFF_READY = "HANDOFF_READY"
    HANDOFF_BLOCKED = "HANDOFF_BLOCKED"
    RELEASE_FAILED = "RELEASE_FAILED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class AppBrief:
    def __init__(
        self,
        name: str = "",
        description: str = "",
        full_text: str = "",
        technology: Optional[Dict[str, str]] = None,
        features: Optional[List[str]] = None,
        requirements: Optional[List[str]] = None,
        ui_ux: Optional[Dict[str, Any]] = None,
        authentication: Optional[str] = None,
        database: Optional[str] = None,
        apis: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
        references: Optional[List[Dict[str, Any]]] = None,
        images: Optional[List[str]] = None,
        design_preferences: Optional[List[str]] = None,
        additional_instructions: Optional[List[str]] = None
    ):
        self.name = name
        self.description = description
        self.full_text = full_text or description or ""
        self.technology = technology or {"frontend": "Flutter", "backend": "Node.js"}
        self.features = features or []
        self.requirements = requirements or []
        self.ui_ux = ui_ux or {
            "theme": None,
            "colors": [],
            "fonts": [],
            "animations": []
        }
        self.authentication = authentication
        self.database = database
        self.apis = apis or []
        self.platforms = platforms or ["Android"]
        self.references = references or []
        self.images = images or []
        self.design_preferences = design_preferences or []
        self.additional_instructions = additional_instructions or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "full_text": self.full_text,
            "technology": self.technology,
            "features": self.features,
            "requirements": self.requirements,
            "ui_ux": self.ui_ux,
            "authentication": self.authentication,
            "database": self.database,
            "apis": self.apis,
            "platforms": self.platforms,
            "references": self.references,
            "images": self.images,
            "design_preferences": self.design_preferences,
            "additional_instructions": self.additional_instructions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppBrief":
        if not data:
            return cls()
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            full_text=data.get("full_text") or data.get("description", ""),
            technology=data.get("technology", {"frontend": "Flutter", "backend": "Node.js"}),
            features=data.get("features", []),
            requirements=data.get("requirements", []),
            ui_ux=data.get("ui_ux", {"theme": None, "colors": [], "fonts": [], "animations": []}),
            authentication=data.get("authentication"),
            database=data.get("database"),
            apis=data.get("apis", []),
            platforms=data.get("platforms", ["Android"]),
            references=data.get("references", []),
            images=data.get("images", []),
            design_preferences=data.get("design_preferences", []),
            additional_instructions=data.get("additional_instructions", [])
        )


class AppBuildSpec:
    def __init__(
        self,
        app_id: str = "",
        app_name: str = "",
        domain: str = "item",
        platform: str = "Android",
        frontend_stack: str = "Flutter",
        backend_stack: str = "Node.js + Express",
        database: str = "JSON File Store",
        features: Optional[List[str]] = None,
        screens: Optional[List[Dict[str, Any]]] = None,
        apis: Optional[List[str]] = None,
        design: str = "Dark Theme",
        special_requirements: Optional[List[str]] = None,
        is_locked: bool = True
    ):
        self.app_id = app_id
        self.app_name = app_name
        self.domain = domain
        self.platform = platform
        self.frontend_stack = frontend_stack
        self.backend_stack = backend_stack
        self.database = database
        self.features = features or []
        self.screens = screens or []
        self.apis = apis or []
        self.design = design
        self.special_requirements = special_requirements or []
        self.is_locked = is_locked

    def to_dict(self) -> Dict[str, Any]:
        return {
            "app_id": self.app_id,
            "app_name": self.app_name,
            "domain": self.domain,
            "platform": self.platform,
            "frontend_stack": self.frontend_stack,
            "backend_stack": self.backend_stack,
            "database": self.database,
            "features": self.features,
            "screens": self.screens,
            "apis": self.apis,
            "design": self.design,
            "special_requirements": self.special_requirements,
            "is_locked": self.is_locked
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AppBuildSpec":
        if not data:
            return cls()
        return cls(
            app_id=data.get("app_id", ""),
            app_name=data.get("app_name", ""),
            domain=data.get("domain", "item"),
            platform=data.get("platform", "Android"),
            frontend_stack=data.get("frontend_stack", "Flutter"),
            backend_stack=data.get("backend_stack", "Node.js + Express"),
            database=data.get("database", "JSON File Store"),
            features=data.get("features", []),
            screens=data.get("screens", []),
            apis=data.get("apis", []),
            design=data.get("design", "Dark Theme"),
            special_requirements=data.get("special_requirements", []),
            is_locked=data.get("is_locked", True)
        )


class AppProject:
    def __init__(
        self,
        project_id: Optional[str] = None,
        name: str = "",
        description: str = "",
        status: AppState = AppState.WAITING_FOR_BRIEF,
        progress: int = 0,
        technology: Optional[Dict[str, str]] = None,
        brief: Optional[AppBrief] = None,
        workspace_path: Optional[str] = None,
        frontend_path: Optional[str] = None,
        backend_path: Optional[str] = None,
        development_plan: Optional[Dict[str, Any]] = None,
        build_logs: Optional[List[Dict[str, Any]]] = None,
        task_type: str = "APP",
        queued_request: Optional[str] = None,
        build_spec: Optional[AppBuildSpec] = None,
        request_id: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        self.app_id = project_id or str(uuid.uuid4())
        self.type = task_type or "APP"
        self.name = name
        self.description = description
        self.status = status if isinstance(status, AppState) else AppState(status)
        self.progress = progress
        self.technology = technology or {"frontend": "Flutter", "backend": "Node.js"}
        self.brief = brief or AppBrief(technology=self.technology)
        self.workspace_path = workspace_path
        self.frontend_path = frontend_path
        self.backend_path = backend_path
        self.development_plan = development_plan or {}
        self.build_logs = build_logs or []
        self.task_type = task_type or "APP"
        self.queued_request = queued_request
        self.build_spec = build_spec or AppBuildSpec(app_id=self.app_id, app_name=self.name)
        self.request_id = request_id
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.created_at = created_at or now_str
        self.updated_at = updated_at or now_str

    def update_timestamp(self):
        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        brief_dict = self.brief.to_dict()
        res = {
            "app_id": self.app_id,
            "project_id": self.app_id,
            "type": self.type,
            "task_type": self.task_type,
            "name": self.name or brief_dict.get("name", ""),
            "description": self.description or brief_dict.get("description", ""),
            "technology": self.technology,
            "features": brief_dict.get("features", []),
            "requirements": brief_dict.get("requirements", []),
            "ui_ux": brief_dict.get("ui_ux", {}),
            "authentication": brief_dict.get("authentication"),
            "database": brief_dict.get("database"),
            "apis": brief_dict.get("apis", []),
            "platforms": brief_dict.get("platforms", ["Android"]),
            "references": brief_dict.get("references", []),
            "images": brief_dict.get("images", []),
            "design_preferences": brief_dict.get("design_preferences", []),
            "additional_instructions": brief_dict.get("additional_instructions", []),
            "status": self.status.value if isinstance(self.status, AppState) else str(self.status),
            "progress": self.progress,
            "workspace_path": self.workspace_path,
            "frontend_path": self.frontend_path,
            "backend_path": self.backend_path,
            "development_plan": self.development_plan,
            "build_logs": self.build_logs,
            "queued_request": self.queued_request,
            "brief": brief_dict,
            "build_spec": self.build_spec.to_dict() if self.build_spec else None,
            "request_id": self.request_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppProject":
        brief_data = data.get("brief", data)
        brief_obj = AppBrief.from_dict(brief_data)
        st_val = data.get("status", AppState.WAITING_FOR_BRIEF)
        if isinstance(st_val, str):
            try:
                st_enum = AppState(st_val)
            except ValueError:
                st_enum = AppState.WAITING_FOR_BRIEF
        else:
            st_enum = st_val

        spec_data = data.get("build_spec")
        spec_obj = AppBuildSpec.from_dict(spec_data) if spec_data else None

        return cls(
            project_id=data.get("app_id") or data.get("project_id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            status=st_enum,
            progress=data.get("progress", 0),
            technology=data.get("technology", {"frontend": "Flutter", "backend": "Node.js"}),
            brief=brief_obj,
            workspace_path=data.get("workspace_path"),
            frontend_path=data.get("frontend_path"),
            backend_path=data.get("backend_path"),
            development_plan=data.get("development_plan", {}),
            build_logs=data.get("build_logs", []),
            task_type=data.get("task_type", data.get("type", "APP")),
            queued_request=data.get("queued_request"),
            build_spec=spec_obj,
            request_id=data.get("request_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


