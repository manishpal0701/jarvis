"""
tools/app_builder/architecture_planner.py
Phase 3 — Machine-Readable Architecture Planner & Schema Generator.
Generates deterministic JSON-serializable models for ArchitecturePlan, ScreenPlan, FlutterPlan, NodePlan,
ApiContract, DatabasePlan, UiDesignPlan, DependencyPlan, and ImplementationOrder.
Provides hash computation and plan version invalidation tracking.
"""
import os
import json
import hashlib
import datetime
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ArchitecturePlanner")


class ArchitecturePlanner:
    """
    Generates deterministic, machine-readable architecture plans from analyzed requirements.
    """

    @classmethod
    def create_architecture_plan(
        cls,
        app_id: str,
        analyzed_reqs: Dict[str, Any],
        brief_version: int = 1,
        plan_version: int = 1
    ) -> Dict[str, Any]:
        app_name = analyzed_reqs.get("app_name", "JarvisApp")
        domain = analyzed_reqs.get("domain", "item")
        needs_backend = analyzed_reqs.get("needs_backend", True)

        # 0. Generate ApplicationSpecification
        from tools.app_builder.app_specification import AppSpecificationBuilder
        app_spec = AppSpecificationBuilder.build_specification(brief=None, app_id=app_id, analyzed_dict=analyzed_reqs)
        spec_dict = app_spec.to_dict()

        # 1. Compute Architecture Hash
        arch_hash = cls.compute_architecture_hash(analyzed_reqs)

        # 2. Screen Plans
        screens_plan = cls.generate_screen_plans(app_name, domain, analyzed_reqs.get("core_features", []))

        # 3. Shared API Contract
        api_contract = cls.generate_api_contract(app_name, domain, needs_backend)

        # 4. Database Plan
        database_plan = cls.generate_database_plan(app_name, domain, needs_backend)

        # 5. UI / Design Plan
        ui_design_plan = cls.generate_ui_design_plan(analyzed_reqs.get("ui_design_requirements", {}))

        # 6. Flutter Architecture Plan
        flutter_plan = cls.generate_flutter_plan(app_name, domain, screens_plan, ui_design_plan)

        # 7. Node.js Architecture Plan
        node_plan = cls.generate_node_plan(app_name, domain, api_contract, database_plan, needs_backend)

        # 8. Dependency Plan
        dependency_plan = cls.generate_dependency_plan(needs_backend)

        # 9. Implementation Order
        implementation_order = cls.generate_implementation_order(needs_backend)

        # 10. Assembled Complete ArchitecturePlan
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        architecture_plan = {
            "app_id": app_id,
            "plan_version": plan_version,
            "brief_version": brief_version,
            "created_at": now_str,
            "architecture_hash": arch_hash,
            "application_specification": spec_dict,
            "app_metadata": {
                "app_name": app_name,
                "domain": domain,
                "purpose": analyzed_reqs.get("app_purpose", ""),
                "target_users": analyzed_reqs.get("target_users", []),
                "needs_backend": needs_backend
            },
            "requirements": analyzed_reqs,
            "screens": screens_plan,
            "navigation": {
                "initial_route": "/splash" if needs_backend else "/",
                "routes": [s["route"] for s in screens_plan],
                "type": "MaterialPageRoute Stack"
            },
            "components": [
                {"name": "CustomCard", "type": "StatelessWidget", "file": "lib/widgets/custom_widgets.dart"},
                {"name": "PrimaryButton", "type": "StatelessWidget", "file": "lib/widgets/custom_widgets.dart"},
                {"name": "StatusChip", "type": "StatelessWidget", "file": "lib/widgets/custom_widgets.dart"}
            ],
            "models": flutter_plan["models"],
            "state_management": {
                "type": "Riverpod (flutter_riverpod: ^2.5.1)",
                "architecture": "StateNotifierProvider / NotifierProvider + AsyncValue",
                "providers": [f"{domain.capitalize()}NotifierProvider", "AuthProvider", "ThemeNotifierProvider"]
            },
            "services": [
                {"name": "ApiService", "file": "lib/services/api_service.dart"}
            ] if needs_backend else [],
            "api_contract": api_contract,
            "database_schema": database_plan,
            "authentication": {
                "required": analyzed_reqs.get("authentication_requirements") != "NONE",
                "type": analyzed_reqs.get("authentication_requirements", "JWT Auth")
            },
            "permissions": analyzed_reqs.get("permissions", []),
            "dependencies": dependency_plan,
            "theme": ui_design_plan,
            "error_handling": {
                "frontend": "Global Error Catching UI Banner / SnackBar",
                "backend": "Express Central Error Middleware (`src/middleware/errorHandler.js`)"
            },
            "testing_strategy": {
                "flutter": "Widget & Unit tests via flutter_test",
                "node": "Express route unit tests via Node assert/supertest"
            },
            "build_strategy": {
                "flutter_build": "flutter build apk",
                "node_build": "npm run start"
            },
            "flutter_plan": flutter_plan,
            "node_plan": node_plan,
            "implementation_order": implementation_order
        }

        logger.info(f"Generated complete ArchitecturePlan for app_id={app_id} (hash={arch_hash[:12]})")
        return architecture_plan

    @classmethod
    def compute_architecture_hash(cls, reqs: Dict[str, Any]) -> str:
        """
        Computes SHA-256 hash of canonicalized requirement dict for invalidation tracking.
        """
        raw_str = json.dumps(reqs, sort_keys=True)
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    @classmethod
    def generate_screen_plans(cls, app_name: str, domain: str, core_features: List[str]) -> List[Dict[str, Any]]:
        if domain == "calculator":
            return [
                {
                    "id": "calculator_screen",
                    "name": "CalculatorScreen",
                    "purpose": "Primary math calculator interface",
                    "route": "/",
                    "ui_components": ["DisplayWindow", "KeypadGrid", "OperatorButton"],
                    "input_fields": [{"name": "keypad_input", "type": "button_press"}],
                    "validation": ["Division by zero guard", "Expression syntax check"],
                    "api_calls": [],
                    "state_required": ["current_expression", "display_value", "history"],
                    "loading_state": "None",
                    "empty_state": "Display shows '0'",
                    "error_state": "Display shows 'Error'",
                    "success_state": "Result rendered",
                    "navigation_targets": []
                }
            ]

        return [
            {
                "id": "splash_screen",
                "name": "SplashScreen",
                "purpose": "App branding & auth state check",
                "route": "/splash",
                "ui_components": ["BrandingLogo", "LoadingSpinner"],
                "input_fields": [],
                "validation": [],
                "api_calls": ["GET /api/health"],
                "state_required": ["is_authenticated"],
                "loading_state": "Animated Spinner",
                "empty_state": "N/A",
                "error_state": "Backend Offline Notice",
                "success_state": "Navigate to Dashboard or Login",
                "navigation_targets": ["/login", "/dashboard"]
            },
            {
                "id": "login_screen",
                "name": "LoginScreen",
                "purpose": "User login & credentials authentication",
                "route": "/login",
                "ui_components": ["AuthHeader", "InputField", "PrimaryButton"],
                "input_fields": [{"name": "email", "type": "email"}, {"name": "password", "type": "password"}],
                "validation": ["Email required", "Password min length 6"],
                "api_calls": ["POST /api/auth/login"],
                "state_required": ["is_submitting", "error_message"],
                "loading_state": "Button Progress Indicator",
                "empty_state": "Form inputs ready",
                "error_state": "Invalid Credentials Alert",
                "success_state": "Navigate to /dashboard",
                "navigation_targets": ["/dashboard"]
            },
            {
                "id": "dashboard_screen",
                "name": "DashboardScreen",
                "purpose": f"Overview summary metrics for {app_name}",
                "route": "/dashboard",
                "ui_components": ["SummaryCard", "ActivityList", "QuickActionButton"],
                "input_fields": [],
                "validation": [],
                "api_calls": [f"GET /api/{domain}s"],
                "state_required": [f"{domain}_items_list", "is_loading"],
                "loading_state": "Shimmer / Centered CircularProgressIndicator",
                "empty_state": f"No {domain} entries found banner",
                "error_state": "Failed to fetch data error card with Retry button",
                "success_state": f"Render {domain} cards list",
                "navigation_targets": [f"/{domain}/add", f"/{domain}/detail", "/profile"]
            },
            {
                "id": f"{domain}_detail_screen",
                "name": f"{domain.capitalize()}DetailScreen",
                "purpose": f"Detailed view of {domain} record",
                "route": f"/{domain}/detail",
                "ui_components": ["DetailCard", "StatusChip", "DeleteButton"],
                "input_fields": [],
                "validation": [],
                "api_calls": [f"DELETE /api/{domain}s/:id"],
                "state_required": ["selected_item"],
                "loading_state": "Loading Details",
                "empty_state": "Item Not Found",
                "error_state": "Delete error message",
                "success_state": "Item deleted, navigate back",
                "navigation_targets": ["/dashboard"]
            },
            {
                "id": f"add_{domain}_screen",
                "name": f"Add{domain.capitalize()}Screen",
                "purpose": f"Form to create/edit {domain} record",
                "route": f"/{domain}/add",
                "ui_components": ["FormInputField", "DropdownSelector", "SubmitButton"],
                "input_fields": [
                    {"name": "title", "type": "text"},
                    {"name": "description", "type": "text"},
                    {"name": "amount", "type": "number"}
                ],
                "validation": ["Title required", "Amount positive number"],
                "api_calls": [f"POST /api/{domain}s"],
                "state_required": ["is_saving"],
                "loading_state": "Saving entry indicator",
                "empty_state": "Blank form",
                "error_state": "Submission Error Alert",
                "success_state": "Record saved, return to dashboard",
                "navigation_targets": ["/dashboard"]
            },
            {
                "id": "profile_screen",
                "name": "ProfileScreen",
                "purpose": "User settings & theme controls",
                "route": "/profile",
                "ui_components": ["ProfileAvatar", "SettingsTile", "LogoutButton"],
                "input_fields": [],
                "validation": [],
                "api_calls": [],
                "state_required": ["user_info"],
                "loading_state": "None",
                "empty_state": "N/A",
                "error_state": "N/A",
                "success_state": "Profile rendered",
                "navigation_targets": ["/login"]
            }
        ]

    @classmethod
    def generate_api_contract(cls, app_name: str, domain: str, needs_backend: bool) -> Dict[str, Any]:
        if not needs_backend:
            return {"endpoints": [], "shared_version": "1.0.0"}

        if domain == "weather":
            endpoints = [
                {
                    "method": "GET",
                    "path": "/api/health",
                    "purpose": "Backend health status check",
                    "request_schema": {},
                    "response_schema": {"status": "string", "service": "string"},
                    "validation": [],
                    "authentication_requirement": False,
                    "error_responses": [{"code": 500, "message": "Server Error"}]
                },
                {
                    "method": "GET",
                    "path": "/api/weather/current",
                    "purpose": "Fetch current weather details for city",
                    "request_schema": {},
                    "response_schema": {"success": True, "data": {"city": "string", "temp": "number"}},
                    "validation": [],
                    "authentication_requirement": False,
                    "error_responses": [{"code": 404, "message": "City not found"}]
                },
                {
                    "method": "GET",
                    "path": "/api/weather/forecast",
                    "purpose": "Fetch forecast for city",
                    "request_schema": {},
                    "response_schema": {"success": True, "forecast": []},
                    "validation": [],
                    "authentication_requirement": False,
                    "error_responses": []
                },
                {
                    "method": "GET",
                    "path": "/api/weather/search",
                    "purpose": "Search matching cities weather data",
                    "request_schema": {},
                    "response_schema": {"success": True, "data": []},
                    "validation": [],
                    "authentication_requirement": False,
                    "error_responses": []
                }
            ]
        else:
            endpoints = [
                {
                    "method": "GET",
                    "path": "/api/health",
                    "purpose": "Backend health status check",
                    "request_schema": {},
                    "response_schema": {"status": "string", "service": "string"},
                    "validation": [],
                    "authentication_requirement": False,
                    "error_responses": [{"code": 500, "message": "Server Error"}]
                },
                {
                    "method": "POST",
                    "path": "/api/auth/login",
                    "purpose": "User login and JWT retrieval",
                    "request_schema": {"email": "string", "password": "string"},
                    "response_schema": {"token": "string", "user": {"id": "string", "name": "string", "email": "string"}},
                    "validation": ["email required", "password required"],
                    "authentication_requirement": False,
                    "error_responses": [{"code": 401, "message": "Invalid Credentials"}]
                },
                {
                    "method": "GET",
                    "path": f"/api/{domain}s",
                    "purpose": f"Fetch all {domain} records",
                    "request_schema": {},
                    "response_schema": {"data": [{"id": "string", "title": "string", "amount": "number", "category": "string"}]},
                    "validation": [],
                    "authentication_requirement": True,
                    "error_responses": [{"code": 401, "message": "Unauthorized"}]
                },
                {
                    "method": "POST",
                    "path": f"/api/{domain}s",
                    "purpose": f"Create a new {domain} record",
                    "request_schema": {"title": "string", "description": "string", "amount": "number", "category": "string"},
                    "response_schema": {"success": True, "item": {"id": "string", "title": "string"}},
                    "validation": ["title required", "amount numeric"],
                    "authentication_requirement": True,
                    "error_responses": [{"code": 400, "message": "Validation Error"}]
                },
                {
                    "method": "DELETE",
                    "path": f"/api/{domain}s/:id",
                    "purpose": f"Delete a {domain} record by ID",
                    "request_schema": {},
                    "response_schema": {"success": True, "deleted_id": "string"},
                    "validation": ["id parameter required"],
                    "authentication_requirement": True,
                    "error_responses": [{"code": 404, "message": "Record Not Found"}]
                }
            ]

        return {
            "shared_version": "1.0.0",
            "base_url": "http://10.0.2.2:3000/api",
            "endpoints": endpoints
        }

    @classmethod
    def generate_database_plan(cls, app_name: str, domain: str, needs_backend: bool) -> Dict[str, Any]:
        if not needs_backend:
            return {"storage": "SharedPreferences", "entities": []}

        entities = [
            {
                "name": "User",
                "table_or_collection": "users",
                "fields": [
                    {"name": "id", "type": "String", "required": True, "unique": True},
                    {"name": "name", "type": "String", "required": True, "unique": False},
                    {"name": "email", "type": "String", "required": True, "unique": True},
                    {"name": "password_hash", "type": "String", "required": True, "unique": False},
                    {"name": "role", "type": "String", "required": True, "unique": False}
                ],
                "relationships": [f"One-to-Many with {domain.capitalize()}"],
                "indexes": ["email"]
            },
            {
                "name": domain.capitalize(),
                "table_or_collection": f"{domain}s",
                "fields": [
                    {"name": "id", "type": "String", "required": True, "unique": True},
                    {"name": "user_id", "type": "String", "required": True, "unique": False},
                    {"name": "title", "type": "String", "required": True, "unique": False},
                    {"name": "description", "type": "String", "required": False, "unique": False},
                    {"name": "category", "type": "String", "required": True, "unique": False},
                    {"name": "amount", "type": "Number", "required": True, "unique": False},
                    {"name": "status", "type": "String", "required": True, "unique": False},
                    {"name": "createdAt", "type": "String", "required": True, "unique": False}
                ],
                "relationships": ["Belongs-to User"],
                "indexes": ["user_id", "category"]
            }
        ]

        return {
            "storage_type": "JSON File Persistence Store (`data/store.json`)",
            "entities": entities,
            "validation": "Strict Field Type Guarding on Read/Write"
        }

    @classmethod
    def generate_ui_design_plan(cls, ui_reqs: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "visual_style": "Modern Dark Glassmorphism",
            "color_system": {
                "background": ui_reqs.get("colors", ["#0F172A"])[0] if ui_reqs.get("colors") else "#0F172A",
                "surface": "#1E293B",
                "primary": "#38BDF8",
                "secondary": "#818CF8",
                "accent": "#2DD4BF",
                "error": "#EF4444"
            },
            "typography": {
                "headline": "Roboto / Inter Bold 24px",
                "title": "Roboto / Inter SemiBold 18px",
                "body": "Roboto / Inter Regular 14px"
            },
            "spacing": "16px standard grid",
            "border_radius": "12px rounded cards",
            "cards": "Elevated glassmorphism containers with subtle borders",
            "buttons": "Primary solid filled buttons with active tap effect",
            "navigation": "Bottom Navigation Bar with icon indicators",
            "forms": "Outlined input fields with floating labels",
            "dark_mode": True,
            "animations": "Fade and Slide transitions",
            "references": ui_reqs.get("references", []),
            "images": ui_reqs.get("images", [])
        }

    @classmethod
    def generate_flutter_plan(cls, app_name: str, domain: str, screens: List[Dict[str, Any]], ui_plan: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "folder_structure": [
                "lib/theme/",
                "lib/models/",
                "lib/services/",
                "lib/widgets/",
                "lib/screens/"
            ],
            "screens": screens,
            "widgets": ["CustomCard", "PrimaryButton", "StatusChip"],
            "models": ["UserModel", f"{domain.capitalize()}ItemModel"],
            "providers": ["AppProvider"],
            "services": ["ApiService"],
            "repositories": [f"{domain.capitalize()}Repository"],
            "api_service": "lib/services/api_service.dart",
            "routing": "MaterialPageRoute onGenerateRoute",
            "theme": ui_plan,
            "assets": [],
            "dependencies": ["flutter", "http", "provider", "shared_preferences", "intl"]
        }

    @classmethod
    def generate_node_plan(cls, app_name: str, domain: str, api_contract: Dict[str, Any], db_plan: Dict[str, Any], needs_backend: bool) -> Dict[str, Any]:
        if not needs_backend:
            return {"server_type": "None", "routes": [], "controllers": []}

        return {
            "express_structure": [
                "src/config/",
                "src/controllers/",
                "src/routes/",
                "src/middleware/",
                "src/models/",
                "tests/",
                "data/"
            ],
            "routes": ["authRoutes.js", f"{domain}Routes.js", "healthRoutes.js"],
            "controllers": ["authController.js", f"{domain}Controller.js", "healthController.js"],
            "services": [f"{domain}Service.js"],
            "middleware": ["cors", "express.json", "authMiddleware", "errorHandler"],
            "models_store": [f"data/{domain}_store.json"],
            "validation": "Express-Validator or Schema Checks",
            "error_handling": "Centralized Error Catch Middleware",
            "env_variables": ["PORT=3000", "NODE_ENV=development", "JWT_SECRET=jarvis_secret"],
            "database_layer": db_plan
        }

    @classmethod
    def generate_dependency_plan(cls, needs_backend: bool) -> Dict[str, Any]:
        flutter_deps = [
            {"package": "flutter", "reason": "UI Framework SDK", "version_range": ">=3.0.0"},
            {"package": "http", "reason": "REST API Communication Client", "version_range": "^1.2.1"},
            {"package": "provider", "reason": "State Management", "version_range": "^6.1.2"},
            {"package": "shared_preferences", "reason": "Local Key-Value Storage", "version_range": "^2.2.3"},
            {"package": "intl", "reason": "Date & Currency Formatting", "version_range": "^0.19.0"}
        ]

        node_deps = [
            {"package": "express", "reason": "HTTP Web Framework", "version_range": "^4.19.2"},
            {"package": "cors", "reason": "Cross-Origin Resource Sharing", "version_range": "^2.8.5"},
            {"package": "dotenv", "reason": "Environment Variables Loader", "version_range": "^16.4.5"},
            {"package": "morgan", "reason": "HTTP Request Logger", "version_range": "^1.10.0"}
        ] if needs_backend else []

        return {
            "flutter": flutter_deps,
            "node": node_deps
        }

    @classmethod
    def generate_implementation_order(cls, needs_backend: bool) -> List[str]:
        steps = [
            "1. Create Flutter project structure & pubspec.yaml",
            "2. Configure dependencies & Flutter linting",
            "3. Implement theme & design system tokens",
            "4. Create Dart data models & JSON serialization",
            "5. Create API client service",
            "6. Build reusable UI widgets (CustomCard, PrimaryButton, StatusChip)",
            "7. Build screens (Splash, Login, Dashboard, Detail, Add, Profile)",
            "8. Configure Flutter screen navigation & routing"
        ]

        if needs_backend:
            steps.extend([
                "9. Initialize Node.js Express server & package.json",
                "10. Configure database storage layer & JSON store",
                "11. Create Express controllers & business logic",
                "12. Configure API routes & middleware",
                "13. Verify integration between Flutter & Node.js REST API",
                "14. Run automated test suites (flutter analyze & node tests)",
                "15. Auto-debug and resolve any build errors",
                "16. Compile final APK / launch IDEs"
            ])
        else:
            steps.extend([
                "9. Verify Flutter local execution & test suites",
                "10. Compile final APK / launch Android Studio"
            ])

        return steps
