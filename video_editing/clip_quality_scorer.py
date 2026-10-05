"""
video_editing/clip_quality_scorer.py
Phase 5 Deterministic Clip Quality Scorer Module.
Evaluates clips/scenes using measurable metrics: sharpness/blur, exposure/brightness,
motion activity, duration suitability, and duplicate similarity penalties.
Produces explainable, structured scoring breakdowns without randomness.
"""

from typing import List, Dict, Any


class ClipQualityScorer:
    """
    Computes explainable quality scores for video scenes/clips based on physical & visual metrics.
    """

    @classmethod
    def score_scene(cls, scene: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scores a single scene object.
        
        Returns:
            {
                "scene_id": str,
                "score": float,  # normalized 0.0 to 1.0
                "breakdown": {
                    "sharpness": float,
                    "exposure": float,
                    "motion": float,
                    "duration_suitability": float,
                    "duplicate_penalty": float
                },
                "usable": bool
            }
        """
        blur = scene.get("blur_score", 0.0)
        brightness = scene.get("brightness", 0.0)
        motion = scene.get("motion_level", 0.0)
        duration = scene.get("duration", 0.0)
        is_dup = scene.get("is_duplicate", False)

        # 1. Sharpness / Blur score (0.0 to 0.30)
        # Optimal Laplacian variance >= 100. Below 30 is blurry.
        if blur >= 150:
            sharpness_score = 0.30
        elif blur >= 50:
            sharpness_score = 0.20 + 0.10 * ((blur - 50) / 100.0)
        elif blur >= 20:
            sharpness_score = 0.10 + 0.10 * ((blur - 20) / 30.0)
        else:
            sharpness_score = 0.02

        # 2. Exposure / Lighting score (0.0 to 0.25)
        # Optimal brightness 60-200. Under 30 or over 230 is bad.
        if 80 <= brightness <= 180:
            exposure_score = 0.25
        elif 50 <= brightness < 80:
            exposure_score = 0.15 + 0.10 * ((brightness - 50) / 30.0)
        elif 180 < brightness <= 220:
            exposure_score = 0.25 - 0.10 * ((brightness - 180) / 40.0)
        else:
            exposure_score = 0.05

        # 3. Motion / Visual Activity score (0.0 to 0.25)
        # Moderate motion (5-30) is dynamic and cinematic.
        if 5.0 <= motion <= 40.0:
            motion_score = 0.25
        elif motion > 40.0:
            motion_score = 0.18 # Too shaky or high motion
        elif 1.0 <= motion < 5.0:
            motion_score = 0.15 # Static shot
        else:
            motion_score = 0.10

        # 4. Duration suitability score (0.0 to 0.20)
        # Ideal clip duration for editing is 2.0s to 12.0s.
        if 2.5 <= duration <= 10.0:
            dur_score = 0.20
        elif 1.0 <= duration < 2.5:
            dur_score = 0.10 + 0.10 * ((duration - 1.0) / 1.5)
        elif 10.0 < duration <= 30.0:
            dur_score = 0.15
        else:
            dur_score = 0.05

        # 5. Duplicate penalty
        dup_penalty = 0.30 if is_dup else 0.0

        raw_total = sharpness_score + exposure_score + motion_score + dur_score - dup_penalty
        final_score = round(max(0.0, min(1.0, raw_total)), 3)

        usable = (final_score >= 0.35) and (not is_dup) and (duration >= 1.0)

        return {
            "scene_id": scene.get("scene_id", "unknown"),
            "file_path": scene.get("file_path"),
            "filename": scene.get("filename"),
            "start": scene.get("start", 0.0),
            "end": scene.get("end", 0.0),
            "duration": duration,
            "score": final_score,
            "breakdown": {
                "sharpness": round(sharpness_score, 3),
                "exposure": round(exposure_score, 3),
                "motion": round(motion_score, 3),
                "duration_suitability": round(dur_score, 3),
                "duplicate_penalty": round(dup_penalty, 3)
            },
            "usable": usable
        }

    @classmethod
    def score_all_scenes(cls, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scores all scenes and logs telemetry.
        """
        print("[CLIP_SCORING]\nstatus=STARTED", flush=True)
        scored = [cls.score_scene(s) for s in scenes]

        # Sort descending by score
        scored.sort(key=lambda x: x["score"], reverse=True)

        usable_count = sum(1 for s in scored if s["usable"])
        print(f"[CLIP_SCORING]\nstatus=COMPLETE\ntotal_scored={len(scored)}\nusable={usable_count}", flush=True)

        return scored


def score_clips(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convenience wrapper for ClipQualityScorer."""
    return ClipQualityScorer.score_all_scenes(scenes)
