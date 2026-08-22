import queue
import threading
import time
from typing import Callable, Optional
from speech.logger import get_logger

logger = get_logger("QueueManager")

class QueueManager:
    def __init__(self, audio_lock: Optional[threading.Lock] = None):
        self.queue = queue.Queue()
        self.lock = audio_lock or threading.Lock()
        self.is_speaking = False
        self.stop_event = threading.Event()
        self.worker_thread: Optional[threading.Thread] = None
        self.current_playback_thread: Optional[threading.Thread] = None
        
        # Initialize pygame mixer
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.has_pygame = True
        except Exception as e:
            logger.error(f"Failed to initialize pygame mixer in QueueManager: {e}")
            self.has_pygame = False

    def start(self) -> None:
        """Starts the background worker thread."""
        self.stop_event.clear()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        logger.info("QueueManager worker thread started.")

    def stop(self) -> None:
        """Stops the worker thread and clears the queue."""
        self.stop_event.set()
        self.queue.put(None)  # Wake up worker if waiting
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)
        self.clear_queue()
        self.stop_playback()
        logger.info("QueueManager stopped.")

    def enqueue(self, audio_path: str, text: str, callback: Optional[Callable[[], None]] = None) -> None:
        """Enqueues an audio file for playback."""
        self.queue.put((audio_path, text, callback))
        logger.debug(f"Enqueued audio: {audio_path} for text: '{text[:20]}...'")

    def clear_queue(self) -> None:
        """Clears all items in the queue."""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except queue.Empty:
                break

    def stop_playback(self) -> None:
        """Stops any currently playing audio."""
        if not self.has_pygame:
            return
            
        try:
            import pygame
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")

    def wait_until_done(self) -> None:
        """Blocks until the queue is empty and playback is finished."""
        self.queue.join()

    def _play_audio(self, audio_path: str) -> None:
        """Plays the audio file using pygame and blocks until finished."""
        if not self.has_pygame:
            logger.error("Pygame mixer not available. Cannot play audio.")
            return
            
        try:
            import pygame
            # Stop any current music and unload to release file locks
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # Block until playback completes
            while pygame.mixer.music.get_busy() and not self.stop_event.is_set():
                time.sleep(0.05)
                
            pygame.mixer.music.unload()
        except Exception as e:
            logger.error(f"Error playing audio file {audio_path}: {e}")

    def enqueue_pause(self, duration_ms: int) -> None:
        """Enqueues a silent pause duration."""
        self.queue.put((None, duration_ms, None))
        logger.debug(f"Enqueued pause: {duration_ms}ms")

    def _worker(self) -> None:
        """Background worker loop that processes the queue sequentially."""
        import pythoncom
        pythoncom.CoInitialize()
        
        while not self.stop_event.is_set():
            item = self.queue.get()
            if item is None:
                self.queue.task_done()
                break
                
            audio_path, duration_or_text, callback = item
            
            try:
                if audio_path is None:
                    # It's a pause item
                    duration_ms = duration_or_text
                    logger.info(f"Pausing for {duration_ms}ms")
                    time.sleep(duration_ms / 1000.0)
                else:
                    # It's an audio playback item
                    text = duration_or_text
                    with self.lock:
                        self.is_speaking = True
                        logger.info(f"Speaking: '{text}'")
                        self._play_audio(audio_path)
                
                if callback:
                    try:
                        callback()
                    except Exception as e:
                        logger.error(f"Error in speech callback: {e}")
                        
            except Exception as e:
                logger.error(f"Error in queue worker: {e}")
            finally:
                if audio_path is not None:
                    with self.lock:
                        self.is_speaking = False
                self.queue.task_done()
                
        pythoncom.CoUninitialize()
