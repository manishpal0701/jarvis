"""
video_editing/effects/transition_engine.py
Phase 6 Professional Transition Engine.
Selects and configures reference-driven transitions (hard cut, crossfade, dip to black/white, fade, zoom).
"""

from typing import Dict, Any


class TransitionEngine:
    """
    Manages reference-driven video transitions between adjacent timeline clips.
    """

    @classmethod
    def select_transition(
        cls,
        prev_phase: str,
        curr_phase: str,
        reference_transition_style: str = "hard_cut"
    ) -> Dict[str, Any]:
        """
        Determines appropriate transition type and duration for clip boundary.
        """
        if reference_transition_style == "crossfade" or (prev_phase == "intro" and curr_phase == "build_up"):
            trans_type = "crossfade"
            dur = 1.0
        elif curr_phase == "outro":
            trans_type = "dip_to_black"
            dur = 1.2
        elif reference_transition_style == "zoom":
            trans_type = "zoom_transition"
            dur = 0.5
        else:
            trans_type = "hard_cut"
            dur = 0.0

        print(f"[TRANSITION_APPLIED] type={trans_type} duration={dur}s", flush=True)
        return {
            "type": trans_type,
            "duration": dur
        }
