"""
video_editing/export/export_presets.py
Predefined Render Presets for Jarvis Video Editor Phase 4.
Supports INSTAGRAM_REEL, YOUTUBE_SHORT, YOUTUBE, LANDSCAPE, and CUSTOM presets.
"""

PRESET_INSTAGRAM_REEL = "INSTAGRAM_REEL"
PRESET_YOUTUBE_SHORT = "YOUTUBE_SHORT"
PRESET_YOUTUBE = "YOUTUBE"
PRESET_LANDSCAPE = "LANDSCAPE"
PRESET_CUSTOM = "CUSTOM"

PRESETS = {
    PRESET_INSTAGRAM_REEL: {
        "preset_name": PRESET_INSTAGRAM_REEL,
        "format": "mp4",
        "codec": "h264",
        "resolution": "1080x1920",
        "fps": 30,
        "audio_enabled": True
    },
    PRESET_YOUTUBE_SHORT: {
        "preset_name": PRESET_YOUTUBE_SHORT,
        "format": "mp4",
        "codec": "h264",
        "resolution": "1080x1920",
        "fps": 30,
        "audio_enabled": True
    },
    PRESET_YOUTUBE: {
        "preset_name": PRESET_YOUTUBE,
        "format": "mp4",
        "codec": "h264",
        "resolution": "1920x1080",
        "fps": 30,
        "audio_enabled": True
    },
    PRESET_LANDSCAPE: {
        "preset_name": PRESET_LANDSCAPE,
        "format": "mp4",
        "codec": "h264",
        "resolution": "1920x1080",
        "fps": 30,
        "audio_enabled": True
    }
}


def get_preset_config(preset_name: str, output_path: str, custom_override: dict = None, overwrite: bool = False) -> dict:
    """
    Build complete export configuration payload for given preset name and output path.
    """
    p_name = str(preset_name or PRESET_CUSTOM).upper().strip()

    if p_name in PRESETS:
        base = dict(PRESETS[p_name])
    else:
        base = {
            "preset_name": PRESET_CUSTOM,
            "format": "mp4",
            "codec": "h264",
            "resolution": "1920x1080",
            "fps": 30,
            "audio_enabled": True
        }

    if custom_override and isinstance(custom_override, dict):
        base.update(custom_override)

    base["preset_name"] = p_name
    base["output_path"] = output_path
    base["overwrite"] = overwrite
    return base
