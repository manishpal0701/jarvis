"""
vision/privacy_filter.py
Privacy and Sensitive Data Protection for JARVIS Phase 4 Vision.
Filters credentials, API keys, tokens, and manages temporary screenshot file lifecycles.
"""

import os
import re
import glob
import time
import logging
from typing import List

logger = logging.getLogger("PrivacyFilter")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
TEMP_SCREENSHOT_DIR = os.path.join(DATA_DIR, "temp_screenshots")
os.makedirs(TEMP_SCREENSHOT_DIR, exist_ok=True)

# Common regex patterns for secret / sensitive tokens
SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|secret|token|password|auth[_-]?header|bearer)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{8,})["\']?'),
    re.compile(r'sk-[a-zA-Z0-9]{20,}'),
    re.compile(r'ghp_[a-zA-Z0-9]{36}'),
    re.compile(r'eyJ[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*'),  # JWT
    re.compile(r'(?i)password\s*=\s*[^\s]+'),
]

class PrivacyFilter:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PrivacyFilter()
        return cls._instance

    @staticmethod
    def get_temp_dir() -> str:
        os.makedirs(TEMP_SCREENSHOT_DIR, exist_ok=True)
        return TEMP_SCREENSHOT_DIR

    @staticmethod
    def filter_text(text: str) -> str:
        """Masks detected secret tokens, API keys, and passwords from extracted text."""
        if not text:
            return ""
        filtered = text
        for pattern in SECRET_PATTERNS:
            filtered = pattern.sub('[REDACTED_SECRET]', filtered)
        return filtered

    @staticmethod
    def cleanup_file(file_path: str) -> bool:
        """Safely removes a temporary screenshot file."""
        if not file_path or not os.path.exists(file_path):
            return False
        try:
            os.remove(file_path)
            print(f"[PRIVACY_CLEANUP] Deleted temp image: {os.path.basename(file_path)}", flush=True)
            return True
        except Exception as e:
            logger.error(f"[PRIVACY_CLEANUP Error]: Failed to delete {file_path}: {e}")
            return False

    @staticmethod
    def cleanup_all_temp_screenshots(max_age_seconds: float = 60.0) -> int:
        """Cleans up temporary screenshots older than max_age_seconds."""
        now = time.time()
        count = 0
        pattern = os.path.join(TEMP_SCREENSHOT_DIR, "*.png")
        for fpath in glob.glob(pattern):
            try:
                if now - os.path.getmtime(fpath) > max_age_seconds:
                    os.remove(fpath)
                    count += 1
            except Exception:
                pass
        return count
