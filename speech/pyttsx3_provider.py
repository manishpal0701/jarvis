import asyncio
import os
import uuid
import pyttsx3
import threading
from typing import Optional
from speech.logger import get_logger
from speech.utils import is_valid_audio

logger = get_logger("PyTTSx3Provider")

class PyTTSx3Provider:
    def __init__(self):
        self._lock = threading.Lock()
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            try:
                engine = pyttsx3.init()
                from config import SPEECH_RATE, VOICE_ID
                rate_val = SPEECH_RATE if SPEECH_RATE and 130 <= SPEECH_RATE <= 200 else 165
                engine.setProperty('rate', rate_val)
                engine.setProperty('volume', 1.0)

                voices = engine.getProperty('voices')
                if voices:
                    selected_voice = None
                    for v in voices:
                        v_name = (getattr(v, 'name', '') or '').lower()
                        v_id = (getattr(v, 'id', '') or '').lower()
                        if 'zira' in v_name or 'zira' in v_id:
                            selected_voice = v
                            break
                    if not selected_voice:
                        idx = VOICE_ID if 0 <= VOICE_ID < len(voices) else (len(voices) - 1)
                        selected_voice = voices[idx]

                    engine.setProperty('voice', selected_voice.id)
                    try:
                        driver = getattr(engine.proxy, '_driver', None)
                        if driver and hasattr(driver, '_tokenFromId') and hasattr(driver, '_tts'):
                            token = driver._tokenFromId(selected_voice.id)
                            driver._tts.Voice = token
                    except Exception as com_err:
                        logger.warning(f"Direct SAPI5 COM voice assignment notice: {com_err}")

                self._engine = engine
                logger.info("[PyTTSx3Provider] Persistent SAPI5 engine pre-initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize persistent pyttsx3 engine: {e}")
                self._engine = None
        return self._engine

    async def generate_speech(self, text: str, voice: str, rate: str, pitch: str, volume: str, output_path: str) -> bool:
        """
        Generates audio file using pyttsx3 offline engine with atomic file creation.
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_generate, text, output_path)
        except Exception as e:
            logger.error(f"PyTTSx3 speech generation failed: {e}")
            return False

    def _sync_generate(self, text: str, output_path: str) -> bool:
        with self._lock:
            temp_path = f"{output_path}.tmp.{uuid.uuid4().hex[:8]}"
            try:
                engine = self._get_engine()
                if engine is None:
                    engine = pyttsx3.init()

                engine.save_to_file(text, temp_path)
                engine.runAndWait()

                if is_valid_audio(temp_path):
                    os.replace(temp_path, output_path)
                    logger.info(f"[AUDIO_GENERATION_COMPLETE] PyTTSx3 created: {output_path}")
                    return True
                else:
                    logger.error(f"[AUDIO_VALIDATION] Generated PyTTSx3 audio is invalid: {temp_path}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return False
            except Exception as e:
                logger.error(f"Error in pyttsx3 sync generate: {e}")
                # Fallback: re-initialize engine if COM state corrupted
                try:
                    self._engine = pyttsx3.init()
                    self._engine.save_to_file(text, temp_path)
                    self._engine.runAndWait()
                    if is_valid_audio(temp_path):
                        os.replace(temp_path, output_path)
                        return True
                except Exception:
                    pass
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                return False

