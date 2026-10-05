"""
tools/app_builder/runtime_error_analyzer.py
Phase 5 — Runtime Error Extraction & Diagnostics Analyzer.
Parses error logs from Flutter tools (`pub get`, `analyze`, `build apk`, `run`),
Node.js tools (`npm install`, `node --check`, `start`), and HTTP API integration calls into structured diagnostic objects.
"""
import re
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("RuntimeErrorAnalyzer")


class RuntimeErrorAnalyzer:
    """
    Parses raw stderr and stdout outputs into structured runtime error objects:
    platform, file, line, column, message, stack_trace.
    """

    @classmethod
    def parse_error(cls, raw_output: str, platform: str = "flutter") -> Dict[str, Any]:
        """
        Parses raw text output and extracts structured error details.
        """
        if not raw_output:
            return {
                "platform": platform,
                "file": None,
                "line": None,
                "column": None,
                "message": "Unknown runtime error (empty output)",
                "stack_trace": ""
            }

        # 1. Flutter Analyze Pattern: "error • Undefined name 'xyz' • lib/screens/login_screen.dart:42:15 • undefined_identifier"
        flutter_match = re.search(r'(error|warning)\s*•\s*(.*?)\s*•\s*([a-zA-Z0-9_/\\.]+\.dart):(\d+):(\d+)', raw_output)
        if flutter_match:
            msg = flutter_match.group(2).strip()
            file_path = flutter_match.group(3).strip()
            line = int(flutter_match.group(4))
            col = int(flutter_match.group(5))
            return {
                "platform": "flutter",
                "file": file_path,
                "line": line,
                "column": col,
                "message": msg,
                "stack_trace": raw_output[:500]
            }

        # 2. Node.js Syntax Error Pattern: "C:\path\src\app.js:42\nSyntaxError: Unexpected token ..."
        node_match = re.search(r'([a-zA-Z0-9_/\\:.-]+\.js):(\d+)(?::(\d+))?\s*\n.*?(SyntaxError|ReferenceError|TypeError|Error):\s*(.*)', raw_output, re.DOTALL)
        if node_match:
            file_path = node_match.group(1).strip()
            line = int(node_match.group(2))
            col = int(node_match.group(3)) if node_match.group(3) else None
            msg = node_match.group(5).splitlines()[0].strip() if node_match.group(5) else "Node runtime error"
            return {
                "platform": "node",
                "file": file_path,
                "line": line,
                "column": col,
                "message": msg,
                "stack_trace": raw_output[:500]
            }

        # 3. Fallback file/line parser: "file.ext:42:15"
        generic_match = re.search(r'([a-zA-Z0-9_/\\.]+\.(?:dart|js|json)):(\d+)', raw_output)
        if generic_match:
            return {
                "platform": platform,
                "file": generic_match.group(1),
                "line": int(generic_match.group(2)),
                "column": None,
                "message": raw_output.splitlines()[0] if raw_output else "Build error",
                "stack_trace": raw_output[:500]
            }

        # 4. Default return
        lines = [l.strip() for l in raw_output.splitlines() if l.strip()]
        first_err_line = lines[0] if lines else "Execution error"
        return {
            "platform": platform,
            "file": None,
            "line": None,
            "column": None,
            "message": first_err_line,
            "stack_trace": raw_output[:500]
        }
