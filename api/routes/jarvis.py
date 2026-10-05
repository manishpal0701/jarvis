"""
api/routes/jarvis.py
FastAPI REST routes for Jarvis AI Assistant.
Exposes endpoints for health check, state monitoring, command execution, streaming SSE, and cancellation.
"""
import json
import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse, JSONResponse
from api.schemas.jarvis import (
    HealthResponse,
    CommandRequest,
    CommandResponse,
    JarvisStateResponse,
    CancelResponse,
    ErrorResponse,
    ErrorDetail
)
from api.services.jarvis_service import get_jarvis_service, JarvisService

router = APIRouter(tags=["Jarvis"])

@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check():
    """Returns status of the Jarvis API service."""
    return HealthResponse(status="ok", service="jarvis-api")

@router.get("/api/v1/jarvis/state", response_model=JarvisStateResponse, summary="Get Jarvis State")
async def get_state(service: JarvisService = Depends(get_jarvis_service)):
    """Returns the current StateMachine state and speech audio status."""
    try:
        return service.get_state()
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(code="STATE_ERROR", message=str(e))
            ).model_dump()
        )

@router.post("/api/v1/jarvis/command", response_model=CommandResponse, summary="Execute Text Command")
async def execute_command(
    request: CommandRequest,
    service: JarvisService = Depends(get_jarvis_service)
):
    """
    Executes a natural language command via the existing CommandRouter.
    Returns the complete text response.
    """
    if not request.text or not request.text.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(code="INVALID_COMMAND", message="Command text cannot be empty.")
            ).model_dump()
        )

    try:
        return await service.execute_command(request.text, enable_audio_tts=request.enable_audio_tts)
    except ValueError as ve:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(code="INVALID_COMMAND", message=str(ve))
            ).model_dump()
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(code="COMMAND_EXECUTION_FAILED", message=str(e))
            ).model_dump()
        )

@router.post("/api/v1/jarvis/stream", summary="Stream Response (SSE)")
async def stream_command(
    request: CommandRequest,
    service: JarvisService = Depends(get_jarvis_service)
):
    """
    Executes a command and streams response sentence chunks in real time via Server-Sent Events (SSE).
    """
    if not request.text or not request.text.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(code="INVALID_COMMAND", message="Command text cannot be empty.")
            ).model_dump()
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _sync_callback(chunk: str):
            if chunk and chunk.strip():
                loop.call_soon_threadsafe(queue.put_nowait, chunk.strip())

        yield f"event: response_start\ndata: {json.dumps({'status': 'started'})}\n\n"

        full_collected = []

        async def _run_stream():
            try:
                await service.stream_command(request.text, _sync_callback, enable_audio_tts=request.enable_audio_tts)
            except Exception as ex:
                loop.call_soon_threadsafe(queue.put_nowait, ("__ERROR__", str(ex)))
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, "__END__")

        task = asyncio.create_task(_run_stream())

        while True:
            item = await queue.get()
            if item == "__END__":
                break
            if isinstance(item, tuple) and item[0] == "__ERROR__":
                yield f"event: error\ndata: {json.dumps({'error': item[1]})}\n\n"
                break

            full_collected.append(item)
            yield f"event: response_chunk\ndata: {json.dumps({'text': item})}\n\n"

        await task
        full_text = " ".join(full_collected)
        yield f"event: response_end\ndata: {json.dumps({'status': 'completed', 'full_text': full_text})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/api/v1/jarvis/cancel", response_model=CancelResponse, summary="Cancel Speech & Active Session")
async def cancel_speech(service: JarvisService = Depends(get_jarvis_service)):
    """Cancels active speech playback and flushes audio output queue."""
    try:
        return service.cancel_speech()
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error=ErrorDetail(code="CANCELLATION_FAILED", message=str(e))
            ).model_dump()
        )
