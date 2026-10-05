import os

# Speech configuration settings
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge-tts")  # pyttsx3 or edge-tts
VOICE_PERSONALITY = "Assistant"  # Professional, Friendly, Serious, Assistant
EMOTION_ENABLED = True
PAUSE_ENABLED = True
SOUND_EFFECTS_ENABLED = True
CACHE_ENABLED = True
CACHE_SIZE_MB = 100
DEFAULT_LANGUAGE = "en-IN"  # en-IN, hi-IN, en-US, en-GB
ROMAN_HINDI_MODE = True
THINKING_MESSAGES_ENABLED = True

# Audio settings
DEFAULT_RATE = "+0%"   # edge-tts rate format (e.g. +0%, -10%, +15%)
DEFAULT_PITCH = "+0Hz"  # edge-tts pitch format (e.g. +0Hz, -5Hz, +10Hz)
DEFAULT_VOLUME = "+0%"  # edge-tts volume format

# Cache directory
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
