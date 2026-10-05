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
MODEL_NAME = "qwen3:4b-instruct"          # Default conversation & general response model (fast CPU inference)
CODE_GEN_MODEL = "qwen3:4b-instruct"      # React/TypeScript/Tailwind code generation & targeted repair
APP_CODING_MODEL = os.environ.get("APP_CODING_MODEL", CODE_GEN_MODEL)  # Phase 4 App Builder multi-file coding model
APP_CODE_FIX_MAX_RETRIES = int(os.environ.get("APP_CODE_FIX_MAX_RETRIES", "4"))
RESEARCH_MODEL = "qwen3:8b"               # Research, content strategy & design system
ROUTER_MODEL = "phi4-mini"                # Lightweight intent routing
OLLAMA_CODEGEN_TIMEOUT = 60               # Bounded HTTP timeout for local code generation

# Speech settings (pyttsx3)
SPEECH_RATE = 170   # speed of voice
VOICE_ID = 4       # default voice

# Jarvis behavior``
WAKE_WORD = "jarvis"

# Optional limits
MAX_MEMORY_ITEMS = 50

FLUTTER_PROJECT = r"C:\Users\manis\OneDrive\Desktop\Flutter projects\weather_forecast"
ANDROID_STUDIO = r"C:\Program Files\Android\Android Studio\bin\studio64.exe"