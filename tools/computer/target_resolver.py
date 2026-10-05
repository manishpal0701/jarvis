"""
tools/computer/target_resolver.py
Semantic visual target resolver for JARVIS Phase 5 Computer Control.
Maps semantic target labels to screen bounding boxes and center coordinates using Phase 4 Vision (OCR/WindowTracker).
Enforces target confidence scoring, ambiguity detection, and target staleness invalidation.
"""

import os
import re
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from vision.screen_capture import ScreenCapture
from vision.window_tracker import WindowTracker
from vision.ocr_engine import OCREngine, OCRTextBlock
from vision.screen_context import ScreenContext, ScreenContextAnalyzer
from vision.privacy_filter import PrivacyFilter
from tools.computer.action_model import ActionTarget

logger = logging.getLogger("TargetResolver")


class TargetResolutionResult:
    def __init__(
        self,
        target: Optional[ActionTarget] = None,
        confidence: float = 0.0,
        is_ambiguous: bool = False,
        ambiguous_candidates: Optional[List[ActionTarget]] = None,
        clarification_message: Optional[str] = None
    ):
        self.target = target
        self.confidence = confidence
        self.is_ambiguous = is_ambiguous
        self.ambiguous_candidates = ambiguous_candidates or []
        self.clarification_message = clarification_message


class TargetResolver:
    def __init__(
        self,
        screen_capture: Optional[ScreenCapture] = None,
        window_tracker: Optional[WindowTracker] = None,
        ocr_engine: Optional[OCREngine] = None,
        context_analyzer: Optional[ScreenContextAnalyzer] = None
    ):
        self.screen_capture = screen_capture or ScreenCapture()
        self.window_tracker = window_tracker or WindowTracker()
        self.ocr_engine = ocr_engine or OCREngine()
        self.context_analyzer = context_analyzer or ScreenContextAnalyzer(self.window_tracker, self.ocr_engine)
        self.privacy_filter = PrivacyFilter.get_instance()

    def resolve_target(
        self,
        semantic_label: str,
        screen_context: Optional[ScreenContext] = None,
        auto_cleanup: bool = True
    ) -> TargetResolutionResult:
        """
        Resolves a semantic target label (e.g., 'Run button', 'Search field', 'Login')
        to an ActionTarget with spatial screen coordinates (x, y).
        """
        if not semantic_label or not semantic_label.strip():
            return TargetResolutionResult(confidence=0.0, clarification_message="Target label was empty.")

        label_clean = semantic_label.strip().lower()

        # Step 1: Obtain fresh ScreenContext if not provided
        context = screen_context
        temp_frame_path = None
        if not context or not context.frame or not context.frame.image_path:
            frame = self.screen_capture.capture_full_screen()
            temp_frame_path = frame.image_path
            context = self.context_analyzer.analyze_frame(frame)

        frame_id = context.frame.frame_id if context.frame else "frame_unknown"
        ocr_res = context.ocr_result

        # Step 2: Match OCR spatial text blocks against label
        candidates: List[Tuple[OCRTextBlock, float]] = []

        if ocr_res and ocr_res.blocks:
            for block in ocr_res.blocks:
                text_clean = block.text.strip().lower()
                conf = self._compute_label_similarity(label_clean, text_clean) * block.confidence
                if conf > 0.30:
                    candidates.append((block, conf))

        # Sort candidates by confidence descending
        candidates.sort(key=lambda x: x[1], reverse=True)

        if auto_cleanup and temp_frame_path:
            self.privacy_filter.cleanup_file(temp_frame_path)

        # Step 3: Handle candidates
        if not candidates:
            # Fallback for active window title matching or desktop center
            win_info = context.active_window or {}
            win_rect = win_info.get("rect", (0, 0, 1920, 1080))
            center_x = (win_rect[0] + win_rect[2]) // 2
            center_y = (win_rect[1] + win_rect[3]) // 2

            fallback_target = ActionTarget(
                semantic_label=semantic_label,
                bbox=(win_rect[0], win_rect[1], win_rect[2] - win_rect[0], win_rect[3] - win_rect[1]),
                center_x=center_x,
                center_y=center_y,
                confidence=0.50,
                frame_id=frame_id,
                metadata={"reason": "Active window fallback"}
            )
            return TargetResolutionResult(target=fallback_target, confidence=0.50)

        # Check top match vs second match for ambiguity
        top_block, top_conf = candidates[0]
        x, y, w, h = top_block.bbox
        center_x = x + w // 2
        center_y = y + h // 2

        top_target = ActionTarget(
            semantic_label=top_block.text,
            bbox=(x, y, w, h),
            center_x=center_x,
            center_y=center_y,
            confidence=top_conf,
            frame_id=frame_id,
            metadata={"extracted_text": top_block.text}
        )

        if len(candidates) >= 2:
            second_block, second_conf = candidates[1]
            if top_conf >= 0.65 and second_conf >= 0.60 and (top_conf - second_conf) < 0.15:
                # Ambiguity detected!
                amb_targets = []
                for b, c in candidates[:3]:
                    bx, by, bw, bh = b.bbox
                    amb_targets.append(ActionTarget(
                        semantic_label=b.text,
                        bbox=(bx, by, bw, bh),
                        center_x=bx + bw // 2,
                        center_y=by + bh // 2,
                        confidence=c,
                        frame_id=frame_id
                    ))

                msg = f"Boss, mujhe multiple matching elements dikh rahe hain '{semantic_label}' ke liye. Kaunsa click karu?"
                return TargetResolutionResult(
                    target=top_target,
                    confidence=top_conf,
                    is_ambiguous=True,
                    ambiguous_candidates=amb_targets,
                    clarification_message=msg
                )

        return TargetResolutionResult(target=top_target, confidence=top_conf)

    def validate_target_freshness(self, target: ActionTarget, current_context: ScreenContext) -> bool:
        """
        Validates if target was created from a fresh screen frame and active window match.
        If screen changed significantly, returns False (invalidating target).
        """
        if not target or not target.frame_id:
            return True

        if current_context.frame and current_context.frame.frame_id:
            if target.frame_id != current_context.frame.frame_id:
                # Check change magnitude
                if not current_context.has_changed or current_context.change_magnitude < 0.05:
                    return True
                logger.info(f"[TargetResolver] Target frame {target.frame_id} invalidated due to screen change magnitude {current_context.change_magnitude:.4f}")
                return False
        return True

    def _compute_label_similarity(self, target_label: str, candidate_text: str) -> float:
        """Computes matching similarity score between target_label and candidate_text."""
        if target_label == candidate_text:
            return 1.0
        if target_label in candidate_text:
            return 0.90
        if candidate_text in target_label:
            return 0.85

        words_target = set(re.findall(r"\w+", target_label))
        words_candidate = set(re.findall(r"\w+", candidate_text))
        if not words_target or not words_candidate:
            return 0.0

        overlap = words_target.intersection(words_candidate)
        return float(len(overlap)) / float(max(len(words_target), len(words_candidate)))
