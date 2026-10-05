"""
video_editing/effects/speed_ramp_engine.py
Phase 6 Speed Ramp Engine.
Applies motion-guided speed ramps (slow-motion, fast-forward, speed ramp in/out) matching reference pacing.
"""

from typing import Dict, Any


class SpeedRampEngine:
    """
    Manages speed ramps and slow motion settings for timeline clips.
    """

    @classmethod
    def apply_speed_ramp(
        cls,
        phase: str,
        reference_speed_profile: str = "subtle",
        base_speed: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculates clip speed factor and speed ramp mode.
        """
        if reference_speed_profile == "frequent" and phase == "drop":
            speed_factor = 1.25
            mode = "fast_section"
        elif phase == "outro":
            speed_factor = 0.85
            mode = "slow_motion"
        else:
            speed_factor = base_speed
            mode = "normal"

        print(f"[SPEED_RAMP_APPLIED] speed={speed_factor:.2f} mode={mode}", flush=True)
        return {
            "speed": round(speed_factor, 2),
            "mode": mode
        }
