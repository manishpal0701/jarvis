"""
api/services/jarvis_service.py
Service facade connecting FastAPI routes and WebSockets to the underlying Jarvis backend core modules.
Executes blocking routines safely off-thread to maintain a non-blocking FastAPI event loop.
"""
import asyncio
import logging
from typing import Callable, Dict, Any, List, Optional
from conversation.conversation_engine import ConversationEngine
from conversation.command_router import CommandRouter
from core.state_machine import State
from api.schemas.jarvis import CommandResponse, JarvisStateResponse, CancelResponse

logger = logging.getLogger("JarvisAPIService")

class JarvisService:
    def __init__(self):
        # Obtain singleton instance of ConversationEngine
        self.engine = ConversationEngine()

    def get_state(self) -> JarvisStateResponse:
        """Returns current StateMachine and SpeechCoordinator status."""
        sm_state = self.engine.state_machine.state
        state_name = sm_state.name if hasattr(sm_state, 'name') else str(sm_state)
        is_speaking = self.engine.speech_coordinator.is_speaking()
        is_listening = (sm_state == State.LISTENING)
        return JarvisStateResponse(
            state=state_name,
            is_speaking=is_speaking,
            is_listening=is_listening
        )

    def cancel_speech(self) -> CancelResponse:
        """Cancels active speech playback and flushes audio queues."""
        try:
            self.engine.speech_coordinator.cancel_speech()
            return CancelResponse(
                success=True,
                message="Speech playback and session cancelled successfully.",
                status="ok"
            )
        except Exception as e:
            logger.error(f"Error executing speech cancellation: {e}")
            return CancelResponse(
                success=False,
                message=f"Cancellation error: {e}",
                status="error"
            )

    def _sync_execute_command(self, text: str, enable_audio_tts: bool = False, request_id: Optional[str] = None) -> str:
        """Synchronous wrapper for command execution using CommandRouter."""
        spoken_chunks: List[str] = []

        def _capture_chunk(chunk: str):
            if chunk and chunk.strip():
                spoken_chunks.append(chunk.strip())

        coordinator = self.engine.speech_coordinator if enable_audio_tts else None
        router = CommandRouter(speech_coordinator=coordinator, speak_callback=_capture_chunk)

        try:
            router.route_command(text, request_id=request_id)
        except Exception as e:
            logger.error(f"Error in CommandRouter route_command: {e}")
            if not spoken_chunks:
                spoken_chunks.append(f"An error occurred while processing your command: {e}")

        final_response = " ".join(spoken_chunks) if spoken_chunks else "Command processed."
        return final_response

    async def execute_command(self, text: str, enable_audio_tts: bool = False, request_id: Optional[str] = None) -> CommandResponse:
        """Async command execution offloaded to worker thread."""
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Command text cannot be empty.")

        response_text = await asyncio.to_thread(
            self._sync_execute_command, cleaned_text, enable_audio_tts, request_id
        )

        return CommandResponse(
            success=True,
            text=response_text,
            command=cleaned_text
        )

    def _sync_execute_chat_command(self, text: str, source: str = "chat", enable_audio_tts: bool = True, request_id: Optional[str] = None) -> str:
        """Synchronous wrapper for chat command execution using CommandRouter.process_user_input."""
        spoken_chunks: List[str] = []

        def _capture_chunk(chunk: str):
            if chunk and chunk.strip():
                spoken_chunks.append(chunk.strip())

        coordinator = self.engine.speech_coordinator if enable_audio_tts else None
        router = CommandRouter(speech_coordinator=coordinator, speak_callback=_capture_chunk)

        try:
            router.process_user_input(text, source=source, request_id=request_id)
        except Exception as e:
            logger.error(f"Error in CommandRouter process_user_input: {e}")
            if not spoken_chunks:
                spoken_chunks.append(f"An error occurred while processing your chat command: {e}")

        final_response = " ".join(spoken_chunks) if spoken_chunks else "Command processed."
        return final_response

    async def execute_chat_command(self, text: str, source: str = "chat", enable_audio_tts: bool = True, request_id: Optional[str] = None) -> str:
        """Async chat command execution offloaded to worker thread."""
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Command text cannot be empty.")

        return await asyncio.to_thread(
            self._sync_execute_chat_command, cleaned_text, source, enable_audio_tts, request_id
        )

    def _sync_stream_command(self, text: str, chunk_callback: Callable[[str], None], enable_audio_tts: bool = False, request_id: Optional[str] = None):
        """Synchronous streaming execution wrapper."""
        coordinator = self.engine.speech_coordinator if enable_audio_tts else None
        router = CommandRouter(speech_coordinator=coordinator, speak_callback=chunk_callback)
        router.route_command(text, request_id=request_id)

    async def stream_command(self, text: str, chunk_callback: Callable[[str], None], enable_audio_tts: bool = False, request_id: Optional[str] = None):
        """Async streaming command execution offloaded to worker thread."""
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Command text cannot be empty.")

        await asyncio.to_thread(
            self._sync_stream_command, cleaned_text, chunk_callback, enable_audio_tts, request_id
        )

# Singleton service instance
_jarvis_service_instance: Optional[JarvisService] = None

def get_jarvis_service() -> JarvisService:
    global _jarvis_service_instance
    if _jarvis_service_instance is None:
        _jarvis_service_instance = JarvisService()
    return _jarvis_service_instance
