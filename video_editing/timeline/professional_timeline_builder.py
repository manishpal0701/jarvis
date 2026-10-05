"""
video_editing/timeline/professional_timeline_builder.py
Phase 7 Professional Timeline Builder Engine.
Generates structured narrative timeline sequences (INTRO, HOOK, BUILD, TRANSITION,
MAIN_SEQUENCE, PEAK/DROP, CLIMAX, OUTRO) driven by reference video blueprints and target pacing.
"""

from typing import Dict, List, Any


class ProfessionalTimelineBuilder:
    """
    Constructs professional timeline structures dynamically adapted to reference editing language.
    """

    SECTION_STRUCTURE = [
        "INTRO",
        "HOOK",
        "BUILD",
        "TRANSITION",
        "MAIN_SEQUENCE",
        "PEAK_DROP",
        "CLIMAX",
        "OUTRO"
    ]

    @classmethod
    def build_professional_timeline(cls, ref_blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Creates a structured timeline specification from reference blueprint.
        """
        print("[TIMELINE_BUILD_START]", flush=True)

        dur_prof = ref_blueprint.get("duration_profile", {})
        pacing_prof = ref_blueprint.get("pacing_profile", {})
        ref_scenes = ref_blueprint.get("shot_structure", [])

        target_total_dur = float(dur_prof.get("total_duration", 30.0))
        pacing_style = pacing_prof.get("pacing_style", "MODERATE")
        avg_shot_dur = float(dur_prof.get("avg_shot_duration", 2.0))

        # Adjust section breakdown based on reference style
        if pacing_style == "FAST_ACTION" or len(ref_scenes) >= 6:
            shot_count = max(6, len(ref_scenes))
            shot_duration = max(0.8, min(1.8, avg_shot_dur))
        elif pacing_style == "SLOW_CINEMATIC" or len(ref_scenes) <= 2:
            shot_count = max(2, len(ref_scenes))
            shot_duration = max(3.5, avg_shot_dur)
        else:
            shot_count = max(4, len(ref_scenes))
            shot_duration = max(1.8, avg_shot_dur)

        timeline_shots = []
        curr_t = 0.0

        for idx in range(shot_count):
            section_name = cls.SECTION_STRUCTURE[idx % len(cls.SECTION_STRUCTURE)]
            shot_id = f"shot_{idx+1}"
            dur = round(shot_duration, 2)
            end_t = round(curr_t + dur, 2)

            # Determine motion & transition parameters per section
            if section_name in ["HOOK", "PEAK_DROP", "CLIMAX"]:
                motion_level = "high"
                trans_type = "whip_zoom" if pacing_style == "FAST_ACTION" else "crossfade"
            elif section_name == "INTRO":
                motion_level = "low"
                trans_type = "fade_in"
            elif section_name == "OUTRO":
                motion_level = "low"
                trans_type = "dip_to_black"
            else:
                motion_level = "medium"
                trans_type = "hard_cut"

            shot_spec = {
                "shot_id": shot_id,
                "section": section_name,
                "start_time": curr_t,
                "end_time": end_t,
                "target_duration": dur,
                "motion_level": motion_level,
                "transition_type": trans_type,
                "pacing_phase": section_name.lower()
            }

            print(
                f"[TIMELINE_SECTION_CREATED] section={section_name} "
                f"start={curr_t}s end={end_t}s duration={dur}s",
                flush=True
            )
            print(
                f"[TIMELINE_SHOT_PLACED] shot_id={shot_id} section={section_name} "
                f"motion={motion_level} transition={trans_type}",
                flush=True
            )

            timeline_shots.append(shot_spec)
            curr_t = end_t

        print(f"[TIMELINE_BUILD_COMPLETE] total_shots={len(timeline_shots)} total_duration={curr_t}s", flush=True)
        return timeline_shots
