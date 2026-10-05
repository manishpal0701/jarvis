"""
video_editing/video_intent_router.py
Deterministic High-Priority Video Intent Classifier for Jarvis.
Distinguishes VIDEO_EDIT, VIDEO_EXPORT, VIDEO_ANALYSIS, and GENERAL_CONVERSATION
before generic conversation LLM invocation.
"""

import re

# Intent String Constants
INTENT_VIDEO_EDIT = "VIDEO_EDIT"
INTENT_VIDEO_EDIT_REFERENCE = "VIDEO_EDIT_REFERENCE"
INTENT_VIDEO_EXPORT = "VIDEO_EXPORT"
INTENT_VIDEO_ANALYSIS = "VIDEO_ANALYSIS"
INTENT_GENERAL_CONVERSATION = "GENERAL_CONVERSATION"


class VideoIntentRouter:
    """
    High-priority deterministic intent classifier for video requests.
    Supports English & Hinglish phrasing variations.
    """

    # Informational / Q&A Command Patterns (Must remain GENERAL_CONVERSATION)
    INFORMATIONAL_PATTERNS = [
        r"\b(kya\s+hoti\s+hai|kya\s+hai|what\s+is|explain|how\s+does|how\s+to|tell\s+me\s+about)\b",
        r"\b(meaning|definition|difference\s+between)\b"
    ]

    # Reference-Driven Edit Command Patterns
    REFERENCE_EDIT_PATTERNS = [
        r"\breference\s+jaisi\b",
        r"\breference\s+ko\s+follow\b",
        r"\breference\s+video\s+jaisi\b",
        r"\breference\s+jaisa\b",
        r"\breference\s+style\b",
        r"\breference\s+pacing\b"
    ]

    # Video Edit Command Patterns (Hinglish + English)
    EDIT_PATTERNS = [
        r"\btrim\b",
        r"\bcut\b",
        r"\bcombine\b",
        r"\bmerge\b",
        r"\b(meri|ek|is|ye|this|these)\s+.*(video|reel|clip|clips|footage)\s+.*(edit|bana|banao|trim|cut|crop|combine|merge|sequence|arrange)\b",
        r"\b(edit|bana|banao|trim|cut|crop|combine|merge|sequence|arrange)\s+.*(video|reel|clip|clips|footage)\b",
        r"\b(cinematic|beat\s*sync)\s+.*(edit|video|bana|banao|karo|do)\b",
        r"\b(edit|bana|banao|karo|do)\s+.*(cinematic|beat\s*sync)\b",
        r"\b(premiere|capcut)\s+.*(mein|me|with)?\s*(video|edit)\b",
        r"\bvideo\s+edit\b",
        r"\bedit\s+video\b",
        r"\bedit\s+this\s+video\b",
        r"\bedit\s+this\s+footage\b",
        r"\breel\s+bana\b",
        r"\bcinematic\s+edit\b",
        r"\bcinematic\s+video\b",
        r"\bcinematic\s+sequence\b",
        r"\bboring\s+part\s+hata\b",
        r"\bbest\s+clips?\s+select\b",
        r"\bcinematic\s+reel\b",
        r"\b(make|create)\s+a?\s*(cinematic|reel|short|montage|video|edit)\b",
        r"\b(instagram|youtube|tiktok)\s+(reel|video)\s*(edit|bana)?\b",
        r"\bvideo\s+ko\s+.*(edit|bana|cinematic|trim|combine)\b",
        r"\b(meri|ek|is|ye)\s+.*(video|clip|clips)\s+.*(edit|bana|trim)\b",
        r"\b(combine|merge|join)\s+.*(clips?|videos?|folder|files?)\b",
        r"\b(clips?|videos?)\s+ko\s+.*(combine|merge|join|arrange|sequence)\b",
        r"\bfolder\s+ki\s+videos?\b",
        r"\bis\s+folder\s+.*(edit|bana|banao|combine|merge)\b",
        r"\btrim\s+.*(video|clip|3\s*seconds?)\b",
        r"\bmake\s+a?\s*montage\b"
    ]

    # Video Export Command Patterns
    EXPORT_PATTERNS = [
        r"\b(export|render)\s+.*(project|sequence)\b",
        r"\b(export|render)\s+(kar\s+do|karo)\b",
        r"\b1080p\s+mein\s+export\b",
        r"\b(instagram|youtube\s+short)\s+ke\s+liye\s+export\b"
    ]

    # Video Analysis Command Patterns
    ANALYSIS_PATTERNS = [
        r"\b(video|scene|scenes)\s+.*(analyze|analysis)\b",
        r"\b(analyze|analysis)\s+.*(video|scene|scenes)\b",
        r"\b(is\s+video\s+ka|video\s+ka|audio\s+ka)\s+(bpm|scenes)\b",
        r"\b(bpm|scenes)\s+(batao|check|analyze)\b",
        r"\bvideo\s+mein\s+kitne\s+scenes\b",
        r"\bscenes\s+analyze\b"
    ]

    @classmethod
    def classify_intent(cls, command: str) -> dict:
        """
        Classifies user input command.
        """
        if not command or not command.strip():
            return {
                "intent": INTENT_GENERAL_CONVERSATION,
                "confidence": 1.0,
                "matched_pattern": None
            }

        cmd_clean = command.strip().lower()

        # -1. Check INFORMATIONAL queries first (Must NOT trigger Video Agent)
        is_info = any(re.search(pat, cmd_clean) for pat in cls.INFORMATIONAL_PATTERNS)
        has_edit_imperative = any(re.search(r"\b(bana\s+do|edit\s+karke\s+do|edit\s+karo|trim\s+karo|export\s+karo|banao)\b", cmd_clean) for _ in [1])

        if is_info and not has_edit_imperative:
            res = {
                "intent": INTENT_GENERAL_CONVERSATION,
                "confidence": 0.99,
                "matched_pattern": "informational_query"
            }
            cls._log_classification(command, res["intent"], res["confidence"])
            return res

        # 0. Check REFERENCE EDIT intent
        for pat in cls.REFERENCE_EDIT_PATTERNS:
            if re.search(pat, cmd_clean):
                res = {
                    "intent": INTENT_VIDEO_EDIT_REFERENCE,
                    "confidence": 0.98,
                    "matched_pattern": pat
                }
                cls._log_classification(command, res["intent"], res["confidence"])
                return res

        # 1. Check EDIT intent
        for pat in cls.EDIT_PATTERNS:
            if re.search(pat, cmd_clean):
                res = {
                    "intent": INTENT_VIDEO_EDIT,
                    "confidence": 0.95,
                    "matched_pattern": pat
                }
                cls._log_classification(command, res["intent"], res["confidence"])
                return res

        # 2. Check EXPORT intent
        for pat in cls.EXPORT_PATTERNS:
            if re.search(pat, cmd_clean):
                res = {
                    "intent": INTENT_VIDEO_EXPORT,
                    "confidence": 0.95,
                    "matched_pattern": pat
                }
                cls._log_classification(command, res["intent"], res["confidence"])
                return res

        # 3. Check ANALYSIS intent
        for pat in cls.ANALYSIS_PATTERNS:
            if re.search(pat, cmd_clean):
                res = {
                    "intent": INTENT_VIDEO_ANALYSIS,
                    "confidence": 0.95,
                    "matched_pattern": pat
                }
                cls._log_classification(command, res["intent"], res["confidence"])
                return res

        # 4. Fallback: GENERAL_CONVERSATION
        res = {
            "intent": INTENT_GENERAL_CONVERSATION,
            "confidence": 1.0,
            "matched_pattern": None
        }
        return res

    @classmethod
    def _log_classification(cls, command: str, intent: str, confidence: float):
        print(
            f"[INTENT_CLASSIFICATION]\n"
            f"command=\"{command}\"\n"
            f"intent={intent}\n"
            f"confidence={confidence:.2f}\n",
            flush=True
        )


def classify_video_intent(command: str) -> dict:
    """Convenience functional wrapper for VideoIntentRouter.classify_intent."""
    return VideoIntentRouter.classify_intent(command)
