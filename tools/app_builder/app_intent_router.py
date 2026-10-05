"""
tools/app_builder/app_intent_router.py
Intent detection engine for identifying mobile app creation requests.
"""
import re


class AppIntentRouter:
    """
    Classifies whether a user prompt represents an APP_BUILD request.
    Identifies explicit creation commands, domain-specific app titles (e.g. Music Player, Expense Manager),
    and multi-feature detailed application briefs.
    """

    APP_BUILD_KEYWORDS = [
        "app bana do",
        "app banao",
        "app create karo",
        "create an app",
        "create app",
        "build app",
        "build an app",
        "make an app",
        "make app",
        "flutter app",
        "android app",
        "mobile app",
        "mobile application",
        "ek app",
        "ek mobile application",
        "app bana dena",
        "application bana do",
        "attendance app",
        "shopping app",
        "expense tracker app",
        "expense manager app",
        "music player app",
        "spotify app",
        "chat app",
        "todo app",
        "task manager app"
    ]

    APP_BUILD_PATTERNS = [
        # Explicit app creation imperatives
        r"\b(bana|banaa)\s*(do|banao)?\s+.*(app|application)\b",
        r"\b(app|application)\s+(bana|banaa|create|build|make)\b",
        r"\b(create|build|make|develop|generate)\s+.*(android|flutter|mobile|ios)\s*(app|application|project)?\b",
        r"\b(ek|a)\s+.*(app|application)\s+(bana|create|build|make)\b",
        r"\b(app\s+bana\s+do|app\s+banao|create\s+an?\s+app|build\s+me\s+an?\s+app)\b",
        # Domain specific creation (e.g. "Create a Spotify-style music player", "Build an expense manager")
        r"\b(create|build|make|bana|banaa|develop)\s+(?:a|an)?\s+.*(music player|expense manager|expense tracker|attendance|shopping|ecommerce|e-commerce|chat|todo|task manager|social media|fitness tracker|news|delivery|notes|weather)\b",
        r"\b(music player|expense manager|expense tracker|attendance|shopping|ecommerce|chat|todo)\s+(app|application|system|project)\b"
    ]

    APP_FEATURE_INDICATORS = [
        "login", "auth", "home screen", "search", "playlists", "liked songs",
        "recently played", "queue", "shuffle", "repeat", "categories", "album pages",
        "artist pages", "backend", "node.js", "rest api", "database", "flutter",
        "android", "dashboard", "transactions", "categories", "playback state"
    ]

    @classmethod
    def is_app_build_intent(cls, command: str) -> bool:
        if not command:
            return False
        cmd_lower = command.lower().strip()

        # Simple datetime query guard (e.g. "what time is it")
        strict_dt_exact = ["what time is it", "what is the time", "current time", "what is today's date", "what is the date"]
        if cmd_lower in strict_dt_exact:
            return False

        # 1. Check explicit keywords
        for kw in cls.APP_BUILD_KEYWORDS:
            if kw in cmd_lower:
                return True

        # 2. Check regex patterns
        for pat in cls.APP_BUILD_PATTERNS:
            if re.search(pat, cmd_lower):
                return True

        # 3. Structural / Multi-feature brief check
        # e.g., "Create a Spotify-style music player with login, home screen, search, playlists..."
        creation_verbs = ["create", "build", "make", "bana", "banaa", "develop", "generate"]
        has_creation_verb = any(re.search(r"\b" + verb + r"\b", cmd_lower) for verb in creation_verbs)
        
        if has_creation_verb:
            feature_count = sum(1 for feat in cls.APP_FEATURE_INDICATORS if feat in cmd_lower)
            if feature_count >= 2:
                return True

        return False

