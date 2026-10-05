"""
tools/app_builder/app_brief_merger.py
Intelligent brief merging engine for incremental app requirements collection from chat messages.
"""
import re
from typing import Dict, Any, List, Optional
from tools.app_builder.app_model import AppBrief


class AppBriefMerger:
    """
    Parses and merges new client requirements into an existing AppBrief instance.
    Preserves all previously gathered information while adding or updating fields.
    """

    @staticmethod
    def merge_brief(
        existing_brief: AppBrief,
        new_text: str = "",
        references: Optional[List[Dict[str, Any]]] = None,
        images: Optional[List[str]] = None,
        raw_payload: Optional[Dict[str, Any]] = None
    ) -> AppBrief:
        if raw_payload:
            AppBriefMerger._merge_dict_payload(existing_brief, raw_payload)

        if new_text and new_text.strip():
            AppBriefMerger._merge_text_input(existing_brief, new_text.strip())

        if references:
            for ref in references:
                if ref not in existing_brief.references:
                    existing_brief.references.append(ref)

        if images:
            for img in images:
                if img not in existing_brief.images:
                    existing_brief.images.append(img)

        return existing_brief

    @staticmethod
    def _merge_dict_payload(brief: AppBrief, payload: Dict[str, Any]):
        if "name" in payload and payload["name"]:
            brief.name = payload["name"]
        if "description" in payload and payload["description"]:
            brief.description = payload["description"]
        if "authentication" in payload and payload["authentication"]:
            brief.authentication = payload["authentication"]
        if "database" in payload and payload["database"]:
            brief.database = payload["database"]

        if "technology" in payload and isinstance(payload["technology"], dict):
            brief.technology.update(payload["technology"])

        if "features" in payload and isinstance(payload["features"], list):
            for feat in payload["features"]:
                if feat and feat not in brief.features:
                    brief.features.append(feat)

        if "requirements" in payload and isinstance(payload["requirements"], list):
            for req in payload["requirements"]:
                if req and req not in brief.requirements:
                    brief.requirements.append(req)

        if "ui_ux" in payload and isinstance(payload["ui_ux"], dict):
            for k, v in payload["ui_ux"].items():
                if isinstance(v, list) and isinstance(brief.ui_ux.get(k), list):
                    for item in v:
                        if item not in brief.ui_ux[k]:
                            brief.ui_ux[k].append(item)
                else:
                    brief.ui_ux[k] = v

        if "design_preferences" in payload and isinstance(payload["design_preferences"], list):
            for pref in payload["design_preferences"]:
                if pref and pref not in brief.design_preferences:
                    brief.design_preferences.append(pref)

        if "apis" in payload and isinstance(payload["apis"], list):
            for api in payload["apis"]:
                if api and api not in brief.apis:
                    brief.apis.append(api)

        if "platforms" in payload and isinstance(payload["platforms"], list):
            for plat in payload["platforms"]:
                if plat and plat not in brief.platforms:
                    brief.platforms.append(plat)

        if "references" in payload and isinstance(payload["references"], list):
            for ref in payload["references"]:
                if ref not in brief.references:
                    brief.references.append(ref)

        if "images" in payload and isinstance(payload["images"], list):
            for img in payload["images"]:
                if img not in brief.images:
                    brief.images.append(img)

    @staticmethod
    def _merge_text_input(brief: AppBrief, text: str):
        if not text:
            return

        text_str = text.strip()
        text_lower = text_str.lower()

        # Preserve canonical full_text
        if not getattr(brief, "full_text", None):
            brief.full_text = text_str
        else:
            if text_str not in brief.full_text:
                brief.full_text += f"\n\n{text_str}"

        # 1. App Name extraction
        is_generic_name = not brief.name or brief.name in ["Mobile Application", "App", "Mobile App", "JarvisApp"]
        search_corpus = f"{text_str}\n{getattr(brief, 'full_text', '') or ''}"

        # Explicit app name pattern e.g. "App ka naam Expense Tracker hai", "App ka naam: JARVIS Music", "App Name: JARVIS Music"
        name_match = re.search(
            r"(?:^|\n|\.|\s)\s*(?:app\s+ka\s+naam|app\s+name|name\s+of\s+(?:the\s+)?app|name)\s*(?::|=|\s+is|\s+hai|\s+)\s*[\"']?([^\"'\.\,\n\r]+)[\"']?\s*(?:hai|\.|\r|\n|$)",
            search_corpus,
            re.IGNORECASE
        )

        if name_match:
            extracted_name = name_match.group(1).strip()
            extracted_name = re.sub(r"(?i)^(?:is|hai|=|:)\s+", "", extracted_name).strip()
            extracted_name = re.sub(r"(?i)\s+hai$", "", extracted_name).strip().rstrip(".")
            if extracted_name and not extracted_name.startswith("-") and len(extracted_name) < 50:
                brief.name = extracted_name
                is_generic_name = False

        if is_generic_name:
            # Domain app name regex e.g. "Create a Spotify-style music player", "Create a Music Player app"
            create_name_match = re.search(
                r"\b(?:create|build|make|bana|banaa|develop)\s+(?:a|an)?\s+([a-zA-Z0-9_\-\s]+?)(?:\s+(?:app|application|mobile project|with|having|including|for)|\.|\n|$)",
                text_str,
                re.IGNORECASE
            )
            if create_name_match:
                p_name = create_name_match.group(1).strip()
                if p_name and p_name.lower() not in ["app", "android app", "flutter app", "mobile app", "ek app"]:
                    brief.name = p_name.title()

            if not brief.name or brief.name in ["Mobile Application", "App", "Mobile App", "JarvisApp"]:
                if "spotify" in text_lower or "music" in text_lower:
                    brief.name = "JARVIS Music"
                elif "expense" in text_lower:
                    brief.name = "Expense Tracker App"
                elif "attendance" in text_lower:
                    brief.name = "Attendance App"
                elif "task" in text_lower or "todo" in text_lower:
                    brief.name = "Task Manager App"

        # 2. Features & Requirements extraction
        # Extract explicit bullet points (- , * , + , 1. , 2. )
        bullet_lines = [line.strip() for line in text_str.split("\n") if re.match(r"^\s*[\-\*\+\u2022]\s+|^\s*\d+\.\s+", line)]
        for b_line in bullet_lines:
            clean_b = re.sub(r"^\s*[\-\*\+\u2022]\s+|^\s*\d+\.\s+", "", b_line).strip()
            if clean_b and len(clean_b) > 1 and clean_b not in brief.features:
                brief.features.append(clean_b)

        # Extract comma-separated feature phrases if keywords present or standalone requirement lines
        feat_keywords = ["with", "having", "including", "features", "feature", "isme", "contains", "includes", "honi chahiye", "should have", "player", "library", "playlist", "songs", "queue", "search", "playback", "home"]
        for line in text_str.split("\n"):
            line_s = line.strip()
            line_l = line_s.lower()
            if any(kw in line_l for kw in feat_keywords) and not re.match(r"^\s*[\-\*\+\u2022]\s+|^\s*\d+\.\s+", line_s):
                clean_feat_text = re.sub(r"(?i)^(?:isme|features|feature|requirements|includes|with|having)\s*(?:hai|:|=)?\s*", "", line_s).strip()
                clean_feat_text = re.sub(r"(?i)\s*(?:feature|features|honi chahiye|hona chahiye|include karo|add karo|\.)$", "", clean_feat_text).strip()
                items = re.split(r",|\baur\b|\band\b", clean_feat_text)
                for item in items:
                    feat = item.strip()
                    feat = re.sub(r"(?i)^(login|signup|auth)\s+system", r"\1", feat)
                    feat = re.sub(r"(?i)^(?:create|build|make|add|include)\s+", "", feat).strip()
                    if feat and len(feat) > 1 and len(feat) < 80 and feat.lower() not in [f.lower() for f in brief.features]:
                        if not any(kw in feat.lower() for kw in ["jarvis", "banao", "generate", "analyze", "bana", "backend", "frontend"]):
                            brief.features.append(feat)

        # 3. Theme & Design Preferences
        if any(kw in text_lower for kw in ["theme", "color", "colour", "design", "dark", "light"]):
            if "theme" in text_lower:
                theme_match = re.search(r"([a-zA-Z0-9_\-\s]+)\s+theme", text_str, re.IGNORECASE)
                if theme_match:
                    t_val = theme_match.group(1).strip()
                    if t_val and t_val.lower() not in brief.design_preferences:
                        brief.design_preferences.append(f"{t_val} theme")
                        brief.ui_ux["theme"] = f"{t_val} theme"

        # 4. Authentication
        if "login" in text_lower or "auth" in text_lower or "firebase auth" in text_lower or "oauth" in text_lower:
            if "firebase" in text_lower:
                brief.authentication = "Firebase Auth"
            elif not brief.authentication:
                brief.authentication = "JWT / Custom Auth"

        # 5. Database
        if "database" in text_lower or "db" in text_lower or "mongodb" in text_lower or "sql" in text_lower or "sqlite" in text_lower:
            if "mongodb" in text_lower:
                brief.database = "MongoDB"
            elif "sqlite" in text_lower:
                brief.database = "SQLite"
            elif "postgres" in text_lower:
                brief.database = "PostgreSQL"
            elif not brief.database:
                brief.database = "SQLite / PostgreSQL"

        # 6. Description update
        if not brief.description:
            brief.description = text_str
        else:
            if text_str not in brief.description:
                brief.description += f" | {text_str}"

    @staticmethod
    def is_brief_sufficient(brief: AppBrief) -> tuple[bool, str]:
        """
        Determines whether sufficient information exists in the AppBrief to proceed to PLANNING.
        Returns (is_sufficient, missing_info_prompt).
        """
        if not brief:
            return False, "Boss, app ki basic requirements chat me bhej do."

        # If name is missing but description is substantial, synthesize name
        if not brief.name and brief.description and len(brief.description) > 10:
            search_corpus = f"{brief.description}\n{getattr(brief, 'full_text', '') or ''}"
            name_match = re.search(
                r"(?:^|\n|\.|\s)\s*(?:app\s+ka\s+naam|app\s+name|name\s+of\s+(?:the\s+)?app|name)\s*(?::|=|\s+is|\s+hai|\s+)\s*[\"']?([^\"'\.\,\n\r]+)[\"']?\s*(?:hai|\.|\r|\n|$)",
                search_corpus,
                re.IGNORECASE
            )
            if name_match:
                extracted = name_match.group(1).strip()
                extracted = re.sub(r"(?i)^(?:is|hai|=|:)\s+", "", extracted).strip()
                extracted = re.sub(r"(?i)\s+hai$", "", extracted).strip().rstrip(".")
                if extracted and len(extracted) < 50:
                    brief.name = extracted
                elif "music" in search_corpus.lower() or "spotify" in search_corpus.lower():
                    brief.name = "JARVIS Music"
                else:
                    brief.name = "Mobile Application"
            elif "music" in search_corpus.lower() or "spotify" in search_corpus.lower():
                brief.name = "JARVIS Music"
            else:
                brief.name = "Mobile Application"

        has_name = bool(brief.name and brief.name.strip())
        has_desc = bool(brief.description and len(brief.description.strip()) > 5)
        has_features = len(brief.features) > 0 or len(brief.requirements) > 0

        if not has_name and not has_desc:
            return False, "Boss, app ka naam aur main purpose confirm kar do."

        if not has_features:
            return False, "Boss, app me kya features chahiye wo batado."

        return True, "Brief is sufficient to proceed."


