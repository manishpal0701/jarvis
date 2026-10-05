import asyncio
import os
import re
import uuid
import threading
from abc import ABC, abstractmethod
from typing import Optional, Callable

import edge_tts

from speech.config import ROMAN_HINDI_MODE, EMOTION_ENABLED, PAUSE_ENABLED, TTS_PROVIDER
from speech.pyttsx3_provider import PyTTSx3Provider
from speech.logger import get_logger
from speech.utils import transliterate_text, is_valid_audio
from speech.language_detector import LanguageDetector
from speech.response_formatter import ResponseFormatter
from speech.emotion_engine import EmotionEngine
from speech.pause_engine import PauseEngine
from speech.voice_manager import VoiceManager
from speech.cache_manager import CacheManager
from speech.sound_manager import SoundManager
from speech.queue_manager import QueueManager

logger = get_logger("SpeechEngine")

class BaseSpeechProvider(ABC):
    @abstractmethod
    async def generate_speech(self, text: str, voice: str, rate: str, pitch: str, volume: str, output_path: str) -> bool:
        pass

class EdgeTTSProvider(BaseSpeechProvider):
    def __init__(self, voice: Optional[str] = None):
        self.voice = voice or "en-IN-NeerjaExpressiveNeural"

    async def generate_speech(self, text: str, voice: str, rate: str, pitch: str, volume: str, output_path: str) -> bool:
        temp_path = f"{output_path}.tmp.{uuid.uuid4().hex[:8]}"
        target_voice = voice or self.voice
        try:
            logger.info(f"[AUDIO_GENERATION_START] EdgeTTS text: '{text[:30]}...' voice='{target_voice}'")
            communicate = edge_tts.Communicate(text, target_voice, rate=rate, pitch=pitch, volume=volume)
            await communicate.save(temp_path)

            if is_valid_audio(temp_path):
                os.replace(temp_path, output_path)
                logger.info(f"[AUDIO_GENERATION_COMPLETE] EdgeTTS created: {output_path}")
                return True
            else:
                logger.error(f"[AUDIO_VALIDATION] Generated EdgeTTS audio is invalid: {temp_path}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                return False
        except Exception as e:
            logger.error(f"Edge TTS speech generation failed: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            return False

class SpeechEngine:
    def __init__(self, provider: Optional[BaseSpeechProvider] = None):
        if provider:
            self.provider = provider
        elif TTS_PROVIDER == "pyttsx3":
            self.provider = PyTTSx3Provider()
        else:
            self.provider = EdgeTTSProvider()
        self.language_detector = LanguageDetector()
        self.response_formatter = ResponseFormatter()
        self.emotion_engine = EmotionEngine()
        self.pause_engine = PauseEngine()
        self.voice_manager = VoiceManager()
        self.cache_manager = CacheManager()
        self.sound_manager = SoundManager()
        self.queue_manager = QueueManager()
        self._speak_lock = threading.Lock()
        
        # Event loop for running async tasks
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._loop_thread.start()

    def _run_event_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def initialize(self) -> None:
        """Initializes the speech engine, pre-warms TTS provider, and starts the queue manager."""
        self.queue_manager.start()
        # Pre-warm persistent PyTTSx3 provider SAPI5 engine
        if isinstance(self.provider, PyTTSx3Provider):
            try:
                self.provider._get_engine()
            except Exception:
                pass
        self.sound_manager.play_sound("startup")
        logger.info("SpeechEngine initialized successfully.")

    def shutdown(self) -> None:
        """Shuts down the speech engine and stops the queue manager."""
        self.sound_manager.play_sound("shutdown")
        self.queue_manager.stop()
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._loop_thread.join(timeout=2.0)
        logger.info("SpeechEngine shut down.")

    def speak(self, text: str, wait: bool = True, callback: Optional[Callable[[], None]] = None, single_response: bool = True, speech_id: Optional[str] = None, request_id: Optional[str] = None, **kwargs) -> Optional[str]:
        """Processes the text and enqueues TTS audio output. Returns generated audio_path."""
        if not text or not text.strip():
            return None

        eff_speech_id = speech_id or f"speech_{uuid.uuid4().hex[:8]}"
        eff_request_id = request_id or f"req_{uuid.uuid4().hex[:8]}"

        with self._speak_lock:
            # Determine provider audio extension (.wav for pyttsx3, .mp3 for edge-tts)
            is_pyttsx3 = isinstance(self.provider, PyTTSx3Provider)
            audio_ext = "wav" if is_pyttsx3 else "mp3"
            prov_name = "PyTTSx3Provider" if is_pyttsx3 else "EdgeTTSProvider"
            logger.info(f"[TTS_RUNTIME_PROVIDER] provider={prov_name}")
            print(f"[TTS_RUNTIME_PROVIDER] provider={prov_name}", flush=True)

            # 1. Format response for speech (console vs spoken text)
            spoken_text = self.response_formatter.format_for_speech(text).strip()
            if not spoken_text:
                return None

            logger.info(f"[CONVERSATION_RESPONSE_READY] response_id={eff_speech_id} chars={len(spoken_text)}")

            if single_response:
                logger.info("[CONVERSATION_TTS_MODE] mode=single_response")
                logger.info(f"[TTS_QUEUE] response_id={eff_speech_id} chars={len(spoken_text)}")
                # If request_id was not explicitly passed from SpeechCoordinator, print TTS_QUEUE format
                if not request_id:
                    print(f"[TTS_QUEUE]\nrequest_id={eff_request_id}\nresponse_id={eff_speech_id}", flush=True)

                # Classify emotion for the entire text
                emotion = "professional"
                rate, pitch, volume = "+0%", "+0Hz", "+0%"
                if EMOTION_ENABLED:
                    emotion = self.emotion_engine.classify(spoken_text)
                    rate, pitch, volume = self.emotion_engine.get_params(emotion)

                # Detect language & transliterate Devanagari Hindi to Roman Hindi if enabled
                lang = self.language_detector.detect(spoken_text)
                if lang == "hi-IN" and ROMAN_HINDI_MODE:
                    spoken_text = transliterate_text(spoken_text)
                    lang = "hinglish"

                # Select voice identifier
                if is_pyttsx3:
                    voice = "pyttsx3_zira_v2"
                    logger.info(f"[TTS_VOICE_RESOLUTION] provider=PyTTSx3Provider resolved_voice={voice}")
                else:
                    voice = self.voice_manager.get_voice(lang)
                    logger.info(f"[TTS_RUNTIME_VOICE] voice={voice}")
                    print(f"[TTS_RUNTIME_VOICE] voice={voice}", flush=True)
                    logger.info(f"[TTS_VOICE_RESOLUTION] provider=EdgeTTSProvider resolved_voice={voice}")

                # Check cache or generate single audio file
                audio_path = self.cache_manager.get_cached_audio(spoken_text, voice, rate, pitch, emotion, ext=audio_ext)

                if not audio_path:
                    audio_path = self.cache_manager.get_cache_path(spoken_text, voice, rate, pitch, emotion, ext=audio_ext)

                    if emotion == "thinking":
                        self.sound_manager.play_sound("thinking")

                    future = asyncio.run_coroutine_threadsafe(
                        self.provider.generate_speech(spoken_text, voice, rate, pitch, volume, audio_path),
                        self._loop
                    )
                    success = future.result()
                    if not success:
                        logger.error(f"Failed to generate speech audio for response: '{spoken_text[:30]}...'")
                        return None

                logger.info(f"[TTS_PLAYBACK] request_id={eff_request_id} response_id={eff_speech_id} file={audio_path}")
                print(f"[TTS_PLAYBACK]\nrequest_id={eff_request_id}\nresponse_id={eff_speech_id}", flush=True)
                logger.info(f"[AUDIO_QUEUE] Enqueueing complete response: {audio_path} for text: '{spoken_text[:30]}...'")
                self.queue_manager.enqueue(audio_path, spoken_text, callback=callback, speech_id=eff_speech_id)
                if wait:
                    self.queue_manager.wait_until_done()
                return audio_path
            else:
                logger.info("[CONVERSATION_TTS_MODE] mode=streaming")
                # Legacy chunked speech fallback if explicitly requested
                parts = re.split(r'(\.\.\.|[\.!\?,])', spoken_text)

                emotion = "professional"
                rate, pitch, volume = "+0%", "+0Hz", "+0%"
                if EMOTION_ENABLED:
                    emotion = self.emotion_engine.classify(spoken_text)
                    rate, pitch, volume = self.emotion_engine.get_params(emotion)

                i = 0
                while i < len(parts):
                    part = parts[i].strip()
                    if not part:
                        i += 1
                        continue

                    if part in ['...', '.', '!', '?', ',']:
                        if PAUSE_ENABLED:
                            pause_type = "sentence" if part not in ['...', ','] else ("ellipsis" if part == '...' else "comma")
                            duration_ms = self.pause_engine.get_pause_duration(pause_type, emotion)
                            self.queue_manager.enqueue_pause(duration_ms)
                        i += 1
                        continue

                    lang = self.language_detector.detect(part)
                    if lang == "hi-IN" and ROMAN_HINDI_MODE:
                        part = transliterate_text(part)
                        lang = "hinglish"

                    voice = self.voice_manager.get_voice(lang)
                    audio_path = self.cache_manager.get_cached_audio(part, voice, rate, pitch, emotion, ext=audio_ext)

                    if not audio_path:
                        audio_path = self.cache_manager.get_cache_path(part, voice, rate, pitch, emotion, ext=audio_ext)
                        future = asyncio.run_coroutine_threadsafe(
                            self.provider.generate_speech(part, voice, rate, pitch, volume, audio_path),
                            self._loop
                        )
                        success = future.result()
                        if not success:
                            i += 1
                            continue

                    self.queue_manager.enqueue(audio_path, part)
                    i += 1

            if wait:
                self.queue_manager.wait_until_done()


