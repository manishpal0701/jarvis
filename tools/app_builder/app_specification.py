"""
tools/app_builder/app_specification.py
Phase 1 — Structured ApplicationSpecification Model & Builder.
Generates comprehensive product specifications from user briefs prior to architecture planning & code generation.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional

from tools.app_builder.app_model import AppBrief

logger = logging.getLogger("ApplicationSpecification")


class ApplicationSpecification:
    """
    Structured ApplicationSpecification data model representing complete product requirements.
    """

    def __init__(
        self,
        app_id: str = "",
        app_name: str = "JARVIS Application",
        domain: str = "item",
        app_purpose: str = "",
        target_users: Optional[List[str]] = None,
        platform: str = "Android",
        frontend_technology: str = "Flutter",
        backend_technology: str = "Node.js + Express",
        database_requirement: str = "JSON File Store",
        authentication_requirement: str = "JWT Authentication",
        core_features: Optional[List[str]] = None,
        secondary_features: Optional[List[str]] = None,
        screens: Optional[List[Dict[str, Any]]] = None,
        navigation_flow: Optional[List[str]] = None,
        api_requirements: Optional[List[Dict[str, Any]]] = None,
        data_models: Optional[List[Dict[str, Any]]] = None,
        user_roles: Optional[List[str]] = None,
        external_integrations: Optional[List[str]] = None,
        media_requirements: Optional[Dict[str, Any]] = None,
        offline_requirements: Optional[List[str]] = None
    ):
        self.app_id = app_id
        self.app_name = app_name
        self.domain = domain
        self.app_purpose = app_purpose or f"Production-ready mobile application for {app_name}"
        self.target_users = target_users or ["End Users", "Administrators"]
        self.platform = platform
        self.frontend_technology = frontend_technology
        self.backend_technology = backend_technology
        self.database_requirement = database_requirement
        self.authentication_requirement = authentication_requirement
        self.core_features = core_features or []
        self.secondary_features = secondary_features or []
        self.screens = screens or []
        self.navigation_flow = navigation_flow or []
        self.api_requirements = api_requirements or []
        self.data_models = data_models or []
        self.user_roles = user_roles or ["user", "admin"]
        self.external_integrations = external_integrations or []
        self.media_requirements = media_requirements or {"audio": False, "images": True, "video": False}
        self.offline_requirements = offline_requirements or ["Local caching", "Offline fallback state"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "app_id": self.app_id,
            "app_name": self.app_name,
            "domain": self.domain,
            "app_purpose": self.app_purpose,
            "target_users": self.target_users,
            "platform": self.platform,
            "frontend_technology": self.frontend_technology,
            "backend_technology": self.backend_technology,
            "database_requirement": self.database_requirement,
            "authentication_requirement": self.authentication_requirement,
            "core_features": self.core_features,
            "secondary_features": self.secondary_features,
            "screens": self.screens,
            "navigation_flow": self.navigation_flow,
            "api_requirements": self.api_requirements,
            "data_models": self.data_models,
            "user_roles": self.user_roles,
            "external_integrations": self.external_integrations,
            "media_requirements": self.media_requirements,
            "offline_requirements": self.offline_requirements
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApplicationSpecification":
        if not data:
            return cls()
        return cls(
            app_id=data.get("app_id", ""),
            app_name=data.get("app_name", "JARVIS Application"),
            domain=data.get("domain", "item"),
            app_purpose=data.get("app_purpose", ""),
            target_users=data.get("target_users"),
            platform=data.get("platform", "Android"),
            frontend_technology=data.get("frontend_technology", "Flutter"),
            backend_technology=data.get("backend_technology", "Node.js + Express"),
            database_requirement=data.get("database_requirement", "JSON File Store"),
            authentication_requirement=data.get("authentication_requirement", "JWT Authentication"),
            core_features=data.get("core_features"),
            secondary_features=data.get("secondary_features"),
            screens=data.get("screens"),
            navigation_flow=data.get("navigation_flow"),
            api_requirements=data.get("api_requirements"),
            data_models=data.get("data_models"),
            user_roles=data.get("user_roles"),
            external_integrations=data.get("external_integrations"),
            media_requirements=data.get("media_requirements"),
            offline_requirements=data.get("offline_requirements")
        )

    def save_to_workspace(self, workspace_path: str) -> str:
        abs_path = os.path.abspath(workspace_path)
        os.makedirs(abs_path, exist_ok=True)
        spec_file = os.path.join(abs_path, "application_specification.json")
        build_spec_file = os.path.join(abs_path, "app_build_spec.json")
        try:
            with open(spec_file, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
            with open(build_spec_file, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.info(f"Saved ApplicationSpecification to '{spec_file}' & '{build_spec_file}'")
        except Exception as ex:
            logger.error(f"Failed writing application_specification.json: {ex}")
        return spec_file


class AppSpecificationBuilder:
    """
    Constructs detailed ApplicationSpecification instances tailored to the target domain.
    """

    @classmethod
    def from_brief(cls, brief: Optional[AppBrief] = None, workspace_path: str = "") -> ApplicationSpecification:
        if not brief:
            brief = AppBrief()
        spec = cls.build_specification(brief)
        if workspace_path:
            spec.save_to_workspace(workspace_path)
        return spec

    @classmethod
    def build_specification(
        cls,
        brief: AppBrief,
        app_id: str = "",
        analyzed_dict: Optional[Dict[str, Any]] = None
    ) -> ApplicationSpecification:
        from tools.app_builder.app_requirements_analyzer import AppRequirementsAnalyzer
        analyzed = analyzed_dict or AppRequirementsAnalyzer.analyze(brief)

        app_name = analyzed.get("app_name") or (brief.name if brief else "") or "JARVIS Application"
        domain = analyzed.get("domain", "item")
        needs_backend = analyzed.get("needs_backend", True)

        # Domain-Tailored Specifications
        if domain == "music":
            spec = cls._build_music_spec(app_id, app_name, analyzed)
        elif domain == "weather":
            spec = cls._build_weather_spec(app_id, app_name, analyzed)
        elif domain == "expense":
            spec = cls._build_finance_spec(app_id, app_name, analyzed)
        elif domain == "product":
            spec = cls._build_ecommerce_spec(app_id, app_name, analyzed)
        elif domain == "task":
            spec = cls._build_task_spec(app_id, app_name, analyzed)
        elif domain == "social":
            spec = cls._build_social_spec(app_id, app_name, analyzed)
        else:
            spec = cls._build_generic_spec(app_id, app_name, domain, analyzed)

        logger.info(f"[APP_SPECIFICATION] Created spec for app_name='{app_name}' domain='{domain}' screens={len(spec.screens)}")
        return spec

    @classmethod
    def _build_music_spec(cls, app_id: str, app_name: str, analyzed: Dict[str, Any]) -> ApplicationSpecification:
        screens = [
            {"id": "splash_screen", "name": "SplashScreen", "purpose": "App branding & audio engine init", "route": "/splash", "is_primary": False},
            {"id": "login_screen", "name": "LoginScreen", "purpose": "User account login & token storage", "route": "/login", "is_primary": False},
            {"id": "home_screen", "name": "HomeScreen", "purpose": "Browse featured tracks, trending playlists & quick picks", "route": "/home", "is_primary": True},
            {"id": "search_screen", "name": "SearchScreen", "purpose": "Live track, artist & genre search bar", "route": "/search", "is_primary": True},
            {"id": "library_screen", "name": "LibraryScreen", "purpose": "User playlists, liked songs & recent history", "route": "/library", "is_primary": True},
            {"id": "player_screen", "name": "MusicPlayerScreen", "purpose": "Full-screen music player with artwork, seekbar & controls", "route": "/player", "is_primary": False},
            {"id": "playlist_screen", "name": "PlaylistDetailScreen", "purpose": "Playlist track listing & playback controls", "route": "/playlist/detail", "is_primary": False},
            {"id": "profile_screen", "name": "ProfileScreen", "purpose": "Account details & audio quality preferences", "route": "/profile", "is_primary": True}
        ]

        apis = [
            {"method": "POST", "endpoint": "/api/auth/login", "description": "Authenticate user & return token", "auth_required": False},
            {"method": "GET", "endpoint": "/api/health", "description": "Backend health status", "auth_required": False},
            {"method": "GET", "endpoint": "/api/songs", "description": "Fetch featured & trending songs", "auth_required": True},
            {"method": "GET", "endpoint": "/api/playlists", "description": "Fetch user playlists", "auth_required": True},
            {"method": "POST", "endpoint": "/api/playlists", "description": "Create new playlist", "auth_required": True},
            {"method": "POST", "endpoint": "/api/songs/like", "description": "Toggle liked song status", "auth_required": True}
        ]

        models = [
            {"name": "SongModel", "fields": ["id", "title", "artist", "album", "duration", "artworkUrl", "audioUrl", "isLiked"]},
            {"name": "PlaylistModel", "fields": ["id", "name", "description", "coverUrl", "songCount", "songs"]},
            {"name": "UserModel", "fields": ["id", "name", "email", "subscription", "avatarUrl"]}
        ]

        return ApplicationSpecification(
            app_id=app_id,
            app_name=app_name,
            domain="music",
            app_purpose=f"Commercial-grade music streaming application with live audio controls & playlist management",
            target_users=["Music Listeners", "Audio Enthusiasts"],
            database_requirement="JSON File Store (`data/music_store.json`)",
            authentication_requirement="JWT Token Authentication",
            core_features=["Featured Tracks Home", "Live Track Search", "Full Audio Player", "Mini Player Bar", "Playlist Management", "Liked Songs"],
            secondary_features=["Audio Quality Settings", "Dark Spotify Theme", "Offline Song Caching"],
            screens=screens,
            navigation_flow=["Splash -> Login -> BottomNav (Home, Search, Library, Profile) -> Player Screen"],
            api_requirements=apis,
            data_models=models,
            media_requirements={"audio": True, "images": True, "video": False}
        )

    @classmethod
    def _build_weather_spec(cls, app_id: str, app_name: str, analyzed: Dict[str, Any]) -> ApplicationSpecification:
        screens = [
            {"id": "splash_screen", "name": "SplashScreen", "purpose": "App branding & location load", "route": "/splash", "is_primary": False},
            {"id": "home_screen", "name": "HomeScreen", "purpose": "Current location weather hero card, hourly & 7-day forecast", "route": "/home", "is_primary": True},
            {"id": "search_screen", "name": "SearchScreen", "purpose": "Search global cities & add to saved list", "route": "/search", "is_primary": True},
            {"id": "saved_screen", "name": "SavedLocationsScreen", "purpose": "Manage saved city cards & quick metrics", "route": "/saved", "is_primary": True},
            {"id": "details_screen", "name": "WeatherDetailScreen", "purpose": "Comprehensive weather metrics (UV, Wind, Humidity, Pressure)", "route": "/details", "is_primary": False}
        ]

        apis = [
            {"method": "GET", "endpoint": "/api/health", "description": "Backend health status", "auth_required": False},
            {"method": "GET", "endpoint": "/api/weather/current", "description": "Get current weather by city", "auth_required": False},
            {"method": "GET", "endpoint": "/api/weather/forecast", "description": "Get 7-day weather forecast", "auth_required": False},
            {"method": "GET", "endpoint": "/api/weather/hourly", "description": "Get 24-hour weather forecast", "auth_required": False},
            {"method": "GET", "endpoint": "/api/weather/search", "description": "Search matching cities", "auth_required": False}
        ]

        models = [
            {"name": "WeatherModel", "fields": ["city", "tempC", "condition", "icon", "humidity", "windSpeedKmh", "uvIndex", "highC", "lowC"]},
            {"name": "ForecastDayModel", "fields": ["day", "date", "tempHigh", "tempLow", "condition", "icon"]},
            {"name": "HourlyForecastModel", "fields": ["time", "tempC", "condition", "rainProbability"]}
        ]

        return ApplicationSpecification(
            app_id=app_id,
            app_name=app_name,
            domain="weather",
            app_purpose=f"Real-time weather forecast application with hourly & 7-day metrics",
            target_users=["Daily Commuters", "Travelers"],
            database_requirement="JSON File Store (`data/weather_store.json`)",
            authentication_requirement="Optional Guest Access",
            core_features=["Current Location Weather", "24-Hour Hourly Forecast", "7-Day Forecast Cards", "Global City Search", "Saved Locations"],
            secondary_features=["Animated Weather Icons", "Temperature Unit Switcher (°C/°F)", "Weather Alerts"],
            screens=screens,
            navigation_flow=["Splash -> BottomNav (Home, Search, Saved) -> Detail Screen"],
            api_requirements=apis,
            data_models=models
        )

    @classmethod
    def _build_finance_spec(cls, app_id: str, app_name: str, analyzed: Dict[str, Any]) -> ApplicationSpecification:
        screens = [
            {"id": "splash_screen", "name": "SplashScreen", "purpose": "App branding & session check", "route": "/splash", "is_primary": False},
            {"id": "login_screen", "name": "LoginScreen", "purpose": "Secure account login", "route": "/login", "is_primary": False},
            {"id": "dashboard_screen", "name": "DashboardScreen", "purpose": "Net balance, total income/expenses & recent transactions", "route": "/dashboard", "is_primary": True},
            {"id": "analytics_screen", "name": "AnalyticsScreen", "purpose": "Category breakdown & monthly spend charts", "route": "/analytics", "is_primary": True},
            {"id": "add_tx_screen", "name": "AddTransactionScreen", "purpose": "Form to record new income or expense entry", "route": "/add_tx", "is_primary": False},
            {"id": "cards_screen", "name": "CardsScreen", "purpose": "Manage linked bank accounts & credit cards", "route": "/cards", "is_primary": True},
            {"id": "profile_screen", "name": "ProfileScreen", "purpose": "Budget limits & security settings", "route": "/profile", "is_primary": True}
        ]

        apis = [
            {"method": "POST", "endpoint": "/api/auth/login", "description": "Authenticate user", "auth_required": False},
            {"method": "GET", "endpoint": "/api/health", "description": "Backend health check", "auth_required": False},
            {"method": "GET", "endpoint": "/api/expenses", "description": "Fetch all transaction entries", "auth_required": True},
            {"method": "POST", "endpoint": "/api/expenses", "description": "Create new transaction entry", "auth_required": True},
            {"method": "DELETE", "endpoint": "/api/expenses/:id", "description": "Delete transaction entry", "auth_required": True}
        ]

        models = [
            {"name": "TransactionModel", "fields": ["id", "title", "category", "type", "amount", "date", "note"]},
            {"name": "AccountModel", "fields": ["id", "name", "type", "balance", "accountNumberLast4"]}
        ]

        return ApplicationSpecification(
            app_id=app_id,
            app_name=app_name,
            domain="expense",
            app_purpose=f"Financial management & expense tracking app with spending analytics",
            target_users=["Personal Finance Users", "Small Business Owners"],
            database_requirement="JSON File Store (`data/expense_store.json`)",
            authentication_requirement="JWT Token Authentication",
            core_features=["Balance Overview", "Income & Expense Logging", "Category Analytics", "Recent Transactions List", "Account Cards"],
            secondary_features=["Monthly Budget Target", "Export PDF/CSV", "Biometric Lock"],
            screens=screens,
            navigation_flow=["Splash -> Login -> BottomNav (Dashboard, Analytics, Cards, Profile) -> Add Transaction Modal"],
            api_requirements=apis,
            data_models=models
        )

    @classmethod
    def _build_ecommerce_spec(cls, app_id: str, app_name: str, analyzed: Dict[str, Any]) -> ApplicationSpecification:
        screens = [
            {"id": "splash_screen", "name": "SplashScreen", "purpose": "App branding & catalog sync", "route": "/splash", "is_primary": False},
            {"id": "login_screen", "name": "LoginScreen", "purpose": "User login", "route": "/login", "is_primary": False},
            {"id": "catalog_screen", "name": "CatalogScreen", "purpose": "Featured product grid, categories & promo banners", "route": "/catalog", "is_primary": True},
            {"id": "detail_screen", "name": "ProductDetailScreen", "purpose": "Product image gallery, specs, reviews & Add to Cart button", "route": "/product/detail", "is_primary": False},
            {"id": "cart_screen", "name": "CartScreen", "purpose": "Shopping cart items, total breakdown & checkout button", "route": "/cart", "is_primary": True},
            {"id": "orders_screen", "name": "OrdersScreen", "purpose": "Order history & live shipment tracking", "route": "/orders", "is_primary": True},
            {"id": "profile_screen", "name": "ProfileScreen", "purpose": "Shipping addresses & saved payment methods", "route": "/profile", "is_primary": True}
        ]

        apis = [
            {"method": "GET", "endpoint": "/api/products", "description": "Fetch product catalog", "auth_required": False},
            {"method": "GET", "endpoint": "/api/cart", "description": "Fetch shopping cart items", "auth_required": True},
            {"method": "POST", "endpoint": "/api/cart", "description": "Add product to cart", "auth_required": True},
            {"method": "POST", "endpoint": "/api/orders", "description": "Checkout & place order", "auth_required": True}
        ]

        models = [
            {"name": "ProductModel", "fields": ["id", "title", "price", "category", "rating", "imageUrl", "description"]},
            {"name": "CartItemModel", "fields": ["product", "quantity", "selectedSize"]}
        ]

        return ApplicationSpecification(
            app_id=app_id,
            app_name=app_name,
            domain="product",
            app_purpose=f"Commercial e-commerce store with catalog, shopping cart & order checkout",
            target_users=["Online Shoppers"],
            database_requirement="JSON File Store (`data/product_store.json`)",
            authentication_requirement="JWT Token Authentication",
            core_features=["Product Catalog Grid", "Category Filters", "Product Details View", "Shopping Cart", "Checkout & Orders"],
            secondary_features=["Wishlist", "Rating & Reviews", "Promo Codes"],
            screens=screens,
            navigation_flow=["Splash -> Login -> BottomNav (Catalog, Cart, Orders, Profile) -> Product Detail"],
            api_requirements=apis,
            data_models=models
        )

    @classmethod
    def _build_task_spec(cls, app_id: str, app_name: str, analyzed: Dict[str, Any]) -> ApplicationSpecification:
        screens = [
            {"id": "splash_screen", "name": "SplashScreen", "purpose": "App branding & auth state check", "route": "/splash", "is_primary": False},
            {"id": "login_screen", "name": "LoginScreen", "purpose": "User credentials login & token retrieval", "route": "/login", "is_primary": False},
            {"id": "dashboard_screen", "name": "DashboardScreen", "purpose": "Overview task summary metrics, today's tasks & quick create shortcut", "route": "/dashboard", "is_primary": True},
            {"id": "task_list_screen", "name": "TaskListScreen", "purpose": "All tasks list with Riverpod filtering, priority badges, completion checkboxes & swipe actions", "route": "/tasks", "is_primary": True},
            {"id": "search_screen", "name": "SearchScreen", "purpose": "Search tasks by title, description & category", "route": "/search", "is_primary": True},
            {"id": "categories_screen", "name": "CategoriesScreen", "purpose": "Task category & project boards management", "route": "/categories", "is_primary": True},
            {"id": "task_detail_screen", "name": "TaskDetailScreen", "purpose": "Detailed task view, status toggle & action buttons", "route": "/task/detail", "is_primary": False},
            {"id": "create_task_screen", "name": "CreateTaskScreen", "purpose": "Form to create new task with due date, priority & category", "route": "/task/create", "is_primary": False},
            {"id": "edit_task_screen", "name": "EditTaskScreen", "purpose": "Form to edit existing task details", "route": "/task/edit", "is_primary": False},
            {"id": "profile_screen", "name": "ProfileScreen", "purpose": "Productivity statistics, user avatar & app settings", "route": "/profile", "is_primary": True}
        ]

        apis = [
            {"method": "POST", "endpoint": "/api/auth/login", "description": "Authenticate user & return JWT token", "auth_required": False},
            {"method": "GET", "endpoint": "/api/health", "description": "Backend health check status", "auth_required": False},
            {"method": "GET", "endpoint": "/api/tasks", "description": "Fetch user tasks with search & category filters", "auth_required": True},
            {"method": "GET", "endpoint": "/api/tasks/:id", "description": "Fetch single task by ID", "auth_required": True},
            {"method": "POST", "endpoint": "/api/tasks", "description": "Create new task", "auth_required": True},
            {"method": "PUT", "endpoint": "/api/tasks/:id", "description": "Update existing task fields", "auth_required": True},
            {"method": "PATCH", "endpoint": "/api/tasks/:id/status", "description": "Update task completion status", "auth_required": True},
            {"method": "DELETE", "endpoint": "/api/tasks/:id", "description": "Delete task by ID", "auth_required": True},
            {"method": "GET", "endpoint": "/api/categories", "description": "Fetch task categories list", "auth_required": True},
            {"method": "POST", "endpoint": "/api/categories", "description": "Create new task category", "auth_required": True}
        ]

        models = [
            {"name": "TaskModel", "fields": ["id", "title", "description", "status", "priority", "dueDate", "createdAt", "updatedAt", "categoryId", "projectId", "assignedUserId"]},
            {"name": "CategoryModel", "fields": ["id", "name", "color", "icon", "taskCount"]},
            {"name": "UserModel", "fields": ["id", "name", "email", "avatarUrl"]}
        ]

        return ApplicationSpecification(
            app_id=app_id,
            app_name=app_name,
            domain="task",
            app_purpose=f"Production-grade productivity task manager & project organizer app with Riverpod state management",
            target_users=["Busy Professionals", "Students", "Project Managers"],
            database_requirement="JSON File Store (`data/tasks_store.json`)",
            authentication_requirement="JWT Token Authentication",
            core_features=["Dashboard Summary Metrics (Total, Pending, In Progress, Completed, Overdue)", "Riverpod Task State Management", "Task List Overview with Priority Badges", "Checkable Completion Checkboxes", "Create/Edit/Delete Task Forms", "Search & Priority/Status Filtering", "Category & Project Boards"],
            secondary_features=["Due Date Indicators", "Completion Progress Statistics", "Dark Material 3 Theme"],
            screens=screens,
            navigation_flow=["Splash -> Login -> BottomNav (Home, Tasks, Search, Categories, Profile) -> Create/Edit Task"],
            api_requirements=apis,
            data_models=models
        )

    @classmethod
    def _build_social_spec(cls, app_id: str, app_name: str, analyzed: Dict[str, Any]) -> ApplicationSpecification:
        screens = [
            {"id": "splash_screen", "name": "SplashScreen", "purpose": "App branding", "route": "/splash", "is_primary": False},
            {"id": "login_screen", "name": "LoginScreen", "purpose": "User login", "route": "/login", "is_primary": False},
            {"id": "feed_screen", "name": "FeedScreen", "purpose": "Social activity feed with posts, likes & comments", "route": "/feed", "is_primary": True},
            {"id": "create_post_screen", "name": "CreatePostScreen", "purpose": "Create post form with image attachment", "route": "/post/create", "is_primary": False},
            {"id": "notifications_screen", "name": "NotificationsScreen", "purpose": "Like, comment & follow notifications", "route": "/notifications", "is_primary": True},
            {"id": "profile_screen", "name": "ProfileScreen", "purpose": "User profile, follower counts & personal posts grid", "route": "/profile", "is_primary": True}
        ]

        apis = [
            {"method": "GET", "endpoint": "/api/posts", "description": "Fetch social feed posts", "auth_required": True},
            {"method": "POST", "endpoint": "/api/posts", "description": "Publish new post", "auth_required": True},
            {"method": "POST", "endpoint": "/api/posts/like", "description": "Like post", "auth_required": True}
        ]

        models = [
            {"name": "PostModel", "fields": ["id", "authorName", "authorAvatar", "content", "imageUrl", "likesCount", "commentsCount", "createdAt"]}
        ]

        return ApplicationSpecification(
            app_id=app_id,
            app_name=app_name,
            domain="social",
            app_purpose=f"Social networking application with live activity feed & post sharing",
            target_users=["Social Media Users"],
            database_requirement="JSON File Store (`data/social_store.json`)",
            authentication_requirement="JWT Token Authentication",
            core_features=["Social Activity Feed", "Post Creation", "Like & Comment Interaction", "Notifications", "User Profile Grid"],
            secondary_features=["Follow Users", "Dark Theme Feed"],
            screens=screens,
            navigation_flow=["Splash -> Login -> BottomNav (Feed, Notifications, Profile) -> Create Post"],
            api_requirements=apis,
            data_models=models
        )

    @classmethod
    def _build_generic_spec(cls, app_id: str, app_name: str, domain: str, analyzed: Dict[str, Any]) -> ApplicationSpecification:
        cap_domain = domain.capitalize()
        screens = [
            {"id": "splash_screen", "name": "SplashScreen", "purpose": "App branding & auth check", "route": "/splash", "is_primary": False},
            {"id": "login_screen", "name": "LoginScreen", "purpose": "User authentication", "route": "/login", "is_primary": False},
            {"id": "dashboard_screen", "name": "DashboardScreen", "purpose": f"Overview summary metrics & recent {domain} records", "route": "/dashboard", "is_primary": True},
            {"id": f"{domain}_list_screen", "name": f"{cap_domain}ListScreen", "purpose": f"Browse & filter all {domain} entries", "route": f"/{domain}/list", "is_primary": True},
            {"id": f"add_{domain}_screen", "name": f"Add{cap_domain}Screen", "purpose": f"Create or edit {domain} record", "route": f"/{domain}/add", "is_primary": False},
            {"id": "profile_screen", "name": "ProfileScreen", "purpose": "User profile & settings", "route": "/profile", "is_primary": True}
        ]

        apis = [
            {"method": "POST", "endpoint": "/api/auth/login", "description": "Authenticate user", "auth_required": False},
            {"method": "GET", "endpoint": "/api/health", "description": "Backend health status", "auth_required": False},
            {"method": "GET", "endpoint": f"/api/{domain}s", "description": f"Fetch {domain} records", "auth_required": True},
            {"method": "POST", "endpoint": f"/api/{domain}s", "description": f"Create {domain} record", "auth_required": True},
            {"method": "DELETE", "endpoint": f"/api/{domain}s/:id", "description": f"Delete {domain} record", "auth_required": True}
        ]

        models = [
            {"name": f"{cap_domain}ItemModel", "fields": ["id", "title", "description", "category", "amount", "status", "createdAt"]}
        ]

        return ApplicationSpecification(
            app_id=app_id,
            app_name=app_name,
            domain=domain,
            app_purpose=f"Production-ready mobile application for {app_name}",
            target_users=["End Users"],
            database_requirement=f"JSON File Store (`data/{domain}_store.json`)",
            authentication_requirement="JWT Token Authentication",
            core_features=[f"Overview Dashboard for {app_name}", f"Full {cap_domain} Management", "Add & Edit Records", "Live Node.js API Integration", "User Settings"],
            secondary_features=["Filter & Sort Records", "Dark Modern Theme"],
            screens=screens,
            navigation_flow=[f"Splash -> Login -> BottomNav (Dashboard, {cap_domain} List, Profile) -> Add Screen"],
            api_requirements=apis,
            data_models=models
        )
