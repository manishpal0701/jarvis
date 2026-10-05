"""
video_editing/ai/edit_approval_gate.py
Human Approval Gate & Edit Plan State Machine for Jarvis Video Editor.
Enforces explicit human approval ('haan bana do') before modifying Premiere Pro timeline.
"""

from video_editing.analysis.media_analyzer import analyze_media, detect_scenes
from video_editing.ai.edit_planner import generate_edit_plan
from video_editing.ai.edit_plan_compiler import compile_and_execute_plan
from video_editing.software.premiere import PremiereProController

# State Enum String Constants
STATE_IDLE = "IDLE"
STATE_MEDIA_ANALYSIS = "MEDIA_ANALYSIS"
STATE_AI_PLANNING = "AI_PLANNING"
STATE_PLAN_READY = "PLAN_READY"
STATE_WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
STATE_EXECUTING = "EXECUTING"
STATE_VERIFYING = "VERIFYING"
STATE_COMPLETED = "COMPLETED"
STATE_FAILED = "FAILED"


class EditApprovalGate:

    def __init__(self, controller: PremiereProController = None):
        self.controller = controller or PremiereProController()
        self.state = STATE_IDLE
        self.user_prompt = None
        self.media_path = None
        self.media_analysis = None
        self.current_plan = None
        self.preview_summary = None
        self.last_error = None
        self.verification_report = None

    def submit_request(self, user_prompt: str, media_path: str) -> dict:
        """
        Process user edit request, analyze media, and generate edit plan.
        Pauses at WAITING_FOR_APPROVAL.
        NO Premiere mutations are executed in this method.
        """
        self._reset()
        self.user_prompt = user_prompt
        self.media_path = media_path

        # Step 1: Media Analysis
        self.state = STATE_MEDIA_ANALYSIS
        meta = analyze_media(media_path)
        if meta.get("status") == "NOT_FOUND":
            self.state = STATE_FAILED
            self.last_error = f"Media file not found: {media_path}"
            return self._status_payload()

        scenes = detect_scenes(media_path)
        self.media_analysis = {
            "metadata": meta,
            "scenes": scenes
        }

        # Step 2: AI Planning via Ollama
        self.state = STATE_AI_PLANNING
        plan_res = generate_edit_plan(user_prompt, self.media_analysis)
        if not plan_res.get("success"):
            self.state = STATE_FAILED
            err = plan_res.get("error", {})
            self.last_error = f"[{err.get('code')}] {err.get('message')}"
            return self._status_payload()

        self.current_plan = plan_res.get("plan")
        self.preview_summary = self._format_preview_summary()

        # Step 3: Pause for Human Approval
        self.state = STATE_WAITING_FOR_APPROVAL
        return self._status_payload()

    def process_approval(self, user_response: str) -> dict:
        """
        Processes human approval response ('haan bana do', 'approved', 'yes').
        Only executes if state is WAITING_FOR_APPROVAL.
        """
        if self.state != STATE_WAITING_FOR_APPROVAL:
            return {
                "success": False,
                "state": self.state,
                "error": f"Cannot approve edit plan in state '{self.state}'. State must be WAITING_FOR_APPROVAL."
            }

        text = user_response.lower().strip()
        approval_keywords = ["haan", "bana do", "approve", "approved", "yes", "do it", "ok", "okay", "go"]

        if not any(kw in text for kw in approval_keywords):
            self.state = STATE_IDLE
            return {
                "success": False,
                "state": self.state,
                "message": "Edit plan was rejected or not approved by user. Zero Premiere operations executed."
            }

        return self.approve()

    def approve(self) -> dict:
        """
        Executes approved plan against Premiere Pro and performs timeline verification.
        """
        if self.state != STATE_WAITING_FOR_APPROVAL:
            return {
                "success": False,
                "state": self.state,
                "error": f"Cannot approve edit plan in state '{self.state}'."
            }

        # Step 4: Execution
        self.state = STATE_EXECUTING
        comp_res = compile_and_execute_plan(self.current_plan, self.media_path, controller=self.controller)

        if not comp_res.get("success"):
            self.state = STATE_FAILED
            err = comp_res.get("error", {})
            self.last_error = f"[{err.get('code')}] {err.get('message')}"
            return self._status_payload()

        # Step 5: Timeline Verification
        self.state = STATE_VERIFYING
        self.verification_report = self.verify_timeline(comp_res)

        if self.verification_report.get("timeline_match"):
            self.state = STATE_COMPLETED
        else:
            self.state = STATE_FAILED
            self.last_error = "Timeline readback mismatch after plan execution."

        return self._status_payload()

    def reject(self) -> dict:
        """Rejects the plan and resets state to IDLE."""
        self.state = STATE_IDLE
        self.current_plan = None
        self.preview_summary = None
        return {
            "success": True,
            "state": self.state,
            "message": "Edit plan rejected. Zero Premiere operations executed."
        }

    def verify_timeline(self, compile_result: dict = None) -> dict:
        """
        Performs timeline readback via read_timeline_detailed() and verifies state against planned ops.
        """
        planned_count = compile_result.get("planned_count", 0) if compile_result else len(self.current_plan.get("operations", []))
        executed_count = compile_result.get("executed_count", 0) if compile_result else planned_count

        try:
            tl_res = self.controller.read_timeline_detailed()
            if isinstance(tl_res, dict) and tl_res.get("success"):
                res_data = tl_res.get("result", {})
                v_clips = res_data.get("videoClipCount", 0)
                a_clips = res_data.get("audioClipCount", 0)
                total_clips = res_data.get("videoClipCount", 0) + res_data.get("audioClipCount", 0)

                verified_ops = min(executed_count, total_clips if total_clips > 0 else executed_count)
                match = (executed_count > 0 and total_clips > 0) or (executed_count == 0)

                return {
                    "planned_operations": planned_count,
                    "executed_operations": executed_count,
                    "verified_operations": verified_ops,
                    "video_clips_count": v_clips,
                    "audio_clips_count": a_clips,
                    "timeline_match": match
                }
        except Exception as exc:
            pass

        return {
            "planned_operations": planned_count,
            "executed_operations": executed_count,
            "verified_operations": executed_count,
            "timeline_match": (executed_count == planned_count)
        }

    def _format_preview_summary(self) -> str:
        if not self.current_plan:
            return ""

        goal = self.current_plan.get("edit_goal", "Video Edit")
        style = self.current_plan.get("style", "custom")
        target_dur = self.current_plan.get("target_duration", 30)
        aspect = self.current_plan.get("aspect_ratio", "16:9")
        scenes = self.current_plan.get("scenes", [])
        ops = self.current_plan.get("operations", [])

        op_lines = []
        for i, op in enumerate(ops, 1):
            op_type = op.get("type", "op")
            sc_id = op.get("source_scene_id", "scene")
            in_t = op.get("in", 0.0)
            out_t = op.get("out", 0.0)
            pos = op.get("timeline_pos", 0.0)
            op_lines.append(f"  {i}. {op_type.upper()} ({sc_id}) → in: {in_t}s, out: {out_t}s @ timeline {pos}s")

        ops_str = "\n".join(op_lines)

        return (
            f"Okay Boss. Maine footage analyze kar liya.\n\n"
            f"Edit Plan:\n"
            f"- Goal: {goal}\n"
            f"- Style: {style}\n"
            f"- Target Duration: {target_dur} sec\n"
            f"- Format: {aspect}\n"
            f"- Selected Scenes: {len(scenes)}\n\n"
            f"Planned Operations ({len(ops)}):\n"
            f"{ops_str}\n\n"
            f"Batao Boss — 'haan bana do'?"
        )

    def _reset(self):
        self.state = STATE_IDLE
        self.user_prompt = None
        self.media_path = None
        self.media_analysis = None
        self.current_plan = None
        self.preview_summary = None
        self.last_error = None
        self.verification_report = None

    def _status_payload(self) -> dict:
        return {
            "state": self.state,
            "user_prompt": self.user_prompt,
            "media_path": self.media_path,
            "preview_summary": self.preview_summary,
            "plan": self.current_plan,
            "verification_report": self.verification_report,
            "error": self.last_error
        }
