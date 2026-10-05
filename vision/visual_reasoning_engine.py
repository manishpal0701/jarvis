"""
vision/visual_reasoning_engine.py
Visual Reasoning Engine for JARVIS Phase 4 Vision.
Performs Visual QA, developer error diagnosis, grounding tag attribution ([OBSERVED], [INFERRED], [UNKNOWN]),
and manages the end-to-end vision workflow with privacy filtering and auto-cleanup.
"""

import os
import re
import logging
from typing import Any, Dict, Optional

from vision.screen_capture import ScreenCapture
from vision.window_tracker import WindowTracker
from vision.ocr_engine import OCREngine
from vision.screen_context import ScreenContext, ScreenContextAnalyzer
from vision.vision_provider import VisionProvider, OllamaVisionProvider, LocalVisionProvider
from vision.privacy_filter import PrivacyFilter

logger = logging.getLogger("VisualReasoningEngine")


class VisualReasoningEngine:
    def __init__(
        self,
        screen_capture: Optional[ScreenCapture] = None,
        screen_analyzer: Optional[ScreenContextAnalyzer] = None,
        vision_provider: Optional[VisionProvider] = None
    ):
        self.screen_capture = screen_capture or ScreenCapture()
        self.screen_analyzer = screen_analyzer or ScreenContextAnalyzer()
        self.primary_vision = vision_provider or OllamaVisionProvider()
        self.fallback_vision = LocalVisionProvider()
        self.privacy_filter = PrivacyFilter.get_instance()

    def process_visual_query(self, query: str, auto_cleanup: bool = True) -> Dict[str, Any]:
        """
        Executes on-demand screen capture, context analysis, visual reasoning,
        grounding tag attribution, privacy filtering, and image cleanup.
        """
        logger.info(f"[VisualReasoningEngine] Processing visual query: '{query}'")

        # Step 1: On-demand screen capture
        frame = self.screen_capture.capture_full_screen()
        if not frame.image_path or not os.path.exists(frame.image_path):
            return self._build_unknown_response("Failed to capture screen image.")

        # Step 2: Screen context analysis (window tracking & OCR)
        context = self.screen_analyzer.analyze_frame(frame)

        # Step 3: Attempt primary vision model or fallback to local context synthesis
        prov_res = self.primary_vision.analyze_screen(frame.image_path, query, context.to_dict())
        if not prov_res.get("success") or not prov_res.get("raw_response"):
            prov_res = self.fallback_vision.analyze_screen(frame.image_path, query, context.to_dict())

        raw_response = prov_res.get("raw_response", "")

        # Step 4: Grounding & error analysis
        grounded_response = self._attribute_grounding(raw_response, context, query)

        # Step 5: Privacy filtering
        filtered_response = self.privacy_filter.filter_text(grounded_response)

        # Step 6: Auto-cleanup of temp screenshot
        if auto_cleanup and frame.image_path:
            self.privacy_filter.cleanup_file(frame.image_path)

        return {
            "success": True,
            "response": filtered_response,
            "context_summary": context.summary,
            "active_window": context.active_window,
            "provider_used": prov_res.get("provider", "Unknown")
        }

    def _attribute_grounding(self, raw_response: str, context: ScreenContext, query: str) -> str:
        """
        Attributes grounding confidence tags ([OBSERVED], [INFERRED], [UNKNOWN]) to the analysis.
        """
        win_info = context.active_window
        ocr_info = context.ocr_result
        win_title = win_info.get("window_title", "Desktop")
        app_name = win_info.get("process_name", "App")

        # Check low confidence / empty screen text case
        if not raw_response and (not ocr_info or not ocr_info.full_text):
            return "[UNKNOWN] Screen details could not be detected clearly or vision input was empty."

        query_lower = query.lower()
        is_error_query = any(k in query_lower for k in ["error", "issue", "problem", "bug", "crash", "traceback", "fix", "kya galat hai"])
        is_code_query = any(k in query_lower for k in ["code", "function", "explain", "samjha", "logic"])

        lines = []

        # Grounding: Observed foreground application window
        lines.append(f"[OBSERVED] Foreground window is '{win_title}' ({app_name}).")

        # Handle error queries
        if is_error_query:
            if ocr_info and ocr_info.detected_errors:
                err_text = ocr_info.detected_errors[0]
                lines.append(f"[OBSERVED] Detected error on screen: {err_text}")

                # Infer root cause & suggestion
                inference = self._infer_error_solution(err_text)
                lines.append(f"[INFERRED] Cause & Solution: {inference}")
            elif raw_response:
                lines.append(f"[OBSERVED] Screen response: {raw_response}")
                lines.append(f"[INFERRED] Analyzing visible UI details for error context.")
            else:
                lines.append("[UNKNOWN] No explicit stack trace or error message was found on screen.")

        # Handle code queries
        elif is_code_query:
            if ocr_info and ocr_info.code_snippets:
                code_sample = ocr_info.code_snippets[0][:300]
                lines.append(f"[OBSERVED] Code snippet visible on screen:\n{code_sample}")
                lines.append(f"[INFERRED] Logic overview: The code performs operations in {app_name}.")
            elif raw_response:
                lines.append(f"[OBSERVED] Visual content analysis: {raw_response}")
            else:
                lines.append("[UNKNOWN] No readable code snippet could be extracted from the active window.")

        # General Visual QA queries ("screen pe kya hai?", "what do you see?")
        else:
            if ocr_info and ocr_info.full_text:
                txt_snippet = ocr_info.full_text[:250].replace("\n", " ")
                lines.append(f"[OBSERVED] Visible text content: '{txt_snippet}...'")
            if raw_response:
                lines.append(f"[INFERRED] Analysis summary: {raw_response}")

        return "\n".join(lines)

    def _infer_error_solution(self, error_text: str) -> str:
        err_lower = error_text.lower()

        if "syntaxerror" in err_lower:
            return "Syntax Error detected. Check for missing colons, unbalanced parentheses, or improper indentation."
        if "typeerror" in err_lower:
            return "TypeError detected. An operation was performed on an incompatible data type."
        if "nameerror" in err_lower:
            return "NameError detected. A variable or function was referenced before definition or import."
        if "attributeerror" in err_lower:
            return "AttributeError detected. Check if the object has the specified attribute or method."
        if "importerror" in err_lower or "modulenotfounderror" in err_lower:
            return "ImportError detected. Verify that the package is installed in your Python environment."
        if "build failed" in err_lower or "flutter" in err_lower:
            return "Build Failure detected. Check missing dependencies, unresolved imports, or syntax in widget files."

        return "Terminal/runtime error detected. Review the line numbers and file paths referenced in the stack trace."

    def _build_unknown_response(self, message: str) -> Dict[str, Any]:
        return {
            "success": False,
            "response": f"[UNKNOWN] {message}",
            "context_summary": "Screen capture unavailable",
            "active_window": {},
            "provider_used": "None"
        }
