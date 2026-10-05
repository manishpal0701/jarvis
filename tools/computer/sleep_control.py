"""
tools/computer/sleep_control.py
Dedicated Laptop / Windows System Sleep Controller for Jarvis AI Assistant.
Provides intent detection for natural language sleep requests and executes safe native Windows sleep.
"""

import re
import sys
import os
import subprocess
import ctypes
from typing import Tuple

class SleepController:
    """
    Manages system sleep intent recognition and native Windows sleep execution.
    """

    @classmethod
    def is_sleep_command(cls, query: str) -> bool:
        """
        Determines if a natural language query expresses the intent to put the laptop to sleep,
        or indicates the user is leaving/going to sleep.
        Guards against generic or informational queries containing the word 'sleep'.
        """
        if not query:
            return False

        q = query.lower().strip()

        # Negative checks: exclude informational, technical, or Q&A queries
        negative_keywords = [
            "what is", "how to", "why do", "explain", "python", "code", "script",
            "function", "time.sleep", "sleep cycle", "sleep quality", "sleep disorder",
            "sleep pattern", "sleep duration", "sleep mode in windows", "meaning of",
            "tell me about", "defined as", "how many hours of sleep"
        ]
        if any(kw in q for kw in negative_keywords):
            return False

        # Positive intent regex patterns
        sleep_patterns = [
            # Hindi / Hinglish going to sleep
            r"\b(main|mai)\s+(so|sone)\s+(raha|rha)\s+(hoon|hu|huu)\b",
            r"\b(sone|so)\s+(ja|jaa)\s+(raha|rha)\s+(hoon|hu|huu)\b",

            # Hindi / Hinglish leaving / going out
            r"\b(main|mai)\s+bahar\s+(ja|jaa)\s+(raha|rha)\s+(hoon|hu|huu)\b",
            r"\b(main|mai)\s+bahar\s+(ja|jaa)\s+(raha|rha)\s+h?u?n?,?\s*(der\s+se\s+aaunga|der\s+se\s+aunga)\b",

            # Explicit laptop/PC sleep imperatives
            r"\b(laptop|pc|computer|system)\s+(sleep|ko\s+sleep|pe\s+daal|pe\s+dal|mode\s+me)\b",
            r"\b(sleep|sleep\s+mode)\s+(pe\s+daal|ko\s+kar|me\s+daal|kar\s+do|pe\s+dalo|me\s+dalo)\b",
            r"\bput\s+(the\s+)?(laptop|pc|computer|system)\s+to\s+sleep\b",
            r"\b(put|set)\s+(system|laptop|pc)\s+(in|to)\s+sleep\b",
            r"\bgo\s+to\s+sleep\s*mode?\b",
            r"\b(turn\s+off\s+screen\s+and\s+sleep|sleep\s+the\s+laptop)\b"
        ]

        return any(re.search(pat, q) for pat in sleep_patterns)

    @classmethod
    def execute_sleep_action(cls) -> bool:
        """
        Executes native Windows sleep (Suspend mode).
        Disables hibernate flag in SetSuspendState call to prevent hibernate.
        """
        if sys.platform != "win32":
            print("[SleepController] Non-Windows OS detected. Sleep action skipped.", flush=True)
            return False

        print("[SleepController] Initiating native Windows Sleep action...", flush=True)
        try:
            # Native C API: SetSuspendState(bHibernate=0, bForceCritical=0, bDisableWakeEvent=0)
            res = ctypes.windll.powrprof.SetSuspendState(0, 0, 0)
            if res != 0:
                return True
        except Exception as e:
            print(f"[SleepController Ctypes Error]: {e}", flush=True)

        try:
            cmd = "Add-Type -Assembly System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState([System.Windows.Forms.PowerState]::Suspend, $false, $false)"
            subprocess.run(["powershell", "-Command", cmd], capture_output=True)
            return True
        except Exception as e:
            print(f"[SleepController PowerShell Error]: {e}", flush=True)
            return False
