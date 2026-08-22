import os

# =========================
# JARVIS CONFIG FILE
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Memory file (chat history / user data store)
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")

# Ollama settings (local AI)
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

# Speech settings (pyttsx3)
SPEECH_RATE = 170   # speed of voice
VOICE_ID = 2        # default voice

# Jarvis behavior
WAKE_WORD = "jarvis"

# Optional limits
MAX_MEMORY_ITEMS = 50

FLUTTER_PROJECT = r"C:\Users\manis\OneDrive\Desktop\Flutter projects\weather_forecast"
ANDROID_STUDIO = r"C:\Program Files\Android\Android Studio\bin\studio64.exe"