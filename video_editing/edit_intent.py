"""
video_editing/edit_intent.py
Phase 5 Structured Edit Intent Parser Module.
Parses natural language user editing requests into a clean, deterministic schema.
Explicitly represents missing requirements as UNKNOWN or NOT_AVAILABLE.
"""

import re
from typing import Dict, Any

VALUE_UNKNOWN = "UNKNOWN"
VALUE_NOT_AVAILABLE = "NOT_AVAILABLE"


class EditIntentParser:
    """
    Parses natural language edit requests into structured EditIntent specifications.
    """

    @classmethod
    def parse_intent(cls, command: str) -> Dict[str, Any]:
        """
        Parses command string into structured EditIntent dict.
        """
        if not command or not isinstance(command, str):
            cmd = ""
        else:
            cmd = command.lower().strip()

        print("[EDIT_INTENT]\nstatus=PARSING", flush=True)

        # 1. Edit Type
        if "cinematic" in cmd:
            edit_type = "cinematic_reel"
        elif "montage" in cmd or "combine" in cmd:
            edit_type = "montage"
        elif "beat" in cmd or "sync" in cmd:
            edit_type = "beat_sync"
        elif "reel" in cmd or "short" in cmd:
            edit_type = "reel"
        else:
            edit_type = "standard_edit"

        # 2. Target Duration parsing (e.g., "30 second", "15 sec", "1 min")
        target_duration = None
        dur_match = re.search(r"\b(\d+)\s*(second|sec|s|min|minute)s?\b", cmd)
        if dur_match:
            val = float(dur_match.group(1))
            unit = dur_match.group(2)
            if "min" in unit:
                target_duration = val * 60.0
            else:
                target_duration = val
        elif "reel" in cmd or "short" in cmd:
            target_duration = 30.0 # Standard social media default if unstated

        # 3. Platform & Aspect Ratio / Resolution
        platform = VALUE_UNKNOWN
        aspect_ratio = VALUE_UNKNOWN
        output_resolution = VALUE_UNKNOWN

        if "instagram" in cmd or "insta" in cmd or "reel" in cmd:
            platform = "instagram"
            aspect_ratio = "9:16"
            output_resolution = "1080x1920"
        elif "youtube short" in cmd or "shorts" in cmd:
            platform = "youtube_shorts"
            aspect_ratio = "9:16"
            output_resolution = "1080x1920"
        elif "tiktok" in cmd:
            platform = "tiktok"
            aspect_ratio = "9:16"
            output_resolution = "1080x1920"
        elif "youtube" in cmd or "landscape" in cmd or "16:9" in cmd:
            platform = "youtube"
            aspect_ratio = "16:9"
            output_resolution = "1920x1080"

        # 4. Pacing
        if "fast" in cmd or "quick" in cmd or "dynamic" in cmd:
            pacing = "fast"
        elif "slow" in cmd or "smooth" in cmd:
            pacing = "slow"
        else:
            pacing = "medium"

        # 5. Transition Style
        if "crossfade" in cmd or "dissolve" in cmd:
            transition_style = "dissolve"
        elif "cut" in cmd or "hard cut" in cmd:
            transition_style = "cut"
        else:
            transition_style = "dynamic"

        # 6. Music & Text Requirements
        music_req = True if any(k in cmd for k in ["music", "song", "audio", "beat"]) else VALUE_NOT_AVAILABLE
        text_req = True if any(k in cmd for k in ["text", "title", "caption", "subtitle"]) else VALUE_NOT_AVAILABLE

        # Construct final dict
        intent_data = {
            "edit_type": edit_type,
            "target_duration": target_duration if target_duration is not None else VALUE_UNKNOWN,
            "aspect_ratio": aspect_ratio,
            "output_resolution": output_resolution,
            "pacing": pacing,
            "transition_style": transition_style,
            "music_requirement": music_req,
            "text_requirement": text_req,
            "preferred_sections": VALUE_NOT_AVAILABLE,
            "platform": platform,
            "special_instructions": command
        }

        print(
            f"[EDIT_INTENT]\n"
            f"status=COMPLETE\n"
            f"edit_type={edit_type}\n"
            f"target_duration={intent_data['target_duration']}\n"
            f"aspect_ratio={aspect_ratio}\n"
            f"platform={platform}",
            flush=True
        )

        return intent_data


def parse_edit_intent(command: str) -> Dict[str, Any]:
    """Convenience functional wrapper for EditIntentParser."""
    return EditIntentParser.parse_intent(command)
