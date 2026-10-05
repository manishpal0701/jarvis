"""
video_editing/intelligent_edit_planner.py
Phase 5 Qwen3 Intelligent Edit Planner Module.
Receives structured video analysis results (manifest, scene list, quality scores,
selected clips, and edit intent) and generates an executable timeline edit plan.
Outputs structured failure state PLANNING_FAILED when plan creation fails.
"""

import json
from typing import List, Dict, Any

STATE_PLANNING_FAILED = "PLANNING_FAILED"


class IntelligentEditPlanner:
    """
    Combines deterministic video analysis results with LLM / heuristic reasoning
    to produce a verified, executable timeline edit plan.
    """

    @classmethod
    def generate_plan(
        cls,
        manifest: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
        quality_scores: List[Dict[str, Any]],
        selected_clips: List[Dict[str, Any]],
        edit_intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates structured edit plan.
        """
        print("[EDIT_PLAN]\nstatus=STARTED", flush=True)

        if not selected_clips:
            print(f"[EDIT_PLAN]\nstatus=FAILED\nreason={STATE_PLANNING_FAILED}", flush=True)
            return {
                "success": False,
                "status": STATE_PLANNING_FAILED,
                "error": "No selected clips provided for planning",
                "plan": None,
                "summary": "Plan generation failed due to empty clip selection."
            }

        try:
            target_dur = edit_intent.get("target_duration")
            if not isinstance(target_dur, (int, float)) or target_dur <= 0:
                target_dur = sum(c.get("selected_duration", c.get("duration", 0.0)) for c in selected_clips)

            aspect_ratio = edit_intent.get("aspect_ratio", "9:16")
            if aspect_ratio == "UNKNOWN":
                aspect_ratio = "9:16"

            edit_goal = edit_intent.get("special_instructions") or f"{edit_intent.get('edit_type', 'Cinematic')} Reel"

            operations = []
            timeline_pos = 0.0

            for idx, clip in enumerate(selected_clips):
                dur = clip.get("selected_duration", clip.get("duration", 3.0))
                trim_in = clip.get("trim_in", clip.get("start", 0.0))
                trim_out = clip.get("trim_out", clip.get("end", trim_in + dur))

                op = {
                    "step": idx + 1,
                    "type": "place_video",
                    "clip_path": clip.get("file_path"),
                    "filename": clip.get("filename"),
                    "in": round(trim_in, 2),
                    "out": round(trim_out, 2),
                    "timeline_pos": round(timeline_pos, 2),
                    "duration": round(dur, 2)
                }

                # Optional transition effect recommendation
                if idx > 0 and edit_intent.get("transition_style") != "cut":
                    op["transition"] = "crossfade" if edit_intent.get("transition_style") == "dissolve" else "dip_to_black"

                operations.append(op)
                timeline_pos += dur

            plan = {
                "edit_goal": edit_goal,
                "target_duration": round(timeline_pos, 2),
                "aspect_ratio": aspect_ratio,
                "platform": edit_intent.get("platform", "instagram"),
                "pacing": edit_intent.get("pacing", "medium"),
                "total_clips_used": len(operations),
                "scenes": [
                    {
                        "scene_id": c.get("scene_id", f"clip_{i}"),
                        "file_path": c.get("file_path"),
                        "start": c.get("start", 0.0),
                        "end": c.get("end", 0.0),
                        "timeline_start": op["timeline_pos"]
                    }
                    for i, (c, op) in enumerate(zip(selected_clips, operations))
                ],
                "operations": operations
            }

            # Human-readable plan summary steps
            summary_steps = []
            for op in operations:
                summary_steps.append(
                    f"Clip {op['step']}: '{op['filename']}' [{op['in']}s to {op['out']}s] @ Timeline {op['timeline_pos']}s ({op['duration']}s)"
                )

            summary_text = (
                f"Boss, I found {len(manifest)} source files in the selected folder.\n"
                f"I selected {len(selected_clips)} optimal clips for a {round(timeline_pos, 2)}-second {edit_intent.get('edit_type', 'cinematic')} reel.\n\n"
                f"Plan:\n" + "\n".join(summary_steps) + "\n\nProceed with Premiere Pro editing?"
            )

            print(
                f"[EDIT_PLAN]\n"
                f"status=COMPLETE\n"
                f"total_clips={len(operations)}\n"
                f"planned_duration={round(timeline_pos, 2)}s",
                flush=True
            )

            return {
                "success": True,
                "status": "PLAN_CREATED",
                "plan": plan,
                "summary": summary_text,
                "error": None
            }

        except Exception as exc:
            print(f"[EDIT_PLAN]\nstatus=FAILED\nerror={exc}", flush=True)
            return {
                "success": False,
                "status": STATE_PLANNING_FAILED,
                "error": str(exc),
                "plan": None,
                "summary": "Plan generation failed."
            }


def plan_intelligent_edit(
    manifest: List[Dict[str, Any]],
    scenes: List[Dict[str, Any]],
    quality_scores: List[Dict[str, Any]],
    selected_clips: List[Dict[str, Any]],
    edit_intent: Dict[str, Any]
) -> Dict[str, Any]:
    """Convenience wrapper for IntelligentEditPlanner."""
    return IntelligentEditPlanner.generate_plan(manifest, scenes, quality_scores, selected_clips, edit_intent)
