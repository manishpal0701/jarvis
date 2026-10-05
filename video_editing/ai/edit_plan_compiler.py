"""
video_editing/ai/edit_plan_compiler.py
Edit Plan Compiler for Jarvis Video Editor.
Translates validated edit plans into standard Phase 1 PremiereProController commands.
"""

from video_editing.software.premiere import PremiereProController


def compile_and_execute_plan(edit_plan: dict, media_path: str, controller: PremiereProController = None) -> dict:
    """
    Translates a validated edit plan into Phase 1 Premiere commands.
    Executes each operation cleanly and collects structured results.
    Returns:
      {"success": True, "planned_count": N, "executed_count": N, "executed_operations": [...], "error": None}
    """
    if controller is None:
        controller = PremiereProController()

    if not edit_plan or not isinstance(edit_plan, dict):
        return _err("INVALID_PLAN", "edit_plan must be a valid plan dictionary.")

    operations = edit_plan.get("operations", [])
    if not isinstance(operations, list) or len(operations) == 0:
        return _err("NO_OPERATIONS", "edit_plan contains no operations to compile.")

    # Step 1: Ensure Premiere project & sequence are open
    try:
        controller.ensure_project_open("Jarvis_AI_Edit")
        controller.ensure_sequence("Master_Edit")
    except Exception as e:
        return _err("PREMIERE_UNAVAILABLE", f"Could not initialize Premiere Pro session: {e}")

    # Step 2: Import media asset if provided
    if media_path:
        try:
            controller.import_clip(media_path)
        except Exception as e:
            # Continue if asset is already imported
            pass

    executed = []
    failed_op = None

    # Step 3: Map operations to Phase 1 methods
    for idx, op in enumerate(operations):
        op_type = str(op.get("type", "")).lower()
        track_type = str(op.get("track_type", "video")).lower()
        track_index = int(op.get("track_index", 0))
        timeline_pos = float(op.get("timeline_pos", 0.0))

        res = None
        try:
            if op_type in ["place_video", "overwrite"]:
                res = controller.place_video_clip(media_path, timeline_pos, track_index=track_index, overwrite=True)

            elif op_type == "place_audio":
                res = controller.place_audio_clip(media_path, timeline_pos, track_index=track_index, overwrite=True)

            elif op_type == "insert":
                res = controller.insert_clip(media_path, timeline_pos, track_type=track_type, track_index=track_index)

            elif op_type == "trim":
                in_time = float(op["in"]) if "in" in op and op["in"] is not None else None
                out_time = float(op["out"]) if "out" in op and op["out"] is not None else None
                clip_idx = int(op.get("clip_index", 0))
                res = controller.trim_clip(track_type, track_index, clip_idx, in_time=in_time, out_time=out_time)

            elif op_type == "move":
                clip_idx = int(op.get("clip_index", 0))
                new_pos = float(op.get("new_pos", timeline_pos))
                res = controller.move_clip(track_type, track_index, clip_idx, new_pos=new_pos)

            elif op_type == "split":
                clip_idx = int(op.get("clip_index", 0))
                split_time = float(op.get("split_time", op.get("in", 0.0)))
                res = controller.split_clip(track_type, track_index, clip_idx, split_time=split_time)

            elif op_type == "delete":
                clip_idx = int(op.get("clip_index", 0))
                ripple = bool(op.get("ripple", False))
                res = controller.delete_clip(track_type, track_index, clip_idx, ripple=ripple)

            elif op_type == "transition":
                t_type = str(op.get("transition_type", "cut"))
                dur = float(op.get("duration", 1.0))
                clip_idx = int(op.get("clip_index", 0))
                res = controller.apply_transition(track_type, track_index, clip_idx, transition_type=t_type, duration=dur)

            elif op_type == "visual_effect":
                eff_name = str(op.get("effect_name", "opacity"))
                val = float(op.get("value", 100.0))
                clip_idx = int(op.get("clip_index", 0))
                res = controller.set_visual_effect(track_type, track_index, clip_idx, effect_name=eff_name, value=val)

            elif op_type == "align_audio_beat":
                beat_t = float(op.get("beat_time", 0.0))
                res = controller.align_audio_to_beat(media_path, beat_t, timeline_pos, track_index=track_index)

            elif op_type == "move_audio":
                clip_idx = int(op.get("clip_index", 0))
                new_pos = float(op.get("new_pos", timeline_pos))
                res = controller.move_audio_clip(track_index, clip_idx, new_pos)

            elif op_type == "trim_audio":
                in_time = float(op["in"]) if "in" in op and op["in"] is not None else None
                out_time = float(op["out"]) if "out" in op and op["out"] is not None else None
                clip_idx = int(op.get("clip_index", 0))
                res = controller.trim_audio_clip(track_index, clip_idx, in_time=in_time, out_time=out_time)

            elif op_type == "delete_audio":
                clip_idx = int(op.get("clip_index", 0))
                ripple = bool(op.get("ripple", False))
                res = controller.delete_audio_clip(track_index, clip_idx, ripple=ripple)

            else:
                return _err("UNSUPPORTED_OPERATION", f"Operation type '{op_type}' is not supported by compiler.")

            # Record result
            executed.append({
                "op_index": idx,
                "type": op_type,
                "result": res
            })

            # Check for error in response
            if isinstance(res, dict) and res.get("success") is False:
                failed_op = res.get("error", {}).get("message", "Operation execution failed")
                break

        except Exception as exc:
            return _err("EXECUTION_FAILED", f"Operation {idx} ('{op_type}') failed: {exc}")

    if failed_op:
        return {
            "success": False,
            "planned_count": len(operations),
            "executed_count": len(executed),
            "executed_operations": executed,
            "error": {
                "code": "OPERATION_FAILED",
                "message": failed_op
            }
        }

    return {
        "success": True,
        "planned_count": len(operations),
        "executed_count": len(executed),
        "executed_operations": executed,
        "error": None
    }


def _err(code: str, message: str) -> dict:
    return {
        "success": False,
        "planned_count": 0,
        "executed_count": 0,
        "executed_operations": [],
        "error": {
            "code": code,
            "message": message
        }
    }
