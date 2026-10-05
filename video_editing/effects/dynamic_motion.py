"""
video_editing/effects/dynamic_motion.py
Phase 6 Dynamic Motion Engine.
Applies subtle camera motion (push-in, pull-out, punch-in/out, Ken Burns) based on reference motion profile.
"""

from typing import Dict, Any


class DynamicMotionEngine:
    """
    Configures dynamic camera motion and zoom effects for video clips and image assets.
    """

    @classmethod
    def apply_motion_effect(
        cls,
        asset_type: str,
        phase: str,
        reference_motion_profile: str = "smooth"
    ) -> Dict[str, Any]:
        """
        Calculates motion effect type and intensity.
        """
        if asset_type == "image":
            effect_type = "ken_burns_push"
            intensity = "medium"
        elif reference_motion_profile == "dynamic" or phase == "drop":
            effect_type = "push_in"
            intensity = "subtle"
        else:
            effect_type = "none"
            intensity = "none"

        print(f"[DYNAMIC_MOTION_APPLIED] effect={effect_type} intensity={intensity}", flush=True)
        return {
            "effect": effect_type,
            "intensity": intensity
        }
