import os
import time
import threading
from typing import Dict
from speech.config import SOUNDS_DIR, SOUND_EFFECTS_ENABLED
from speech.logger import get_logger

logger = get_logger("SoundManager")

# Try importing winsound for Windows beep fallback
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

class SoundManager:
    def __init__(self):
        self.enabled = SOUND_EFFECTS_ENABLED
        self.sounds_dir = SOUNDS_DIR
        self.cooldowns: Dict[str, float] = {}
        self.cooldown_duration = 3.0  # seconds
        
        if self.enabled:
            os.makedirs(self.sounds_dir, exist_ok=True)
            # Initialize pygame mixer if not already initialized
            try:
                import pygame
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                self.has_pygame = True
            except Exception as e:
                logger.warning(f"Failed to initialize pygame mixer: {e}")
                self.has_pygame = False

    def _play_fallback_beep(self, event: str) -> None:
        """Plays a subtle beep using winsound on Windows as a fallback."""
        if not HAS_WINSOUND:
            return
            
        def run_beep():
            try:
                if event == "startup":
                    winsound.Beep(1000, 150)
                    winsound.Beep(1200, 150)
                elif event == "wake_word":
                    winsound.Beep(1500, 100)
                elif event == "thinking":
                    winsound.Beep(800, 100)
                elif event == "complete":
                    winsound.Beep(1200, 100)
                    winsound.Beep(1500, 150)
                elif event == "warning":
                    winsound.Beep(600, 300)
                elif event == "shutdown":
                    winsound.Beep(1200, 150)
                    winsound.Beep(1000, 150)
            except Exception as e:
                logger.debug(f"Fallback beep failed: {e}")
                
        threading.Thread(target=run_beep, daemon=True).start()

    def play_sound(self, event: str) -> None:
        """Plays the sound effect associated with the event, respecting cooldowns."""
        if not self.enabled:
            return
            
        # Cooldown check
        now = time.time()
        if event in self.cooldowns and now - self.cooldowns[event] < self.cooldown_duration:
            logger.debug(f"Sound effect '{event}' is on cooldown.")
            return
            
        self.cooldowns[event] = now
        
        # Try playing the sound file
        sound_file = os.path.join(self.sounds_dir, f"{event}.wav")
        if self.has_pygame and os.path.exists(sound_file):
            try:
                import pygame
                sound = pygame.mixer.Sound(sound_file)
                sound.play()
                logger.info(f"Played sound effect: {event}")
                return
            except Exception as e:
                logger.error(f"Failed to play sound file {sound_file}: {e}")
                
        # Fallback to winsound beep
        self._play_fallback_beep(event)
