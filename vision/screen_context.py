"""
vision/screen_context.py
Structured ScreenContext model and screen change detection engine for JARVIS Phase 4 Vision.
Integrates ScreenFrame, WindowTracker, OCREngine, and image similarity comparison.
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from PIL import Image

from vision.screen_frame import ScreenFrame
from vision.window_tracker import WindowTracker
from vision.ocr_engine import OCREngine, OCRResult

logger = logging.getLogger("ScreenContext")

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


@dataclass
class ScreenContext:
    frame: ScreenFrame
    active_window: Dict[str, Any] = field(default_factory=dict)
    ocr_result: Optional[OCRResult] = None
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    has_changed: bool = True
    change_magnitude: float = 1.0
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "frame": self.frame.to_dict() if self.frame else None,
            "active_window": self.active_window,
            "ocr_summary": self.ocr_result.to_dict() if self.ocr_result else None,
            "has_changed": self.has_changed,
            "change_magnitude": round(self.change_magnitude, 4),
            "summary": self.summary
        }


class ScreenContextAnalyzer:
    def __init__(self, window_tracker: Optional[WindowTracker] = None, ocr_engine: Optional[OCREngine] = None):
        self.window_tracker = window_tracker or WindowTracker()
        self.ocr_engine = ocr_engine or OCREngine()
        self.last_image_path: Optional[str] = None

    def analyze_frame(self, frame: ScreenFrame, prev_context: Optional[ScreenContext] = None) -> ScreenContext:
        """
        Builds a comprehensive ScreenContext from a captured ScreenFrame.
        Performs active window tracking, spatial OCR, and lightweight change detection.
        """
        active_win = self.window_tracker.get_active_window_info()
        ocr_res = None
        has_changed = True
        change_mag = 1.0

        if frame.image_path:
            # Check screen change magnitude if prev_context is supplied
            if prev_context and prev_context.frame and prev_context.frame.image_path:
                change_mag = self._compute_change_magnitude(prev_context.frame.image_path, frame.image_path)
                has_changed = change_mag > 0.02

            # Run OCR extraction
            ocr_res = self.ocr_engine.extract_text(frame.image_path)

        # Build high-level human-readable context summary
        app_name = active_win.get("process_name", "Unknown App")
        win_title = active_win.get("window_title", "Unknown Window")
        app_cat = active_win.get("app_category", "System")

        summary_parts = [f"Foreground App: '{win_title}' ({app_name}, Category: {app_cat})"]
        if ocr_res and ocr_res.detected_errors:
            summary_parts.append(f"Detected {len(ocr_res.detected_errors)} error trace(s) on screen.")
        if ocr_res and ocr_res.code_snippets:
            summary_parts.append(f"Detected code snippet(s) on screen.")
        if ocr_res and ocr_res.full_text:
            text_snippet = ocr_res.full_text[:120].replace("\n", " ")
            summary_parts.append(f"Visible text snippet: '{text_snippet}...'")

        summary = " | ".join(summary_parts)

        return ScreenContext(
            frame=frame,
            active_window=active_win,
            ocr_result=ocr_res,
            has_changed=has_changed,
            change_magnitude=change_mag,
            summary=summary
        )

    def _compute_change_magnitude(self, path1: str, path2: str) -> float:
        """Computes structural image difference / MSE magnitude between two image paths."""
        try:
            if HAS_OPENCV:
                img1 = cv2.imread(path1, cv2.IMREAD_GRAYSCALE)
                img2 = cv2.imread(path2, cv2.IMREAD_GRAYSCALE)
                if img1 is None or img2 is None or img1.shape != img2.shape:
                    return 1.0
                err = np.sum((img1.astype("float") - img2.astype("float")) ** 2)
                err /= float(img1.shape[0] * img1.shape[1] * 255 * 255)
                return float(err)
            else:
                # PIL fallback pixel difference
                im1 = Image.open(path1).convert("L")
                im2 = Image.open(path2).convert("L")
                if im1.size != im2.size:
                    return 1.0
                hist1 = im1.histogram()
                hist2 = im2.histogram()
                diff = sum(abs(a - b) for a, b in zip(hist1, hist2))
                max_diff = sum(hist1) + sum(hist2)
                return float(diff / max_diff) if max_diff > 0 else 0.0
        except Exception as e:
            logger.debug(f"[ScreenContextAnalyzer] Similarity calculation error: {e}")
            return 1.0
