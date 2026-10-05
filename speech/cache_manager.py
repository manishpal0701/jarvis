import os
import hashlib
import time
import threading
from typing import Optional
from speech.config import CACHE_DIR, CACHE_SIZE_MB, CACHE_ENABLED
from speech.logger import get_logger
from speech.utils import is_valid_audio

logger = get_logger("CacheManager")

class CacheManager:
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.enabled = CACHE_ENABLED
        self.max_size_bytes = CACHE_SIZE_MB * 1024 * 1024
        self._lock = threading.Lock()
        
        if self.enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
            self.cleanup_cache()

    def get_cache_path(self, text: str, voice: str, rate: str, pitch: str, emotion: str, ext: str = "mp3") -> str:
        """Generates a unique cache file path based on speech parameters."""
        ext_clean = ext.lstrip(".")
        key = f"{text}|{voice}|{rate}|{pitch}|{emotion}".encode("utf-8")
        file_hash = hashlib.md5(key).hexdigest()
        return os.path.join(self.cache_dir, f"{file_hash}.{ext_clean}")

    def get_cached_audio(self, text: str, voice: str, rate: str, pitch: str, emotion: str, ext: str = "mp3") -> Optional[str]:
        """Returns the path to the cached audio file if it exists and is valid, otherwise None."""
        if not self.enabled:
            return None
            
        with self._lock:
            path = self.get_cache_path(text, voice, rate, pitch, emotion, ext=ext)
            if os.path.exists(path):
                if is_valid_audio(path):
                    try:
                        os.utime(path, None)
                    except Exception as e:
                        logger.warning(f"Failed to update access time for {path}: {e}")
                    logger.info(f"[AUDIO_FILE_READY] Cache hit for text: '{text[:30]}...' ({path})")
                    return path
                else:
                    logger.warning(f"[AUDIO_VALIDATION] Removing invalid/corrupt cached file: {path}")
                    try:
                        os.remove(path)
                    except Exception as e:
                        logger.error(f"Failed to remove invalid cache file {path}: {e}")
            return None

    def cleanup_cache(self) -> None:
        """Cleans up old cache files if the total size exceeds the limit (LRU policy)."""
        if not self.enabled or not os.path.exists(self.cache_dir):
            return
            
        with self._lock:
            try:
                files = []
                total_size = 0
                for entry in os.scandir(self.cache_dir):
                    if entry.is_file() and (entry.name.endswith(".mp3") or entry.name.endswith(".wav")):
                        stat = entry.stat()
                        files.append((entry.path, stat.st_atime, stat.st_size))
                        total_size += stat.st_size
                        
                if total_size <= self.max_size_bytes:
                    return
                    
                logger.info(f"Cache size ({total_size / (1024*1024):.2f} MB) exceeds limit ({CACHE_SIZE_MB} MB). Cleaning up...")
                
                # Sort by access time (oldest first)
                files.sort(key=lambda x: x[1])
                
                bytes_to_delete = total_size - (self.max_size_bytes * 0.8)  # Clean down to 80% of max size
                deleted_bytes = 0
                
                for path, _, size in files:
                    if deleted_bytes >= bytes_to_delete:
                        break
                    try:
                        os.remove(path)
                        deleted_bytes += size
                        logger.debug(f"Deleted cache file: {path}")
                    except Exception as e:
                        logger.error(f"Failed to delete cache file {path}: {e}")
                        
                logger.info(f"Cache cleanup complete. Deleted {deleted_bytes / (1024*1024):.2f} MB.")
            except Exception as e:
                logger.error(f"Error during cache cleanup: {e}")

