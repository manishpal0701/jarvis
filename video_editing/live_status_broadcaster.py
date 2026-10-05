"""
video_editing/live_status_broadcaster.py
Phase 6 Live Telemetry Broadcaster & Workspace Status Panel Generator.
Emits real-time editing status events and updates the synchronized
Jarvis Video Agent Workspace Status Panel.
"""

import json
from typing import Dict, Any, Optional

# Telemetry Event Names
EVENT_PREMIERE_STARTED = "premiere_started"
EVENT_PREMIERE_READY = "premiere_ready"
EVENT_MEDIA_IMPORT_STARTED = "media_import_started"
EVENT_MEDIA_IMPORT_COMPLETED = "media_import_completed"
EVENT_SEQUENCE_CREATED = "sequence_created"
EVENT_EDIT_OPERATION_STARTED = "edit_operation_started"
EVENT_EDIT_OPERATION_COMPLETED = "edit_operation_completed"
EVENT_PREMIERE_STATE_VERIFIED = "premiere_state_verified"
EVENT_EXPORT_STARTED = "export_started"
EVENT_EXPORT_PROGRESS = "export_progress"
EVENT_EXPORT_COMPLETED = "export_completed"
EVENT_VERIFICATION_STARTED = "verification_started"
EVENT_VERIFICATION_COMPLETED = "verification_completed"
EVENT_VIDEO_COMPLETE = "video_complete"
EVENT_VIDEO_FAILED = "video_failed"


class LiveStatusBroadcaster:
    """
    Broadcasts real-time events and renders the Jarvis Video Agent Status Panel.
    """

    def __init__(self, speaker_func=None):
        self.speaker_func = speaker_func
        self.events_log = []

    def broadcast(self, event_name: str, payload: Optional[Dict[str, Any]] = None):
        """
        Emits a structured status event to console/telemetry streams.
        """
        data = payload or {}
        event_obj = {
            "event": event_name,
            "data": data
        }
        self.events_log.append(event_obj)
        print(f"[STATUS_EVENT]\nevent={event_name}\npayload={json.dumps(data)}", flush=True)

        try:
            from api.websocket.jarvis import broadcast_sync
            broadcast_sync({
                "type": "video_progress",
                "stage": event_name,
                "data": data
            })
        except Exception:
            pass

    def render_workspace_panel(
        self,
        premiere_connected: bool,
        project_name: str,
        current_operation: str,
        active_pipeline_stage: str,
        render_progress: Optional[str] = None
    ) -> str:
        """
        Renders the ASCII Workspace Status Panel.
        Uses pure ASCII characters to prevent Windows console encoding crashes.
        """
        status_dot = "[CONNECTED]" if premiere_connected else "[DISCONNECTED]"
        proj = project_name or "Jarvis_Edit"

        stages = [
            ("Source Analysis", "source_analysis"),
            ("Clip Selection", "clip_selection"),
            ("Edit Plan", "edit_plan"),
            ("Media Import", "media_import"),
            ("Sequence Creation", "sequence_creation"),
            ("Timeline Editing", "timeline_editing"),
            ("Transitions", "transitions"),
            ("Audio", "audio"),
            ("Subtitles", "subtitles"),
            ("Export", "export"),
            ("Verification", "verification")
        ]

        pipeline_lines = []
        found_active = False

        for label, stage_key in stages:
            if stage_key == active_pipeline_stage:
                pipeline_lines.append(f"| -> {label:<22} |")
                found_active = True
            elif not found_active:
                pipeline_lines.append(f"| v  {label:<22} |")
            else:
                pipeline_lines.append(f"| o  {label:<22} |")

        pipeline_str = "\n".join(pipeline_lines)
        progress_line = f"| Render: {render_progress:<20} |\n" if render_progress else ""

        panel = (
            f"+-------------------------------------+\n"
            f"| JARVIS VIDEO AGENT                  |\n"
            f"+-------------------------------------+\n"
            f"| Premiere Pro: {status_dot:<17} |\n"
            f"| Project: {proj:<24} |\n"
            f"|                                     |\n"
            f"| CURRENT OPERATION                   |\n"
            f"| Edit: {current_operation:<23} |\n"
            f"|                                     |\n"
            f"| PIPELINE                            |\n"
            f"{pipeline_str}\n"
            f"{progress_line}"
            f"+-------------------------------------+"
        )

        return panel
