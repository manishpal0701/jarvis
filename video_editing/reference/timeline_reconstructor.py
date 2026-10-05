"""
video_editing/reference/timeline_reconstructor.py
Phase 6 Timeline Reconstructor Engine.
Reconstructs a structural timeline template from reference video shot boundaries,
pacing curves, and narrative sections (intro, build-up, drop, outro).
"""

from typing import Dict, List, Any


class TimelineReconstructor:
    """
    Builds a structural timeline template matching reference shot types, durations, and rhythm.
    """

    @classmethod
    def reconstruct_timeline_template(cls, ref_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Creates timeline structural template from reference analysis.
        """
        print("[TIMELINE_RECONSTRUCTION_START]", flush=True)

        general = ref_analysis.get("general", {})
        rhythm = ref_analysis.get("rhythm", {})
        ref_scenes = rhythm.get("scenes", [])
        total_dur = general.get("duration", 30.0)

        template_segments = []
        t = 0.0

        for idx, sc in enumerate(ref_scenes):
            seg_dur = float(sc.get("duration", 2.0))
            shot_type = sc.get("shot_type", "wide" if idx % 3 == 0 else "medium")

            # Determine pacing phase (intro: 0-15%, build-up: 15-50%, drop/climax: 50-85%, outro: 85-100%)
            progress = t / max(1.0, total_dur)
            if progress < 0.15:
                phase = "intro"
            elif progress < 0.50:
                phase = "build_up"
            elif progress < 0.85:
                phase = "drop"
            else:
                phase = "outro"

            seg = {
                "segment_id": f"seg_{idx+1}",
                "start_time": round(t, 2),
                "end_time": round(t + seg_dur, 2),
                "target_duration": round(seg_dur, 2),
                "shot_type": shot_type,
                "pacing_phase": phase,
                "motion_level": "high" if phase == "drop" else ("low" if phase in ["intro", "outro"] else "medium")
            }

            print(
                f"[TIMELINE_SEGMENT_CREATED] segment={seg['segment_id']} "
                f"start={seg['start_time']}s end={seg['end_time']}s "
                f"shot_type={seg['shot_type']} phase={seg['pacing_phase']}",
                flush=True
            )

            template_segments.append(seg)
            t += seg_dur

        print(f"[TIMELINE_RECONSTRUCTION_COMPLETE] total_segments={len(template_segments)}", flush=True)
        return template_segments
