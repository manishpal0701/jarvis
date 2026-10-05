"""
video_editing/reference/reference_preset.py
Phase 6 Professional Reference Editing Preset.
Defines the ReferenceEditingPreset data structure bridging reference analysis and rendering execution.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ReferenceEditingPreset:
    """
    ReferenceEditingPreset holds all configured editing language rules and parameters
    derived from a reference video.
    """
    target_duration: float = 30.0
    pacing: str = "medium"
    shot_distribution: List[float] = field(default_factory=lambda: [2.0, 2.0, 2.0])
    cut_frequency: str = "medium"
    transition_style: str = "hard_cut"
    motion_style: str = "smooth"
    speed_ramp_style: str = "subtle"
    zoom_style: str = "subtle_push"
    color_style: str = "cinematic_warm"
    music_style: str = "medium"
    beat_sync_strength: str = "strong"
    framing: str = "9:16"
    text_style: str = "minimal_title"

    @classmethod
    def from_style_profile(cls, style_profile: Dict[str, Any], target_dur: float = 30.0) -> "ReferenceEditingPreset":
        """Constructs ReferenceEditingPreset instance from ReferenceStyleProfile dict."""
        return cls(
            target_duration=target_dur,
            pacing=style_profile.get("pacing", "medium"),
            shot_distribution=style_profile.get("shot_duration_distribution", [2.0]),
            cut_frequency=style_profile.get("cut_frequency", "medium"),
            transition_style=style_profile.get("transition_language", "hard_cut"),
            motion_style=style_profile.get("motion_profile", "smooth"),
            speed_ramp_style=style_profile.get("speed_ramp_profile", "subtle"),
            zoom_style=style_profile.get("zoom_profile", "subtle_push"),
            color_style=style_profile.get("color_profile", "cinematic_warm"),
            music_style=style_profile.get("audio_energy_curve", "medium"),
            beat_sync_strength=style_profile.get("beat_sync_strength", "strong"),
            framing=style_profile.get("framing_style", "9:16"),
            text_style=style_profile.get("text_style", "minimal_title")
        )
