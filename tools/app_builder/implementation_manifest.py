"""
tools/app_builder/implementation_manifest.py
Phase 4 — Implementation Manifest & Increment Manager.
Manages `implementation_manifest.json` for file-by-file code generation,
tracking operations (CREATE/MODIFY/KEEP/DELETE), status (PENDING, GENERATING, CREATED, VALIDATED, FAILED),
and enabling crash recovery and resumption.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ImplementationManifest")


class ManifestFileItem:
    """
    Represents a single file entry in implementation_manifest.json.
    """
    def __init__(
        self,
        path: str,
        platform: str,
        purpose: str = "",
        operation: str = "CREATE",
        dependencies: Optional[List[str]] = None,
        generated_by: str = "AppCodingAgent",
        status: str = "PENDING",
        error: Optional[str] = None
    ):
        self.path = path
        self.platform = platform
        self.purpose = purpose
        self.operation = operation
        self.dependencies = dependencies or []
        self.generated_by = generated_by
        self.status = status
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "platform": self.platform,
            "purpose": self.purpose,
            "operation": self.operation,
            "dependencies": self.dependencies,
            "generated_by": self.generated_by,
            "status": self.status,
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ManifestFileItem":
        return cls(
            path=data.get("path", ""),
            platform=data.get("platform", "Flutter"),
            purpose=data.get("purpose", ""),
            operation=data.get("operation", "CREATE"),
            dependencies=data.get("dependencies", []),
            generated_by=data.get("generated_by", "AppCodingAgent"),
            status=data.get("status", "PENDING"),
            error=data.get("error")
        )


class ImplementationManifest:
    """
    Manages building, saving, loading, and updating implementation_manifest.json.
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = os.path.abspath(workspace_path)
        self.manifest_file = os.path.join(self.workspace_path, "implementation_manifest.json")
        self.files: List[ManifestFileItem] = []
        self.metadata: Dict[str, Any] = {}

    def build_from_architecture_plan(self, arch_plan: Dict[str, Any]) -> List[ManifestFileItem]:
        """
        Derives target file list from Phase 3 ArchitecturePlan (screens, models, node routes, controllers, etc.).
        Inspects existing files in workspace to assign operation (CREATE vs MODIFY vs KEEP).
        """
        domain = arch_plan.get("app_metadata", {}).get("domain", "item")
        needs_backend = arch_plan.get("app_metadata", {}).get("needs_backend", True)

        items: List[ManifestFileItem] = []

        # 1. Node.js Files
        if needs_backend:
            node_files = [
                ("backend/package.json", "Node", "Backend dependency manifest & npm scripts", ["express", "cors"]),
                ("backend/src/server.js", "Node", "Backend Express server bootstrap & HTTP entry point", ["app.js"]),
                ("backend/src/app.js", "Node", "Express app configuration, CORS, routes & error middleware", ["routes"]),
                (f"backend/src/routes/{domain}Routes.js", "Node", f"Express API routes for {domain}", [f"{domain}Controller.js"]),
                (f"backend/src/routes/authRoutes.js", "Node", "Express authentication routes", ["authController.js"]),
                (f"backend/src/controllers/{domain}Controller.js", "Node", f"Controller logic for {domain}", [f"{domain}Service.js"]),
                ("backend/src/controllers/authController.js", "Node", "User authentication controller logic", ["authService"]),
                (f"backend/src/models/{domain}Model.js", "Node", f"Data store layer for {domain} records", []),
                ("backend/src/middleware/errorHandler.js", "Node", "Centralized Express error handling middleware", []),
                ("backend/tests/server.test.js", "Node", "Backend API endpoint test suite", ["server.js"])
            ]
            for path, platform, purpose, deps in node_files:
                abs_p = os.path.join(self.workspace_path, path)
                op = "MODIFY" if os.path.exists(abs_p) else "CREATE"
                items.append(ManifestFileItem(path=path, platform=platform, purpose=purpose, operation=op, dependencies=deps))

        # 2. Flutter Files
        screens = arch_plan.get("screens", [])
        flutter_files = [
            ("frontend/pubspec.yaml", "Flutter", "Flutter package dependencies & asset configuration", []),
            ("frontend/lib/main.dart", "Flutter", "Application root entry point & Material app runner", ["app_theme.dart", "splash_screen.dart"]),
            ("frontend/lib/theme/app_theme.dart", "Flutter", "Material3 dark/light theme definitions", []),
            ("frontend/lib/models/user_model.dart", "Flutter", "User data model & JSON serialization", []),
            (f"frontend/lib/models/{domain}_item_model.dart", "Flutter", f"{domain.capitalize()} item model & JSON serialization", []),
            ("frontend/lib/services/api_service.dart", "Flutter", "REST HTTP API client matching shared API contract", ["user_model.dart", f"{domain}_item_model.dart"]),
            ("frontend/lib/widgets/custom_widgets.dart", "Flutter", "Reusable UI widgets (CustomCard, PrimaryButton, StatusChip)", ["app_theme.dart"])
        ]

        for s in screens:
            s_name = s.get("name", "Screen")
            s_id = s.get("id") or s_name.lower()
            s_file = s.get("file") or f"lib/screens/{s_id}.dart"
            if not s_file.startswith("frontend/"):
                s_file = f"frontend/{s_file}"
            flutter_files.append((s_file, "Flutter", f"Screen component for {s_name}", ["custom_widgets.dart", "api_service.dart"]))

        for path, platform, purpose, deps in flutter_files:
            # Avoid duplicate paths
            if not any(it.path == path for it in items):
                abs_p = os.path.join(self.workspace_path, path)
                op = "MODIFY" if os.path.exists(abs_p) else "CREATE"
                items.append(ManifestFileItem(path=path, platform=platform, purpose=purpose, operation=op, dependencies=deps))

        self.files = items
        self.metadata = {
            "app_id": arch_plan.get("app_id", ""),
            "domain": domain,
            "total_files": len(items),
            "architecture_hash": arch_plan.get("architecture_hash", "")
        }

        self.save_manifest()
        logger.info(f"Built implementation manifest for '{self.workspace_path}' ({len(items)} files planned)")
        return items

    def save_manifest(self):
        """Saves manifest items to implementation_manifest.json."""
        payload = {
            "metadata": self.metadata,
            "files": [f.to_dict() for f in self.files]
        }
        try:
            os.makedirs(self.workspace_path, exist_ok=True)
            with open(self.manifest_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as ex:
            logger.error(f"Failed to save manifest file: {ex}")

    def load_manifest(self) -> bool:
        """Loads implementation_manifest.json if file exists."""
        if not os.path.exists(self.manifest_file):
            return False
        try:
            with open(self.manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.metadata = data.get("metadata", {})
            self.files = [ManifestFileItem.from_dict(it) for it in data.get("files", [])]
            logger.info(f"Loaded existing manifest from '{self.manifest_file}' ({len(self.files)} items)")
            return True
        except Exception as ex:
            logger.error(f"Failed to load manifest file: {ex}")
            return False

    def update_file_status(self, path: str, status: str, error: Optional[str] = None):
        """Updates status of target file and saves manifest."""
        for item in self.files:
            if item.path == path or item.path.replace("\\", "/") == path.replace("\\", "/"):
                item.status = status
                if error is not None:
                    item.error = error
                break
        self.save_manifest()

    def get_pending_files(self) -> List[ManifestFileItem]:
        """Returns list of files needing generation/validation (PENDING or FAILED)."""
        return [f for f in self.files if f.status in ["PENDING", "FAILED", "GENERATING"]]

    def get_first_unvalidated_index(self) -> int:
        """Returns index of the first incomplete/failed file for resume support."""
        for idx, item in enumerate(self.files):
            if item.status not in ["VALIDATED", "SKIPPED"]:
                return idx
        return len(self.files)

    def is_fully_validated(self) -> bool:
        return all(f.status in ["VALIDATED", "SKIPPED"] for f in self.files)
