import asyncio
import os
import pyttsx3
import threading
from typing import Optional
from speech.logger import get_logger

logger = get_logger("PyTTSx3Provider")

class PyTTSx3Provider:
    def __init__(self):
        self._lock = threading.Lock()

    async def generate_speech(self, text: str, voice: str, rate: str, pitch: str, volume: str, output_path: str) -> bool:
        """
        Generates audio file using pyttsx3 offline engine.
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_generate, text, output_path)
        except Exception as e:
            logger.error(f"PyTTSx3 speech generation failed: {e}")
            return False

    def _sync_generate(self, text: str, output_path: str) -> bool:
        with self._lock:
            try:
                engine = pyttsx3.init()
                engine.save_to_file(text, output_path)
                engine.runAndWait()
                engine.stop()
                return os.path.exists(output_path) and os.path.getsize(output_path) > 0
            except Exception as e:
                logger.error(f"Error in pyttsx3 sync generate: {e}")
                return False
