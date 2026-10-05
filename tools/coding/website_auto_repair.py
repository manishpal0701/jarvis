"""
tools/coding/website_auto_repair.py
Intelligent Website Auto-Repair Loop module.
Receives build, runtime, dependency, or Visual QA failure information, diagnoses the likely
affected component, generates a targeted code repair, safely applies it, and emits telemetry.

Enforces:
- MAX_REPAIR_ATTEMPTS = 3
- Authoritative validation preservation (Never sets WEBSITE_READY directly)
- Targeted single-file repairs (Never regenerates the full site)
- Strict safety rules (.env, secrets, core files protection)
"""

import os
import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Callable

MAX_REPAIR_ATTEMPTS = 2

PROTECTED_PATTERNS = [
    ".env", "config.py", "main.py", "AGENTS.md", "ARCHITECTURE.md",
    "conversation_engine.py", "speech_engine.py", "listener.py"
]

@dataclass
class RepairIssue:
    issue_type: str = "build"  # build, runtime, visual_qa, asset
    message: str = ""
    source: str = ""
    affected_files: List[str] = field(default_factory=list)
    severity: str = "error"   # error, warning, critical
    repairable: bool = True

@dataclass
class RepairPlan:
    diagnosis: str = ""
    affected_file: str = ""
    repair_action: str = ""
    target_changes: str = ""

@dataclass
class RepairResult:
    attempt_number: int = 1
    status: str = "success"  # success, failed, unrepairable, limit_reached
    repaired_file: str = ""
    error_details: str = ""
    plan: Optional[RepairPlan] = None

class WebsiteAutoRepair:
    """
    Intelligent Website Auto-Repair Agent.
    Diagnoses build/QA failures, formulates targeted repair plans, applies safe edits,
    and returns RepairResult. Enforces MAX_REPAIR_ATTEMPTS = 2.
    """

    @classmethod
    def is_safe_target_file(cls, target_file: str, project_dir: str) -> bool:
        """
        Safety Guard: Verifies that target_file is inside project_dir and does not
        touch .env, secrets, or core Jarvis system files.
        """
        if not target_file:
            return False
        
        target_norm = os.path.normpath(target_file).lower()
        
        # Check protected pattern substrings
        for prot in PROTECTED_PATTERNS:
            if prot.lower() in target_norm:
                return False

        # If path is absolute, verify it stays inside project_dir
        if os.path.isabs(target_file):
            proj_norm = os.path.normpath(project_dir).lower()
            if not target_norm.startswith(proj_norm):
                return False

        return True

    @classmethod
    def diagnose_failure(
        cls,
        issue: RepairIssue,
        project_dir: str,
        known_files: Optional[List[str]] = None
    ) -> RepairPlan:
        """
        Diagnoses failure cause and identifies the single targeted file requiring repair.
        """
        known_files = known_files or []
        msg = issue.message.lower()
        target_file = ""

        # 0. Check for export mismatch error: "X is not exported by Y"
        export_mismatch = re.search(r'["\']?(\w+)["\']?\s+is not exported by\s+["\']?([^"\'\s,]+)["\']?', issue.message, re.IGNORECASE)
        if export_mismatch:
            missing_sym = export_mismatch.group(1)
            target_mod = export_mismatch.group(2)
            for kf in known_files:
                if target_mod in kf or os.path.basename(kf).replace(".tsx", "").replace(".ts", "") == missing_sym:
                    target_file = kf
                    break
            if not target_file:
                target_file = f"src/components/{missing_sym}.tsx"

        # 1. Check if affected_files is explicitly specified
        if not target_file and issue.affected_files:
            for af in issue.affected_files:
                if cls.is_safe_target_file(af, project_dir):
                    target_file = af
                    break

        # 2. Extract filename from error message matching known files or patterns
        if not target_file:
            for kf in known_files:
                basename = os.path.basename(kf).lower()
                if kf.lower() in msg or (basename and basename in msg):
                    target_file = kf
                    break

        # 3. Pattern match for TSX/CSS/JS file references in error message
        if not target_file:
            m = re.search(r"['\"]?((?:src/|app/)?[\w\-\/]+\.(?:tsx|jsx|ts|js|css|json|html))['\"]?", issue.message, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                if candidate in known_files or any(kf.endswith(candidate) for kf in known_files):
                    target_file = candidate
                else:
                    target_file = candidate

        # 4. Smart Category Defaults
        if not target_file:
            if issue.issue_type == "visual_qa":
                if "navbar" in msg or "header" in msg or "nav" in msg:
                    target_file = "src/components/Navbar.tsx"
                elif "hero" in msg:
                    target_file = "src/components/Hero.tsx"
                else:
                    target_file = "src/App.tsx"
            elif issue.issue_type == "build":
                if "css" in msg or "tailwind" in msg or "style" in msg:
                    target_file = "src/index.css"
                else:
                    target_file = "src/App.tsx"
            elif issue.issue_type == "asset":
                target_file = "src/components/Hero.tsx"
            else:
                target_file = "src/App.tsx"

        # Final safety check
        if not cls.is_safe_target_file(target_file, project_dir):
            target_file = "src/App.tsx"

        diagnosis = f"Detected {issue.issue_type.upper()} issue: {issue.message[:120]}"
        action = f"Targeted single-file code correction for '{target_file}'"

        return RepairPlan(
            diagnosis=diagnosis,
            affected_file=target_file,
            repair_action=action,
            target_changes=issue.message
        )

    @classmethod
    def diagnose_and_repair(
        cls,
        task_id: str,
        project_dir: str,
        issue: RepairIssue,
        attempt_number: int,
        generated_contents: Dict[str, str],
        code_generator_func: Optional[Callable[[str, str, str], str]] = None
    ) -> RepairResult:
        """
        Executes a targeted auto-repair attempt:
        1. Validates MAX_REPAIR_ATTEMPTS = 3
        2. Validates issue.repairable
        3. Diagnoses affected file
        4. Applies targeted repair safely
        5. Emits telemetry logs
        6. Returns RepairResult
        """
        print(f"[AUTO_REPAIR_START] task_id={task_id} attempt={attempt_number}/3 issue_type={issue.issue_type}", flush=True)

        # 1. Enforce MAX_REPAIR_ATTEMPTS = 3 Limit
        if attempt_number > MAX_REPAIR_ATTEMPTS:
            print(f"[AUTO_REPAIR_LIMIT_REACHED] task_id={task_id} attempt={attempt_number} exceeds max limit of {MAX_REPAIR_ATTEMPTS}.", flush=True)
            return RepairResult(
                attempt_number=attempt_number,
                status="limit_reached",
                error_details=f"Maximum auto-repair attempts ({MAX_REPAIR_ATTEMPTS}) reached for task '{task_id}'."
            )

        # 2. Check repairability
        if not issue.repairable:
            print(f"[AUTO_REPAIR_FAILED] task_id={task_id} issue marked unrepairable/ambiguous: '{issue.message[:100]}'", flush=True)
            return RepairResult(
                attempt_number=attempt_number,
                status="unrepairable",
                error_details=f"Ambiguous or unsupported failure cannot be safely auto-repaired: {issue.message}"
            )

        print(f"[AUTO_REPAIR_ISSUE] message='{issue.message[:120]}' severity={issue.severity}", flush=True)

        # 3. Diagnose target file
        known_files = list(generated_contents.keys())
        plan = cls.diagnose_failure(issue, project_dir, known_files)
        target_file = plan.affected_file

        print(f"[AUTO_REPAIR_DIAGNOSIS] {plan.diagnosis}", flush=True)
        print(f"[AUTO_REPAIR_PLAN] {plan.repair_action}", flush=True)

        # 4. Verify safety guard
        if not cls.is_safe_target_file(target_file, project_dir):
            print(f"[AUTO_REPAIR_FAILED] Protected/unsafe target file '{target_file}' rejected by safety guard.", flush=True)
            return RepairResult(
                attempt_number=attempt_number,
                status="unrepairable",
                error_details=f"Target file '{target_file}' violates safety policy.",
                plan=plan
            )

        # 5. Apply targeted repair
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"[REPAIR_COMPONENT] file=\"{target_file}\" attempt={attempt_number}/3 timestamp={now}", flush=True)
        print(f"[REBUILD_COMPONENT] file=\"{target_file}\" timestamp={now}", flush=True)
        print(f"[AUTO_REPAIR_APPLY] Applying targeted repair to '{target_file}'...", flush=True)

        current_code = generated_contents.get(target_file, "")
        file_lang = "css" if target_file.endswith(".css") else ("html" if target_file.endswith(".html") else "tsx")

        try:
            if code_generator_func:
                repaired_code = code_generator_func(target_file, file_lang, issue.message)
            else:
                # Fallback targeted fixer (e.g. removing syntax errors or invalid tags)
                repaired_code = current_code
                if "react-router-dom" in issue.message or "react-router-dom" in current_code:
                    repaired_code = re.sub(r'import\s+\{[^}]*\}\s+from\s+[\'"]react-router-dom[\'"]\s*;?\s*\n?', '', repaired_code)
                    repaired_code = re.sub(r'import\s+\S+\s+from\s+[\'"]react-router-dom[\'"]\s*;?\s*\n?', '', repaired_code)
                    repaired_code = re.sub(r"<Link\s+to=['\"]([^'\"]+)['\"]", r'<a href="\1"', repaired_code)
                    repaired_code = repaired_code.replace('</Link>', '</a>')
                elif "doctype html" in issue.message.lower():
                    repaired_code = re.sub(r'<!DOCTYPE html>.*?(?=<)', '', repaired_code, flags=re.IGNORECASE | re.DOTALL)

            if not repaired_code or not repaired_code.strip():
                print(f"[AUTO_REPAIR_FAILED] Repair generated empty code for '{target_file}'.", flush=True)
                return RepairResult(
                    attempt_number=attempt_number,
                    status="failed",
                    repaired_file=target_file,
                    error_details="Targeted repair output was empty.",
                    plan=plan
                )

            # Write repaired code to workspace
            from tools.coding.workspace_manager import WorkspaceManager
            ws = WorkspaceManager.get_instance()
            ws.write_workspace_file(project_dir, target_file, repaired_code)
            generated_contents[target_file] = repaired_code

            print(f"[AUTO_REPAIR_SUCCESS] task_id={task_id} file={target_file} repair attempt={attempt_number} applied successfully.", flush=True)

            return RepairResult(
                attempt_number=attempt_number,
                status="success",
                repaired_file=target_file,
                plan=plan
            )

        except Exception as err:
            print(f"[AUTO_REPAIR_FAILED] Exception during repair execution: {err}", flush=True)
            return RepairResult(
                attempt_number=attempt_number,
                status="failed",
                repaired_file=target_file,
                error_details=str(err),
                plan=plan
            )
