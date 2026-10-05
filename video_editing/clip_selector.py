"""
video_editing/clip_selector.py
Phase 5 Intelligent Clip Selection Module.
Selects an optimal set of scored scenes/clips tailored to the edit intent,
target duration, quality scores, visual diversity, and duplicate avoidance.
"""

from typing import List, Dict, Any


class ClipSelector:
    """
    Selects optimal clip segments from scored scene candidates.
    """

    @classmethod
    def select_clips_for_intent(
        cls,
        scored_scenes: List[Dict[str, Any]],
        edit_intent: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Selects scenes matching target_duration and edit_intent requirements.
        
        Returns:
            List of selected scene dicts ordered for timeline placement.
        """
        print("[CLIP_SELECTION]\nstatus=STARTED", flush=True)

        if not scored_scenes:
            print("[CLIP_SELECTION]\nstatus=FAILED\nreason=no_scored_scenes", flush=True)
            return []

        target_duration = edit_intent.get("target_duration")
        if not target_duration or not isinstance(target_duration, (int, float)) or target_duration <= 0:
            target_duration = 30.0 # Default to 30s reel if unspecified

        # Filter usable non-duplicate candidates
        candidates = [s for s in scored_scenes if s.get("usable", True) and not s.get("is_duplicate", False)]

        # If usable candidates is empty, fall back to top scored candidates
        if not candidates:
            candidates = sorted(scored_scenes, key=lambda x: x.get("score", 0), reverse=True)

        # Sort candidates primarily by score descending
        candidates.sort(key=lambda x: x.get("score", 0.0), reverse=True)

        selected = []
        accumulated_duration = 0.0

        # Diversity tracking: avoid overusing a single video file
        file_counts: Dict[str, int] = {}

        for item in candidates:
            if accumulated_duration >= target_duration:
                break

            f_path = item.get("file_path", "")
            f_count = file_counts.get(f_path, 0)

            # Cap clips per file if we have multiple files available
            unique_files_count = len(set(c.get("file_path") for c in candidates))
            if unique_files_count > 1 and f_count >= max(2, len(candidates) // unique_files_count + 1):
                continue

            dur = item.get("duration", 0.0)
            remaining = target_duration - accumulated_duration

            # If segment duration exceeds remaining target by a lot, trim segment length
            selected_dur = min(dur, remaining)
            if selected_dur < 1.0 and accumulated_duration > 0:
                continue

            scene_copy = dict(item)
            scene_copy["selected_duration"] = round(selected_dur, 2)
            scene_copy["trim_in"] = item.get("start", 0.0)
            scene_copy["trim_out"] = round(item.get("start", 0.0) + selected_dur, 2)

            selected.append(scene_copy)
            file_counts[f_path] = f_count + 1
            accumulated_duration += selected_dur

        # Sort selected clips chronologically per file for natural story flow
        selected.sort(key=lambda x: (x.get("file_path", ""), x.get("start", 0.0)))

        print(
            f"[CLIP_SELECTION]\n"
            f"status=COMPLETE\n"
            f"selected_count={len(selected)}\n"
            f"total_selected_duration={round(accumulated_duration, 2)}s\n"
            f"target_duration={target_duration}s",
            flush=True
        )

        return selected


def select_intelligent_clips(scored_scenes: List[Dict[str, Any]], edit_intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convenience functional wrapper for ClipSelector."""
    return ClipSelector.select_clips_for_intent(scored_scenes, edit_intent)
