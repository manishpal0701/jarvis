"""
speech/voice_config.py
Centralized configuration parameters for JARVIS Voice & Interaction Intelligence (Phase 3).
Defines configurable VAD, listening, silence, interruption thresholds and timeouts.
"""

import os

class VoiceConfig:
    # Minimum user speech duration required for valid interruption (ms)
    MIN_INTERRUPTION_SPEECH_DURATION_MS: float = float(os.getenv("MIN_INTERRUPTION_SPEECH_DURATION_MS", "250.0"))

    # Speech energy / confidence threshold for barge-in detection (0.0 to 1.0)
    INTERRUPTION_CONFIDENCE_THRESHOLD: float = float(os.getenv("INTERRUPTION_CONFIDENCE_THRESHOLD", "0.5"))

    # VAD sensitivity (1 to 3, where 3 is most aggressive)
    VAD_SENSITIVITY: int = int(os.getenv("VAD_SENSITIVITY", "2"))

    # Silence threshold before concluding end of speech (seconds)
    SILENCE_THRESHOLD_SEC: float = float(os.getenv("SILENCE_THRESHOLD_SEC", "0.8"))

    # Maximum duration to wait for user speech onset (seconds)
    LISTENING_TIMEOUT_SEC: float = float(os.getenv("LISTENING_TIMEOUT_SEC", "8.0"))

    # Maximum phrase time limit (seconds)
    MAX_PHRASE_TIME_LIMIT_SEC: float = float(os.getenv("MAX_PHRASE_TIME_LIMIT_SEC", "15.0"))

    # Interruption debounce window to prevent rapid duplicate triggers (ms)
    DEBOUNCE_INTERVAL_MS: float = float(os.getenv("DEBOUNCE_INTERVAL_MS", "300.0"))

    # Echo guard wait time after TTS completes (seconds)
    ECHO_GUARD_DELAY_SEC: float = float(os.getenv("ECHO_GUARD_DELAY_SEC", "0.3"))

    # Explicit interruption phrases
    EXPLICIT_STOP_PHRASES = {
        "stop", "ruk", "ruko", "bas", "chup", "stop speaking", "stop talking",
        "wait", "hold on", "quiet", "pause", "shutup", "shut up", "listen", "sun"
    }

    # Explicit task cancellation phrases
    EXPLICIT_CANCEL_TASK_PHRASES = {
        "stop this task", "cancel task", "stop task", "stop app build",
        "stop development", "abort task", "cancel app build", "cancel project"
    }
