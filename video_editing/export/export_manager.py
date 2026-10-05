"""
video_editing/export/export_manager.py
Natural Export Intent Parser & Export Configuration Manager for Phase 4.
"""

import os
from video_editing.export.export_presets import (
    PRESET_INSTAGRAM_REEL,
    PRESET_YOUTUBE_SHORT,
    PRESET_YOUTUBE,
    PRESET_LANDSCAPE,
    PRESET_CUSTOM,
    get_preset_config
)
from video_editing.export.export_schema import validate_export_config


def parse_export_intent(user_text: str) -> str:
    """
    Parses user request text to deduce the intended export preset.
    Examples:
      'Instagram ke liye export karo' -> INSTAGRAM_REEL
      'YouTube short ke liye export karo' -> YOUTUBE_SHORT
      'YouTube 1080p video export karo' -> YOUTUBE
    """
    if not user_text or not isinstance(user_text, str):
        return PRESET_INSTAGRAM_REEL

    t = user_text.lower().strip()

    if "short" in t or "youtube short" in t:
        return PRESET_YOUTUBE_SHORT
    elif "reel" in t or "instagram" in t or "insta" in t:
        return PRESET_INSTAGRAM_REEL
    elif "youtube" in t:
        return PRESET_YOUTUBE
    elif "landscape" in t or "16:9" in t or "horizontal" in t:
        return PRESET_LANDSCAPE

    return PRESET_INSTAGRAM_REEL


class ExportManager:

    def __init__(self):
        self.current_config = None

    def configure_export(self, preset_name: str, output_path: str, custom_override: dict = None, overwrite: bool = False) -> dict:
        """
        Creates and validates export configuration object.
        Returns {"success": True, "config": {...}} or error dict.
        """
        cfg = get_preset_config(preset_name, output_path, custom_override=custom_override, overwrite=overwrite)
        valid, val_res = validate_export_config(cfg)
        if not valid:
            self.current_config = None
            return val_res

        self.current_config = cfg
        return {
            "success": True,
            "config": cfg,
            "error": None
        }

    def configure_from_user_request(self, user_request: str, output_path: str, overwrite: bool = False) -> dict:
        """
        Deduces preset from natural language prompt and configures export.
        """
        preset = parse_export_intent(user_request)
        return self.configure_export(preset, output_path, overwrite=overwrite)
