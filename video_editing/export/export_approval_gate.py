"""
video_editing/export/export_approval_gate.py
Human Approval Gate & Export State Machine for Phase 4 Render Pipeline.
Enforces EXPORT_STARTED = False until explicit human approval ('haan', 'export kar do').
"""

from video_editing.export.export_manager import ExportManager
from video_editing.export.export_verifier import verify_output_file
from video_editing.software.premiere import PremiereProController

STATE_IDLE = "IDLE"
STATE_EXPORT_REQUESTED = "EXPORT_REQUESTED"
STATE_EXPORT_CONFIGURED = "EXPORT_CONFIGURED"
STATE_WAITING_FOR_EXPORT_APPROVAL = "WAITING_FOR_EXPORT_APPROVAL"
STATE_EXPORTING = "EXPORTING"
STATE_RENDERING = "RENDERING"
STATE_VERIFYING_OUTPUT = "VERIFYING_OUTPUT"
STATE_COMPLETED = "COMPLETED"
STATE_EXPORT_FAILED = "EXPORT_FAILED"
STATE_CANCELLED = "CANCELLED"


class ExportApprovalGate:

    def __init__(self, controller: PremiereProController = None):
        self.controller = controller or PremiereProController()
        self.export_manager = ExportManager()
        self.state = STATE_IDLE
        self.EXPORT_STARTED = False
        self.current_config = None
        self.preview_summary = None
        self.last_error = None
        self.verification_report = None

    def request_export(self, user_prompt: str, output_path: str, custom_override: dict = None, overwrite: bool = False) -> dict:
        """
        Processes export request, builds configuration, and pauses at WAITING_FOR_EXPORT_APPROVAL.
        NO Premiere render command is executed in this method.
        """
        self._reset()
        self.state = STATE_EXPORT_REQUESTED

        cfg_res = self.export_manager.configure_from_user_request(user_prompt, output_path, overwrite=overwrite)
        if not cfg_res.get("success"):
            self.state = STATE_EXPORT_FAILED
            err = cfg_res.get("error", {})
            self.last_error = f"[{err.get('code')}] {err.get('message')}"
            return self._status_payload()

        self.current_config = cfg_res.get("config")
        self.state = STATE_EXPORT_CONFIGURED

        self.preview_summary = self._format_preview_summary()
        self.state = STATE_WAITING_FOR_EXPORT_APPROVAL
        self.EXPORT_STARTED = False

        return self._status_payload()

    def process_approval(self, user_response: str) -> dict:
        """
        Processes user approval response. Only starts export if state is WAITING_FOR_EXPORT_APPROVAL.
        """
        if self.state != STATE_WAITING_FOR_EXPORT_APPROVAL:
            return {
                "success": False,
                "state": self.state,
                "error": f"Cannot approve export in state '{self.state}'. Must be WAITING_FOR_EXPORT_APPROVAL."
            }

        text = user_response.lower().strip()
        approval_keywords = ["haan", "yes", "export karo", "export kar do", "proceed", "render karo", "ok", "okay", "bana do"]

        if not any(kw in text for kw in approval_keywords):
            self.state = STATE_CANCELLED
            self.EXPORT_STARTED = False
            return {
                "success": False,
                "state": self.state,
                "message": "Export request cancelled or not approved by user. Zero render commands sent."
            }

        return self.approve()

    def approve(self) -> dict:
        """
        Executes sequence export against Premiere Pro CEP bridge and verifies output file with ffprobe.
        """
        if self.state != STATE_WAITING_FOR_EXPORT_APPROVAL:
            return {
                "success": False,
                "state": self.state,
                "error": f"Cannot approve export in state '{self.state}'."
            }

        self.EXPORT_STARTED = True
        self.state = STATE_EXPORTING

        # Execute export on Premiere Pro
        self.state = STATE_RENDERING
        out_path = self.current_config.get("output_path")
        preset = self.current_config.get("preset_name")
        fmt = self.current_config.get("format", "mp4")
        codec = self.current_config.get("codec", "h264")
        overwrite = self.current_config.get("overwrite", False)

        exp_res = self.controller.export_sequence(
            output_path=out_path,
            preset=preset,
            format=fmt,
            codec=codec,
            overwrite=overwrite
        )

        if not exp_res.get("success"):
            self.state = STATE_EXPORT_FAILED
            err = exp_res.get("error", {})
            self.last_error = f"[{err.get('code')}] {err.get('message')}"
            return self._status_payload()

        # Verify output file
        self.state = STATE_VERIFYING_OUTPUT
        v_res = verify_output_file(out_path, expected_config=self.current_config)
        self.verification_report = v_res

        if v_res.get("success") and v_res.get("verified"):
            self.state = STATE_COMPLETED
        else:
            self.state = STATE_EXPORT_FAILED
            err = v_res.get("error", {})
            self.last_error = f"[{err.get('code')}] {err.get('message')}"

        return self._status_payload()

    def cancel_export(self) -> dict:
        """Cancels export and resets state machine."""
        self.state = STATE_CANCELLED
        self.EXPORT_STARTED = False
        return {
            "success": True,
            "state": self.state,
            "message": "Export cancelled. Zero render commands executed."
        }

    def _format_preview_summary(self) -> str:
        if not self.current_config:
            return ""

        preset = self.current_config.get("preset_name", "CUSTOM")
        res = self.current_config.get("resolution", "1080x1920")
        fmt = self.current_config.get("format", "mp4").upper()
        codec = self.current_config.get("codec", "h264").upper()
        fps = self.current_config.get("fps", 30)
        audio = "Enabled" if self.current_config.get("audio_enabled", True) else "Disabled"
        out = self.current_config.get("output_path", "")

        return (
            f"Okay Boss. Export ready hai.\n\n"
            f"Export Details:\n"
            f"- Preset: {preset}\n"
            f"- Resolution: {res}\n"
            f"- Format: {fmt}\n"
            f"- Codec: {codec}\n"
            f"- FPS: {fps}\n"
            f"- Audio: {audio}\n"
            f"- Output Path: {out}\n\n"
            f"Export start karu?"
        )

    def _reset(self):
        self.state = STATE_IDLE
        self.EXPORT_STARTED = False
        self.current_config = None
        self.preview_summary = None
        self.last_error = None
        self.verification_report = None

    def _status_payload(self) -> dict:
        return {
            "state": self.state,
            "EXPORT_STARTED": self.EXPORT_STARTED,
            "config": self.current_config,
            "preview_summary": self.preview_summary,
            "verification_report": self.verification_report,
            "error": self.last_error
        }
