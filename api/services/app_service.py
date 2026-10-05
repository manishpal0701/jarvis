"""
api/services/app_service.py
Service layer for App Builder REST API endpoints.
Delegates operations to AppManager singleton.
"""
from typing import Dict, Any, List, Optional
from tools.app_builder.app_manager import AppManager
from tools.app_builder.app_model import AppState


class AppService:
    def __init__(self):
        self.app_manager = AppManager()

    def create_app(
        self,
        name: str = "",
        description: str = "",
        initial_prompt: str = ""
    ) -> Dict[str, Any]:
        app = self.app_manager.create_app_project(
            name=name,
            description=description,
            initial_prompt=initial_prompt
        )
        return app.to_dict()

    def update_brief(
        self,
        app_id: str,
        text: str = "",
        name: Optional[str] = None,
        description: Optional[str] = None,
        features: Optional[List[str]] = None,
        requirements: Optional[List[str]] = None,
        ui_ux: Optional[Dict[str, Any]] = None,
        authentication: Optional[str] = None,
        database: Optional[str] = None,
        apis: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
        references: Optional[List[Dict[str, Any]]] = None,
        images: Optional[List[str]] = None,
        design_preferences: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        raw_payload = {}
        if name is not None:
            raw_payload["name"] = name
        if description is not None:
            raw_payload["description"] = description
        if features is not None:
            raw_payload["features"] = features
        if requirements is not None:
            raw_payload["requirements"] = requirements
        if ui_ux is not None:
            raw_payload["ui_ux"] = ui_ux
        if authentication is not None:
            raw_payload["authentication"] = authentication
        if database is not None:
            raw_payload["database"] = database
        if apis is not None:
            raw_payload["apis"] = apis
        if platforms is not None:
            raw_payload["platforms"] = platforms
        if design_preferences is not None:
            raw_payload["design_preferences"] = design_preferences

        updated = self.app_manager.update_app_brief(
            app_id=app_id,
            new_text=text,
            references=references,
            images=images,
            raw_payload=raw_payload if raw_payload else None
        )
        return updated.to_dict() if updated else None

    def list_apps(self) -> Dict[str, Any]:
        all_apps = self.app_manager.get_all_apps()
        active = self.app_manager.get_active_app()
        queue = [q.to_dict() for q in self.app_manager.get_queue()]

        return {
            "success": True,
            "total": len(all_apps),
            "active_app": active.to_dict() if active else None,
            "queue": queue,
            "apps": all_apps
        }

    def get_app(self, app_id: str) -> Optional[Dict[str, Any]]:
        app = self.app_manager.get_app_by_id(app_id)
        return app.to_dict() if app else None

    def get_status(self, app_id: str) -> Optional[Dict[str, Any]]:
        app = self.app_manager.get_app_by_id(app_id)
        if not app:
            return None
        return {
            "success": True,
            "app_id": app.app_id,
            "name": app.name or app.brief.name or "App",
            "status": app.status.value if isinstance(app.status, AppState) else str(app.status),
            "progress": app.progress,
            "updated_at": app.updated_at
        }

    def queue_app(self, app_id: str) -> Optional[Dict[str, Any]]:
        app = self.app_manager.get_app_by_id(app_id)
        if not app:
            return None
        updated = self.app_manager.update_app_status(app_id, AppState.QUEUED, message="App queued")
        return updated.to_dict() if updated else None

    def start_app(self, app_id: str) -> Optional[Dict[str, Any]]:
        app = self.app_manager.get_app_by_id(app_id)
        if not app:
            return None
        updated = self.app_manager.start_app_development(app_id)
        return updated.to_dict() if updated else None


_app_service_instance = None

def get_app_service() -> AppService:
    global _app_service_instance
    if _app_service_instance is None:
        _app_service_instance = AppService()
    return _app_service_instance
