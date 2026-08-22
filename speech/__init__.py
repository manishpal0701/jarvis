from speech.speech_engine import SpeechEngine

# Global speech engine instance
_engine = SpeechEngine()

def initialize() -> None:
    """Initializes the global speech engine."""
    _engine.initialize()

def shutdown() -> None:
    """Shuts down the global speech engine."""
    _engine.shutdown()

def speak(text: str, wait: bool = True) -> None:
    """Speaks the given text using the global speech engine."""
    _engine.speak(text, wait=wait)

def is_speaking() -> bool:
    """Returns whether the speech engine is currently speaking or has queued speech."""
    return _engine.queue_manager.is_speaking or not _engine.queue_manager.queue.empty()

def get_engine() -> SpeechEngine:
    """Returns the global speech engine instance."""
    return _engine
