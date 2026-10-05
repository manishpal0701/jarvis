"""
tools/app_builder/placeholder_detector.py
Phase 13 — Production Quality Gate Placeholder Detector.
Scans generated source files for forbidden placeholder UI strings ("Component Ready", "Screen Ready", "Coming Soon", etc.).
If forbidden placeholder content exists in user-facing screens, PLACEHOLDER_DETECTION = FAIL.
"""
import os
import json
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("PlaceholderDetector")


class PlaceholderDetector:
    """
    Quality gate scanner verifying that generated UI screens contain real production UI
    and zero placeholder scaffolds.
    """

    FORBIDDEN_PATTERNS = [
        r"\bComponent Ready\b",
        r"\bScreen Ready\b",
        r"\bComing Soon\b",
        r"\bPlaceholder Text\b",
        r"\bPlaceholder Screen\b",
        r"\bDemo Screen\b",
        r"\bTest Screen\b",
        r"\bTODO:\b",
        r"\bImplement here\b",
        r"\bNot implemented\b"
    ]

    @classmethod
    def scan_workspace(cls, workspace_path: str) -> Dict[str, Any]:
        """
        Scans all files in `frontend/lib/` and `backend/src/` for forbidden placeholder strings.
        Returns detailed report dict.
        """
        abs_workspace = os.path.abspath(workspace_path)
        frontend_lib = os.path.join(abs_workspace, "frontend", "lib")
        backend_src = os.path.join(abs_workspace, "backend", "src")

        scanned_files = []
        violations = []

        target_dirs = [d for d in [frontend_lib, backend_src] if os.path.exists(d)]

        compiled_patterns = [(pat, re.compile(pat, re.IGNORECASE)) for pat in cls.FORBIDDEN_PATTERNS]

        for target_dir in target_dirs:
            for root, _, files in os.walk(target_dir):
                for file in files:
                    if file.endswith((".dart", ".js", ".ts", ".html", ".css")):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, abs_workspace)
                        scanned_files.append(rel_path)

                        try:
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                lines = f.readlines()

                            for line_num, line_str in enumerate(lines, start=1):
                                # Ignore comment-only lines for minor internal TODOs if not user-facing
                                # But strict check for strings rendered in Text(...) or UI widgets
                                for pat_str, regex in compiled_patterns:
                                    if regex.search(line_str):
                                        violations.append({
                                            "file": rel_path,
                                            "line": line_num,
                                            "pattern": pat_str,
                                            "snippet": line_str.strip()[:100]
                                        })
                        except Exception as ex:
                            logger.error(f"Error reading file {full_path} during placeholder scan: {ex}")

        passed = len(violations) == 0

        report = {
            "status": "PASS" if passed else "FAIL",
            "passed": passed,
            "has_placeholders": not passed,
            "total_files_scanned": len(scanned_files),
            "violations_count": len(violations),
            "count": len(violations),
            "violations": violations,
            "matches": violations,
            "scanned_files": scanned_files
        }

        # Write placeholder_detection_report.json
        report_file = os.path.join(abs_workspace, "placeholder_detection_report.json")
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            logger.info(f"[PLACEHOLDER_DETECTION] status={report['status']} files={len(scanned_files)} violations={len(violations)}")
        except Exception as ex:
            logger.error(f"Failed writing placeholder_detection_report.json: {ex}")

        return report
