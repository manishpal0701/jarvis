import asyncio
import os
import re
from abc import ABC, abstractmethod
from typing import Optional, Callable

import edge_tts

from speech.config import ROMAN_HINDI_MODE, EMOTION_ENABLED, PAUSE_ENABLED, TTS_PROVIDER
from speech.pyttsx3_provider import PyTTSx3Provider
from speech.logger import get_logger
from speech.utils import transliterate_text
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
    async def generate_speech(self, text: str, voice: str, rate: str, pitch: str, volume: str, output_path: str) -> bool:
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
            await communicate.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Edge TTS speech generation failed: {e}")
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
        
        # Event loop for running async tasks
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._loop_thread.start()

    def _run_event_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def initialize(self) -> None:
        """Initializes the speech engine and starts the queue manager."""
        self.queue_manager.start()
        self.sound_manager.play_sound("startup")
        logger.info("SpeechEngine initialized successfully.")

    def shutdown(self) -> None:
        """Shuts down the speech engine and stops the queue manager."""
        self.sound_manager.play_sound("shutdown")
        self.queue_manager.stop()
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._loop_thread.join(timeout=2.0)
        logger.info("SpeechEngine shut down.")

    def speak(self, text: str, wait: bool = True, callback: Optional[Callable[[], None]] = None) -> None:
        """Processes the text, splits it by delimiters for pauses, and enqueues chunks."""
        if not text:
            return

        # 1. Format response for speech (console vs spoken text)
        spoken_text = self.response_formatter.format_for_speech(text)
        
        # 2. Split text by delimiters to insert pauses
        # Delimiters: ... , . ! ?
        parts = re.split(r'(\.\.\.|[\.!\?,])', spoken_text)
        
        # Classify emotion for the entire text to maintain consistency
        emotion = "professional"
        rate, pitch, volume = "+0%", "+0Hz", "+0%"
        if EMOTION_ENABLED:
            emotion = self.emotion_engine.classify(spoken_text)
            rate, pitch, volume = self.emotion_engine.get_params(emotion)
            
        # Process each part
        i = 0
        while i < len(parts):
            part = parts[i].strip()
            if not part:
                i += 1
                continue
                
            # Check if it's a delimiter
            if part in ['...', '.', '!', '?', ',']:
                if PAUSE_ENABLED:
                    pause_type = "sentence"
                    if part == '...':
                        pause_type = "ellipsis"
                    elif part == ',':
                        pause_type = "comma"
                        
                    duration_ms = self.pause_engine.get_pause_duration(pause_type, emotion)
                    self.queue_manager.enqueue_pause(duration_ms)
                i += 1
                continue
                
            # It's a text chunk
            # Detect language
            lang = self.language_detector.detect(part)
            
            # Transliterate Devanagari Hindi to Roman Hindi if enabled
            if lang == "hi-IN" and ROMAN_HINDI_MODE:
                part = transliterate_text(part)
                lang = "hinglish"
                
            # Select voice
            voice = self.voice_manager.get_voice(lang)
            
            # Check cache
            audio_path = self.cache_manager.get_cached_audio(part, voice, rate, pitch, emotion)
            
            if not audio_path:
                audio_path = self.cache_manager.get_cache_path(part, voice, rate, pitch, emotion)
                
                # Play thinking sound effect if it's a long operation or thinking emotion
                if emotion == "thinking":
                    self.sound_manager.play_sound("thinking")
                    
                # Generate speech
                future = asyncio.run_coroutine_threadsafe(
                    self.provider.generate_speech(part, voice, rate, pitch, volume, audio_path),
                    self._loop
                )
                success = future.result()
                if not success:
                    logger.error(f"Failed to generate speech audio for chunk: '{part}'")
                    i += 1
                    continue
                    
            # Enqueue audio
            self.queue_manager.enqueue(audio_path, part)
            i += 1
            
        if wait:
            self.queue_manager.wait_until_done()
            
# Global thread import for loop thread
import threading
