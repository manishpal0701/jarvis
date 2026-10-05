"""
video_editing/reference/auto_refinement_engine.py
Phase 7 Autonomous Iterative Refinement Engine.
Identifies specific weak sub-score metrics when STYLE_SIMILARITY_SCORE < 85%,
applies targeted adjustments, and halts when score reaches >= 85%, when max iterations (3)
are reached, or when score improvement delta is < 2.0%.
"""

from typing import Dict, Any, List, Tuple


class AutoRefinementEngine:
    """
    Manages automated targeted refinement loop to maximize STYLE_SIMILARITY_SCORE.
    """

    MAX_REFINEMENT_ITERATIONS = 3
    TARGET_SIMILARITY_SCORE = 85.0
    MIN_IMPROVEMENT_DELTA = 2.0

    @classmethod
    def refine_edit_plan_if_needed(
        cls,
        edit_plan: Dict[str, Any],
        comparison_res: Dict[str, Any],
        current_iteration: int = 1,
        prev_score: float = 0.0
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Refines edit plan parameters if similarity score is under 85% and iteration cap is not exceeded.
        Returns tuple: (refined_edit_plan, should_rerender).
        """
        score_num = comparison_res.get("similarity_score_num", 0.0)
        sub_scores = comparison_res.get("sub_scores", {})
        delta = score_num - prev_score if current_iteration > 1 else 10.0

        pacing_val = float(sub_scores.get("SHOT_PACING_SCORE", "80%").rstrip("%"))
        beat_val = float(sub_scores.get("BEAT_SYNC_SCORE", "80%").rstrip("%"))
        trans_val = float(sub_scores.get("TRANSITION_SCORE", "80%").rstrip("%"))
        motion_val = float(sub_scores.get("MOTION_SCORE", "80%").rstrip("%"))
        color_val = float(sub_scores.get("COLOR_SCORE", "80%").rstrip("%"))
        framing_val = float(sub_scores.get("FRAMING_SCORE", "80%").rstrip("%"))

        print(
            f"[REFINEMENT_ANALYSIS] pacing_score={int(pacing_val)} beat_sync_score={int(beat_val)} "
            f"transition_score={int(trans_val)} motion_score={int(motion_val)} "
            f"color_score={int(color_val)} framing_score={int(framing_val)}",
            flush=True
        )
        print(f"[REFINEMENT_SCORE] iteration={current_iteration} similarity_score={score_num}% delta={delta:.1f}%", flush=True)

        if score_num >= cls.TARGET_SIMILARITY_SCORE:
            print(f"[REFINEMENT_STOP] reason=TARGET_SCORE_REACHED score={score_num}% >= {cls.TARGET_SIMILARITY_SCORE}%", flush=True)
            return edit_plan, False

        if current_iteration > cls.MAX_REFINEMENT_ITERATIONS:
            print(f"[REFINEMENT_STOP] reason=MAX_ITERATIONS_REACHED limit={cls.MAX_REFINEMENT_ITERATIONS}", flush=True)
            return edit_plan, False

        if current_iteration > 1 and delta < cls.MIN_IMPROVEMENT_DELTA:
            print(f"[REFINEMENT_STOP] reason=PLATEAU_DETECTED delta={delta:.1f}% < {cls.MIN_IMPROVEMENT_DELTA}%", flush=True)
            return edit_plan, False

        print(
            f"[AUTO_REFINEMENT_START] iteration={current_iteration} "
            f"current_score={score_num}% target={cls.TARGET_SIMILARITY_SCORE}%",
            flush=True
        )

        operations = edit_plan.get("operations", [])
        weakest_target = "NONE"

        # Apply targeted refinement to weakest metric
        if pacing_val < 80.0 and operations:
            weakest_target = "PACING"
            for op in operations:
                cur_dur = op.get("duration", 2.0)
                adj_dur = max(0.8, cur_dur * 0.9)
                op["duration"] = round(adj_dur, 2)
                op["source_end"] = round(op["source_start"] + adj_dur, 2)
                op["out"] = op["source_end"]

        elif beat_val < 80.0:
            weakest_target = "BEAT_SYNC"
            edit_plan["beat_sync_strength"] = "strict"
            for op in operations:
                op["beat_sync"] = True

        elif color_val < 80.0:
            weakest_target = "COLOR"
            edit_plan["color_grading_preset"] = "CINEMATIC_WARM_ENHANCED"

        elif motion_val < 80.0:
            weakest_target = "MOTION"
            edit_plan["motion_profile"] = "dynamic_push"

        else:
            weakest_target = "GENERAL_PACING"
            for op in operations:
                op["duration"] = round(max(0.8, op.get("duration", 2.0) * 0.95), 2)

        print(f"[REFINEMENT_TARGET] metric={weakest_target} score={score_num}%", flush=True)
        print(f"[REFINEMENT_APPLIED] target={weakest_target} ops_modified={len(operations)}", flush=True)
        print(f"[AUTO_REFINEMENT_ADJUSTED] iteration={current_iteration} ops_adjusted={len(operations)}", flush=True)

        return edit_plan, True
