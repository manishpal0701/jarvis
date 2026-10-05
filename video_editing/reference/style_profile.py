"""
video_editing/reference/style_profile.py
Phase 6 Professional Reference Style Profile Generator.
Compiles comprehensive reference analysis findings into a structured ReferenceStyleProfile dict.
"""

from typing import Dict, Any


class StyleProfileGenerator:
    """
    Generates dynamic ReferenceStyleProfile containing all 14 Phase 6 editing language parameters.
    """

    @classmethod
    def generate_profile(cls, ref_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates structured ReferenceStyleProfile.
        """
        rhythm = ref_analysis.get("rhythm", {})
        visual = ref_analysis.get("visual", {})
        motion = ref_analysis.get("motion", {})
        audio = ref_analysis.get("audio", {})
        general = ref_analysis.get("general", {})

        avg_dur = rhythm.get("avg_shot_duration", 2.0)
        cut_freq = rhythm.get("cut_frequency", "medium")
        pace = "fast" if avg_dur < 1.8 else ("slow" if avg_dur > 3.5 else "medium")

        profile = {
            "pacing": pace,
            "average_shot_duration": round(avg_dur, 2),
            "shot_duration_distribution": rhythm.get("shot_duration_distribution", [avg_dur]),
            "cut_frequency": cut_freq,
            "pacing_curve": "accelerating" if pace == "fast" else "steady",
            "transition_language": "crossfade" if pace == "slow" else "hard_cut",
            "motion_profile": motion.get("camera_motion", "smooth"),
            "zoom_profile": motion.get("zoom_profile", "subtle_push"),
            "speed_ramp_profile": "frequent" if pace == "fast" else "subtle",
            "color_profile": visual.get("color_style", "cinematic_warm"),
            "audio_energy_curve": audio.get("energy_curve", "medium"),
            "beat_sync_strength": "strong" if audio.get("has_audio") else "flexible",
            "text_style": "minimal_title",
            "framing_style": general.get("aspect_ratio", "9:16")
        }

        print(
            f"[REFERENCE_STYLE_PROFILE]\n"
            f"pacing={profile['pacing']} "
            f"avg_shot_dur={profile['average_shot_duration']}s "
            f"cut_freq={profile['cut_frequency']} "
            f"trans={profile['transition_language']} "
            f"color={profile['color_profile']} "
            f"motion={profile['motion_profile']}",
            flush=True
        )

        return profile
