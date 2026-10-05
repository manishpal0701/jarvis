"""
tools/app_builder/app_requirements_analyzer.py
Phase 3 — App Requirements Analyzer & Missing Requirement Detector.
Parses AppBrief, chat context, design preferences, and reference metadata into 17 structured requirement categories.
Detects critical missing information, infers sensible defaults, and determines readiness (READY / NEEDS_CLARIFICATION).
"""
import re
import logging
from typing import Dict, Any, List, Optional
from tools.app_builder.app_model import AppBrief

logger = logging.getLogger("AppRequirementsAnalyzer")


class AppRequirementsAnalyzer:
    """
    Analyzes AppBrief and chat context into 17 structured requirement categories.
    """

    @classmethod
    def analyze(
        cls,
        brief: AppBrief,
        chat_history: Optional[List[str]] = None,
        latest_requirements: Optional[str] = ""
    ) -> Dict[str, Any]:
        """
        Parses all brief data and produces a comprehensive requirements analysis dict.
        """
        desc = brief.description or latest_requirements or ""
        full_text = getattr(brief, "full_text", "") or desc

        app_name = brief.name
        if not app_name or app_name in ["Mobile Application", "App", "Mobile App", "JarvisApp"]:
            name_match = re.search(
                r"(?:^|\n|\.|\s)\s*(?:app\s+ka\s+naam|app\s+name|name\s+of\s+(?:the\s+)?app|name)\s*(?::|=|\s+is|\s+hai|\s+)\s*[\"']?([^\"'\.\,\n\r]+)[\"']?\s*(?:hai|\.|\r|\n|$)",
                full_text,
                re.IGNORECASE
            )
            if name_match:
                extracted = name_match.group(1).strip()
                extracted = re.sub(r"(?i)^(?:is|hai|=|:)\s+", "", extracted).strip()
                extracted = re.sub(r"(?i)\s+hai$", "", extracted).strip().rstrip(".")
                if extracted and len(extracted) < 50:
                    app_name = extracted
                    brief.name = extracted
            elif "music" in full_text.lower() or "spotify" in full_text.lower():
                app_name = "JARVIS Music"
                brief.name = app_name

        # Extract/Infer core features
        features = list(brief.features or [])
        if latest_requirements and latest_requirements not in features:
            # Parse individual items if comma/newline separated
            split_reqs = [r.strip() for r in re.split(r'[,;\n]', latest_requirements) if r.strip()]
            for sr in split_reqs:
                if sr not in features:
                    features.append(sr)

        # Detect domain & purpose
        domain = cls._detect_domain(app_name, desc, features, full_text=full_text)
        purpose = desc or f"Mobile Android application for {app_name} ({domain})"
        target_users = brief.additional_instructions or ["General Android Users", "End Users"]

        # Core vs Secondary Features
        core_features = []
        secondary_features = []
        for feat in features:
            lower_f = feat.lower()
            if any(k in lower_f for k in ["login", "auth", "dashboard", "crud", "track", "manage", "calculator", "add", "list", "view", "play", "player", "song", "search", "playlist"]):
                core_features.append(feat)
            else:
                secondary_features.append(feat)

        if not core_features and features:
            core_features = features[:2]
            secondary_features = features[2:]
        elif not core_features:
            core_features = [f"Manage {domain.capitalize()}", "View Dashboard"]
            secondary_features = ["User Profile Settings", "Export Data"]

        # Screens & Navigation Requirements
        screens = cls._infer_screens(app_name, domain, core_features)
        nav_reqs = [f"Bottom Navigation / Stack routing for {len(screens)} screens", "Splash -> Auth -> Dashboard flow"]

        # Authentication Requirements
        auth_req = brief.authentication
        if not auth_req:
            if domain in ["calculator", "utility", "clock", "flashlight"]:
                auth_req = "NONE"
            else:
                auth_req = "JWT / Local Mock Authentication"

        # Data & Offline Requirements
        data_reqs = brief.data_requirements if hasattr(brief, 'data_requirements') and brief.data_requirements else [f"{domain.capitalize()} records schema", "User session profile"]
        offline_reqs = ["SharedPreferences caching", "Offline-first fallback state"]

        # Backend, API, & Database Requirements
        needs_backend = auth_req != "NONE" or domain not in ["calculator", "utility", "clock"]
        backend_reqs = ["Express.js REST Server on Node.js", "CORS Middleware", "JSON Error Handling"] if needs_backend else ["Client-side local execution only"]
        if needs_backend:
            if domain == "music":
                api_reqs = ["POST /api/auth/login", "GET /api/songs", "GET /api/playlists", "GET /api/health"]
                db_reqs = ["JSON File Store for songs & playlists (`data/songs_store.json`)"]
            else:
                api_reqs = ["POST /api/auth/login", f"GET /api/{domain}s", f"POST /api/{domain}s", f"DELETE /api/{domain}s/:id"]
                db_reqs = [f"JSON File Store for {domain} records (`data/{domain}_store.json`)"]
        else:
            api_reqs = []
            db_reqs = ["Local Device Storage"]

        # UI & Design Requirements
        theme_desc = brief.ui_ux.get("theme") if isinstance(brief.ui_ux, dict) else None
        if not theme_desc:
            theme_desc = "Spotify Dark Theme (#121212 / #1DB954 Green)" if domain == "music" else "Dark Blue Theme"
        colors = brief.ui_ux.get("colors") if isinstance(brief.ui_ux, dict) and brief.ui_ux.get("colors") else (["#121212", "#1DB954", "#282828"] if domain == "music" else ["#0F172A", "#1E293B", "#38BDF8"])
        ui_reqs = {
            "theme": theme_desc,
            "colors": colors,
            "fonts": ["Roboto", "Inter"],
            "spacing": "16.0",
            "border_radius": "12.0",
            "dark_mode": True,
            "animations": brief.ui_ux.get("animations") if isinstance(brief.ui_ux, dict) else ["Smooth screen transitions"],
            "references": brief.references or [],
            "images": brief.images or []
        }

        # Integrations, Permissions, Validation
        integrations = brief.apis or (["HTTP API Client"] if needs_backend else [])
        permissions = brief.platforms or ["android.permission.INTERNET", "android.permission.ACCESS_NETWORK_STATE"]
        validation_reqs = ["Form input required fields", "Email format validation", "Numeric bounds validation"]

        from tools.app_builder.app_model import AppBuildSpec
        build_spec = AppBuildSpec(
            app_id=getattr(brief, "app_id", ""),
            app_name=app_name,
            domain=domain,
            platform="Android",
            frontend_stack="Flutter",
            backend_stack="Node.js + Express",
            database=db_reqs[0] if db_reqs else "JSON File Store",
            features=core_features + secondary_features,
            screens=screens,
            apis=api_reqs,
            design=ui_reqs["theme"],
            is_locked=True
        )

        analyzed = {
            "app_name": app_name,
            "app_purpose": purpose,
            "target_users": target_users,
            "domain": domain,
            "needs_backend": needs_backend,
            "core_features": core_features,
            "secondary_features": secondary_features,
            "screens": screens,
            "navigation_requirements": nav_reqs,
            "authentication_requirements": auth_req,
            "data_requirements": data_reqs,
            "offline_requirements": offline_reqs,
            "backend_requirements": backend_reqs,
            "api_requirements": api_reqs,
            "database_requirements": db_reqs,
            "ui_design_requirements": ui_reqs,
            "integrations": integrations,
            "permissions": permissions,
            "validation_requirements": validation_reqs,
            "build_spec": build_spec.to_dict()
        }

        logger.info(f"Analyzed requirements for '{app_name}' (domain={domain}, backend={needs_backend})")
        return analyzed

    @classmethod
    def _detect_domain(cls, name: str, desc: str, features: List[str], full_text: str = "") -> str:
        combined = (name + " " + desc + " " + full_text + " " + " ".join(features)).lower()
        if any(w in combined for w in ["weather", "forecast", "temp", "temperature", "climate", "rain", "wind", "humidity"]):
            return "weather"
        elif any(w in combined for w in ["music", "spotify", "audio", "song", "songs", "album", "artist", "playlist", "radio", "podcast", "mp3", "playback", "music player", "audio player"]):
            return "music"
        elif "calc" in combined or "math" in combined:
            return "calculator"
        elif "expense" in combined or "money" in combined or "budget" in combined or "cost" in combined or "finance" in combined:
            return "expense"
        elif "attendance" in combined or "roll" in combined or "present" in combined:
            return "attendance"
        elif "fitness" in combined or "workout" in combined or "calorie" in combined or "gym" in combined:
            return "fitness"
        elif "shop" in combined or "store" in combined or "cart" in combined:
            return "product"
        elif "task" in combined or "todo" in combined or "note" in combined:
            return "task"
        else:
            return "item"

    @classmethod
    def _infer_screens(cls, app_name: str, domain: str, core_features: List[str]) -> List[Dict[str, Any]]:
        if domain == "calculator":
            return [
                {
                    "id": "calculator_screen",
                    "name": "CalculatorScreen",
                    "purpose": "Primary scientific/basic math calculator screen",
                    "route": "/"
                }
            ]
        elif domain == "music":
            return [
                {"id": "splash_screen", "name": "SplashScreen", "purpose": "App branding & auth check", "route": "/splash"},
                {"id": "login_screen", "name": "LoginScreen", "purpose": "User login & authentication", "route": "/login"},
                {"id": "home_screen", "name": "HomeScreen", "purpose": "Browse featured songs, trending artists & playlists", "route": "/home"},
                {"id": "player_screen", "name": "MusicPlayerScreen", "purpose": "Full audio player controls, seekbar & queue", "route": "/player"},
                {"id": "playlist_screen", "name": "PlaylistScreen", "purpose": "User created playlists & liked songs", "route": "/playlists"},
                {"id": "profile_screen", "name": "ProfileScreen", "purpose": "User settings & preferences", "route": "/profile"}
            ]
        elif domain == "weather":
            return [
                {"id": "splash_screen", "name": "SplashScreen", "purpose": "App branding & weather load", "route": "/splash"},
                {"id": "home_screen", "name": "HomeScreen", "purpose": "Current location weather, hourly & 7-day forecast", "route": "/home"},
                {"id": "search_screen", "name": "SearchScreen", "purpose": "Search worldwide city locations", "route": "/search"},
                {"id": "saved_locations_screen", "name": "SavedLocationsScreen", "purpose": "Manage & switch saved worldwide locations", "route": "/saved"},
                {"id": "details_screen", "name": "WeatherDetailScreen", "purpose": "Detailed weather metrics & forecast", "route": "/details"}
            ]
        elif domain == "task":
            return [
                {"id": "splash_screen", "name": "SplashScreen", "purpose": "App branding & auth check", "route": "/splash"},
                {"id": "login_screen", "name": "LoginScreen", "purpose": "User login & token retrieval", "route": "/login"},
                {"id": "dashboard_screen", "name": "DashboardScreen", "purpose": "Task summary metrics & today's tasks", "route": "/dashboard"},
                {"id": "task_list_screen", "name": "TaskListScreen", "purpose": "All tasks list with Riverpod filtering & actions", "route": "/tasks"},
                {"id": "search_screen", "name": "SearchScreen", "purpose": "Search tasks by title or category", "route": "/search"},
                {"id": "categories_screen", "name": "CategoriesScreen", "purpose": "Manage task categories & projects", "route": "/categories"},
                {"id": "task_detail_screen", "name": "TaskDetailScreen", "purpose": "View task details & completion status", "route": "/task/detail"},
                {"id": "create_task_screen", "name": "CreateTaskScreen", "purpose": "Create task form", "route": "/task/create"},
                {"id": "edit_task_screen", "name": "EditTaskScreen", "purpose": "Edit task form", "route": "/task/edit"},
                {"id": "profile_screen", "name": "ProfileScreen", "purpose": "User settings & statistics", "route": "/profile"}
            ]

        return [
            {"id": "splash_screen", "name": "SplashScreen", "purpose": "App branding & auth state check", "route": "/splash"},
            {"id": "login_screen", "name": "LoginScreen", "purpose": "User login & credentials authentication", "route": "/login"},
            {"id": "dashboard_screen", "name": "DashboardScreen", "purpose": f"Overview summary metrics for {app_name}", "route": "/dashboard"},
            {"id": f"{domain}_detail_screen", "name": f"{domain.capitalize()}DetailScreen", "purpose": f"Detailed view of {domain} record", "route": f"/{domain}/detail"},
            {"id": f"add_{domain}_screen", "name": f"Add{domain.capitalize()}Screen", "purpose": f"Form to create/edit {domain} record", "route": f"/{domain}/add"},
            {"id": "profile_screen", "name": "ProfileScreen", "purpose": "User settings & theme controls", "route": "/profile"}
        ]


class MissingRequirementDetector:
    """
    Detects critical missing information, infers sensible defaults where safe,
    and returns status (READY / NEEDS_CLARIFICATION).
    """

    @classmethod
    def check_requirements(cls, analyzed_reqs: Dict[str, Any], raw_brief: AppBrief) -> Dict[str, Any]:
        missing_fields = []
        critical_questions = []
        inferred_defaults = {}

        app_name = analyzed_reqs.get("app_name", "")
        domain = analyzed_reqs.get("domain", "item")
        desc = raw_brief.description or ""

        # Case 1: Extremely ambiguous request without domain or name (e.g. "make an app")
        if (not app_name or app_name.lower() in ["app", "jarvisapp", "my app"]) and not desc and not raw_brief.features:
            critical_questions.append("What type of app would you like to build? (e.g. Expense Tracker, Calculator, Task Manager)")
            missing_fields.append("app_type_and_features")

        # Case 2: Complex app explicitly requested (e.g. Banking / Payment Gateway) without auth/security parameters
        if "bank" in desc.lower() or "payment" in desc.lower() or "crypto" in desc.lower():
            if not raw_brief.authentication:
                critical_questions.append("Financial/Banking apps require explicit security parameters. Which auth method should be used? (OAuth2 / Biometric / JWT)")
                missing_fields.append("security_auth_method")

        # Case 3: Sensible defaults for standard apps
        if domain == "calculator":
            inferred_defaults["auth"] = "NONE (Utility App)"
            inferred_defaults["backend"] = "NONE (Local Execution)"
            inferred_defaults["screens"] = "Single Main Calculator Screen"
        elif domain == "expense":
            inferred_defaults["currency"] = "USD ($)"
            inferred_defaults["auth"] = "JWT Auth"
            inferred_defaults["storage"] = "Node.js Express + JSON File Store"
        else:
            inferred_defaults["auth"] = "JWT Auth"
            inferred_defaults["theme"] = "Dark Blue Modern Theme"
            inferred_defaults["backend"] = "Express.js REST API"

        # Determine status
        status = "NEEDS_CLARIFICATION" if critical_questions else "READY"

        return {
            "status": status,
            "missing_fields": missing_fields,
            "critical_questions": critical_questions,
            "inferred_defaults": inferred_defaults
        }
