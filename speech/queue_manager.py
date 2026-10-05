import queue
import threading
import time
from typing import Callable, Optional
from speech.logger import get_logger
from speech.utils import is_valid_audio

logger = get_logger("QueueManager")

class QueueManager:
    def __init__(self, audio_lock: Optional[threading.Lock] = None):
        self.queue = queue.Queue()
        self.lock = audio_lock or threading.Lock()
        self.is_speaking = False
        self.stop_event = threading.Event()
        self.worker_thread: Optional[threading.Thread] = None
        self.current_playback_thread: Optional[threading.Thread] = None
        self.seen_speech_ids: dict[str, float] = {}
        
        # Initialize pygame mixer
        try:
            import os
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.mute_speaker_output = os.getenv("MUTE_SPEAKER_OUTPUT", "false").lower() == "true"
            pygame.mixer.music.set_volume(0.0 if self.mute_speaker_output else 1.0)
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

    def enqueue(self, audio_path: str, text: str, callback: Optional[Callable[[], None]] = None, speech_id: Optional[str] = None) -> None:
        """Enqueues an audio file for playback with per-speech deduplication protection."""
        now = time.time()
        # Clean up stale entries older than 10 seconds
        stale_keys = [k for k, t in list(self.seen_speech_ids.items()) if now - t > 10.0]
        for k in stale_keys:
            self.seen_speech_ids.pop(k, None)

        effective_id = speech_id or audio_path or text
        audio_key = f"path:{audio_path}" if audio_path else effective_id

        if (effective_id in self.seen_speech_ids and (now - self.seen_speech_ids[effective_id]) < 4.0) or \
           (audio_key in self.seen_speech_ids and (now - self.seen_speech_ids[audio_key]) < 3.0):
            print(f"[AUDIO_DUPLICATE_BLOCKED]\nspeech_id={effective_id}\nreason=already_queued_or_playing", flush=True)
            print(f"[AUDIO_QUEUE] speech_id={effective_id} action=SKIP_DUPLICATE", flush=True)
            logger.info(f"[AUDIO_QUEUE] speech_id={effective_id} action=SKIP_DUPLICATE")
            return

        self.seen_speech_ids[effective_id] = now
        if audio_path:
            self.seen_speech_ids[audio_key] = now

        print(f"[AUDIO_QUEUE_ENQUEUE]\nspeech_id={effective_id}", flush=True)
        print(f"[AUDIO_QUEUE]\nspeech_id={effective_id}\naction=ENQUEUE", flush=True)
        print(f"[STREAM_DEBUG] queue_entry_created speech_id={effective_id}", flush=True)
        logger.info(f"[AUDIO_QUEUE] speech_id={effective_id} action=ENQUEUE")
        self.queue.put((audio_path, text, callback, effective_id))

    def clear_queue(self) -> None:
        """Clears all items in the queue and resets deduplication tracking."""
        self.seen_speech_ids.clear()
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except queue.Empty:
                break

    def cancel_request(self, request_id: str) -> None:
        """Cancels enqueued items and stops playback specifically for target request_id."""
        if not request_id:
            self.clear_queue()
            self.stop_playback()
            return

        print(f"[AUDIO_QUEUE_CANCEL_REQUEST] request_id={request_id}", flush=True)
        self.clear_queue()
        self.stop_playback()

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
        """Plays the audio file using pygame with validation and blocks until finished."""
        if not self.has_pygame:
            logger.error("Pygame mixer not available. Cannot play audio.")
            return

        MAX_AUDIO_READY_RETRIES = 3
        ready = False
        for attempt in range(MAX_AUDIO_READY_RETRIES):
            if is_valid_audio(audio_path):
                ready = True
                break
            time.sleep(0.05)

        if not ready:
            logger.error(f"[AUDIO_PLAYBACK_REJECTED] reason=invalid_or_incomplete_audio path={audio_path}")
            return

        try:
            import pygame
            # Stop any current music and unload to release file locks
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            pygame.mixer.music.unload()

            logger.info(f"[AUDIO_PLAYBACK_START] path={audio_path}")
            print(f"[AUDIO_PLAYBACK_START]\npath={audio_path}", flush=True)
            pygame.mixer.music.load(audio_path)
            if self.mute_speaker_output:
                pygame.mixer.music.set_volume(0.0)
            else:
                pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()

            # Block until playback completes
            while pygame.mixer.music.get_busy() and not self.stop_event.is_set():
                time.sleep(0.05)

            pygame.mixer.music.unload()
            logger.info(f"[AUDIO_PLAYBACK_SUCCESS] path={audio_path}")
            print(f"[AUDIO_PLAYBACK_SUCCESS]\npath={audio_path}", flush=True)
        except Exception as e:
            logger.error(f"[AUDIO_PLAYBACK_REJECTED] reason=pygame_error details={e} path={audio_path}")

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
                
            if len(item) == 4:
                audio_path, duration_or_text, callback, item_speech_id = item
            else:
                audio_path, duration_or_text, callback = item
                item_speech_id = "unknown"
            
            print(f"[AUDIO_QUEUE_DEQUEUE]\nspeech_id={item_speech_id}", flush=True)
            
            try:
                if audio_path is None:
                    # It's a pause item
                    duration_ms = duration_or_text
                    logger.info(f"Pausing for {duration_ms}ms")
                    time.sleep(duration_ms / 1000.0)
                else:
                    # It's an audio playback item
                    text = duration_or_text
                    import os
                    owner = os.getenv("PLAYBACK_OWNER", "FRONTEND").upper()

                    with self.lock:
                        self.is_speaking = True
                        cnt = self.seen_speech_ids.get(item_speech_id, 1)
                        logger.info(f"Speaking: '{text}'")
                        print(f"[SPEECH_PLAYBACK_START] response_id={item_speech_id} count=1", flush=True)
                        print(f"[TTS_PLAYBACK_START] response_id={item_speech_id} path={audio_path}", flush=True)
                        print(f"[AUDIO_PLAYBACK_OWNER]\nowner={owner}", flush=True)
                        print(f"[VOICE_PLAYBACK_OWNER]\nowner={owner}", flush=True)
                        from core.performance_profiler import PerformanceProfiler
                        PerformanceProfiler.mark("AUDIO_PLAYBACK_START")
                        
                        if owner == "FRONTEND" or self.mute_speaker_output:
                            # Single playback delegated to frontend browser Live2DController
                            time.sleep(0.01)
                        else:
                            self._play_audio(audio_path)

                        print(f"[SPEECH_PLAYBACK_END] response_id={item_speech_id} count=1", flush=True)
                        print(f"[TTS_PLAYBACK_END] response_id={item_speech_id} path={audio_path}", flush=True)
                
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

