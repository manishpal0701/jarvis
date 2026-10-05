"""
core/task_orchestrator.py
Central thread-safe TaskOrchestrator singleton.
Tracks active task execution state (WEBSITE_BUILD, CODE_GENERATION, etc.),
provides structured telemetry logs for sleep suppression guards,
and generates natural human-like progress summaries for status queries.
"""

import time
import threading
import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class TaskInfo:
    task_id: str = ""
    task_type: str = ""  # WEBSITE_BUILD, CODE_GENERATION, PROJECT_MODIFICATION, WEBSITE_HOST
    description: str = ""
    stage: str = "INIT"  # PLANNING, GENERATING_FILES, VALIDATING_DEPENDENCIES, BUILDING_PRODUCTION, STARTING_PREVIEW, VISUAL_QA, COMPLETED, FAILED
    current_item: str = ""
    completed_items: List[str] = field(default_factory=list)
    total_items: int = 0
    status: str = "RUNNING"  # RUNNING, COMPLETED, FAILED
    last_error: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

class TaskOrchestrator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TaskOrchestrator, cls).__new__(cls)
                cls._instance._active_task: Optional[TaskInfo] = None
                cls._instance._last_completed_task: Optional[TaskInfo] = None
            return cls._instance

    @classmethod
    def get_instance(cls):
        return cls()

    def start_task(self, task_id: str, task_type: str, description: str, total_items: int = 0) -> TaskInfo:
        with self._lock:
            task = TaskInfo(
                task_id=task_id,
                task_type=task_type,
                description=description,
                stage="PLANNING",
                total_items=total_items,
                status="RUNNING",
                start_time=time.time()
            )
            self._active_task = task
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            print(f"[TASK_SLEEP_GUARD] task_id={task_id} active=true timestamp={now}", flush=True)

            try:
                from core.progress_reporter import ProgressReporter
                ProgressReporter.get_instance().report(
                    f"Boss, main {description.lower()} start kar raha hu.",
                    request_id=task_id,
                    stage="PLANNING",
                    speak=True
                )
            except Exception:
                pass
            return task

    def update_progress(self, task_id: str, stage: str, current_item: str = "", completed_item: str = ""):
        with self._lock:
            if self._active_task and self._active_task.task_id == task_id:
                self._active_task.stage = stage
                if current_item:
                    self._active_task.current_item = current_item
                if completed_item and completed_item not in self._active_task.completed_items:
                    self._active_task.completed_items.append(completed_item)

                try:
                    from core.progress_reporter import ProgressReporter
                    msg = ""
                    if stage in ("GENERATING_FILES", "WRITING_CODE"):
                        file_name = current_item.split('/')[-1] if current_item else "files"
                        msg = f"Boss, main {file_name} create kar raha hu."
                    elif stage == "VALIDATING_DEPENDENCIES":
                        msg = "Boss, dependencies validate kar raha hu."
                    elif stage == "BUILDING_PRODUCTION":
                        msg = "Boss, production build start kar raha hu."
                    elif stage == "STARTING_PREVIEW":
                        msg = "Boss, preview server connect kar raha hu."
                    elif stage == "REPAIRING":
                        msg = "Boss, layout issue fix karke dobara test kar raha hu."
                    
                    if msg:
                        ProgressReporter.get_instance().report(msg, request_id=task_id, stage=stage, speak=True)
                except Exception:
                    pass

    def complete_task(self, task_id: str, result_summary: str = ""):
        with self._lock:
            if self._active_task and self._active_task.task_id == task_id:
                self._active_task.status = "COMPLETED"
                self._active_task.stage = "COMPLETED"
                self._active_task.end_time = time.time()
                self._last_completed_task = self._active_task
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                print(f"[TASK_SLEEP_GUARD] task_id={task_id} active=false status=COMPLETED timestamp={now}", flush=True)
                print(f"[VOICE_LISTEN_RESUMED] timestamp={now}", flush=True)
                self._active_task = None

                try:
                    from core.progress_reporter import ProgressReporter
                    ProgressReporter.get_instance().report(
                        "Boss, kaam complete ho gaya.",
                        request_id=task_id,
                        stage="COMPLETED",
                        speak=True
                    )
                except Exception:
                    pass

    def fail_task(self, task_id: str, error_message: str = ""):
        with self._lock:
            if self._active_task and self._active_task.task_id == task_id:
                self._active_task.status = "FAILED"
                self._active_task.stage = "FAILED"
                self._active_task.last_error = error_message
                self._active_task.end_time = time.time()
                self._last_completed_task = self._active_task
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                print(f"[TASK_SLEEP_GUARD] task_id={task_id} active=false status=FAILED timestamp={now}", flush=True)
                print(f"[VOICE_LISTEN_RESUMED] timestamp={now}", flush=True)
                self._active_task = None

                try:
                    from core.progress_reporter import ProgressReporter
                    ProgressReporter.get_instance().report(
                        "Boss, task fail ho gaya. Main error check kar raha hu.",
                        request_id=task_id,
                        stage="FAILED",
                        speak=True
                    )
                except Exception:
                    pass

    def is_task_active(self) -> bool:
        with self._lock:
            return self._active_task is not None and self._active_task.status == "RUNNING"

    def get_active_task(self) -> Optional[TaskInfo]:
        with self._lock:
            return self._active_task

    def get_natural_progress_summary(self) -> str:
        with self._lock:
            task = self._active_task
            recent_task = self._last_completed_task if not task else None

        if not task and not recent_task:
            print("[TASK_STATUS_QUERY] task_id=none active=false", flush=True)
            res = "Boss, abhi koi active task nahi chal raha hai."
            print(f"[TASK_STATUS_RESPONSE] stage=NONE progress=IDLE response=\"{res}\"", flush=True)
            return res

        target_task = task or recent_task
        print(f"[TASK_STATUS_QUERY] task_id={target_task.task_id} active={target_task.status == 'RUNNING'}", flush=True)

        if target_task.status == "FAILED":
            err = target_task.last_error or "Build step fail hua hai"
            res = f"Boss, website generation mein issue aaya hai. {err[:60]}, main error details check kar raha hoon."
            print(f"[TASK_STATUS_RESPONSE] stage=FAILED progress=ERROR response=\"{res}\"", flush=True)
            return res

        if target_task.status == "COMPLETED":
            res = "Boss, website completely ready aur verified hai! Preview live chal raha hai."
            print(f"[TASK_STATUS_RESPONSE] stage=COMPLETED progress=100% response=\"{res}\"", flush=True)
            return res

        # Task is actively RUNNING
        stage = target_task.stage
        current_item = target_task.current_item
        completed_items = target_task.completed_items

        if stage == "RESEARCHING":
            res = "Boss, company ki basic information research kar raha hoon. Uske according website structure plan ho raha hai."
        elif stage == "PLANNING":
            res = "Boss, structure ready kiya ja raha hai. Files generate hone waali hain."
        elif stage in ("GENERATING_FILES", "WRITING_CODE"):
            if completed_items:
                last_few = [c.split('/')[-1] for c in completed_items[-2:]]
                items_str = " aur ".join(last_few)
                curr_name = current_item.split('/')[-1] if current_item else "next file"
                res = f"Boss, abhi {items_str} complete ho gaye hain. {curr_name} par kaam chal raha hai. Build abhi baaki hai."
            elif current_item:
                curr_name = current_item.split('/')[-1]
                res = f"Boss, structure ready hai aur ab UI file {curr_name} generate ho rahi hai."
            else:
                res = "Boss, structure ready hai aur ab UI files generate ho rahi hain."
        elif stage == "VALIDATING_DEPENDENCIES":
            res = "Boss, files generate ho chuki hain. Dependency validation check chal raha hai."
        elif stage == "BUILDING_PRODUCTION":
            res = "Boss, files generate ho chuki hain. Ab npm build chal raha hai. Build successful hote hi preview ready kar dunga."
        elif stage == "STARTING_PREVIEW":
            res = "Boss, website almost ready hai. Build complete ho gaya hai, bas preview verification chal rahi hai."
        elif stage == "VISUAL_QA":
            res = "Boss, website build complete ho gaya hai, ab Visual QA aur responsive checks verify ho rahe hain."
        elif stage == "REPAIRING":
            if "visual" in str(current_item).lower() or "qa" in str(current_item).lower() or "layout" in str(current_item).lower():
                res = "Boss, website build ho gayi thi lekin QA mein ek mobile layout issue mila. Usko fix karke dobara test kar raha hoon."
            else:
                res = "Boss, ek build error mila tha. Relevant component fix kar raha hoon, uske baad rebuild aur QA dobara chalega."
        elif stage == "VALIDATING_REPAIR":
            res = "Boss, auto-repair apply ho gaya hai. Ab rebuild aur validation gates dobara check ho rahe hain."
        else:
            res = f"Boss, {target_task.task_type.lower().replace('_', ' ')} chal raha hai. Production build verification baaki hai."

        print(f"[TASK_STATUS_RESPONSE] stage={stage} progress={len(completed_items)}/{target_task.total_items} response=\"{res}\"", flush=True)
        return res
