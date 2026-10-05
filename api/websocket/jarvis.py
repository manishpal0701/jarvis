"""
api/websocket/jarvis.py
Primary real-time WebSocket channel for Jarvis AI Assistant.
Handles real-time streaming, command execution, and immediate cancellation per client connection.
"""
import json
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
logger = logging.getLogger("JarvisWebSocket")
router = APIRouter(tags=["WebSocket"])

class ConnectionManager:
    """Manages active WebSocket client connections."""
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def send_json(self, websocket: WebSocket, data: dict):
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.warning(f"Failed to send JSON over WebSocket: {e}")

    async def broadcast(self, data: dict):
        """Broadcast JSON message to all active WebSocket clients."""
        connections = list(self.active_connections)
        for connection in connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to broadcast JSON over WebSocket: {e}")

manager = ConnectionManager()

_main_event_loop = None

def set_main_event_loop(loop: asyncio.AbstractEventLoop):
    global _main_event_loop
    _main_event_loop = loop

def broadcast_sync(data: dict):
    """Thread-safe sync wrapper to broadcast JSON events across all active WebSockets."""
    global _main_event_loop
    try:
        if _main_event_loop and _main_event_loop.is_running():
            asyncio.run_coroutine_threadsafe(manager.broadcast(data), _main_event_loop)
            return
        try:
            loop = asyncio.get_running_loop()
            if loop and loop.is_running():
                loop.create_task(manager.broadcast(data))
        except RuntimeError:
            pass
    except Exception as ex:
        logger.warning(f"broadcast_sync error: {ex}")


@router.websocket("/ws/jarvis")
async def jarvis_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    from api.services.jarvis_service import get_jarvis_service
    service = get_jarvis_service()


    # Trigger startup character voice event when WebSocket connects if not already spoken
    if not getattr(service.engine, "_startup_spoken", False):
        service.engine._startup_spoken = True
        def _speak_startup():
            import time
            time.sleep(0.3)
            service.engine.speech_coordinator.speak("JARVIS online. All systems operational.", wait=True)
        import threading
        threading.Thread(target=_speak_startup, name="JarvisStartupSpeechThread", daemon=True).start()

    active_task: asyncio.Task = None

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                msg = json.loads(raw_data)
            except json.JSONDecodeError:
                await manager.send_json(websocket, {
                    "type": "error",
                    "error": {"code": "MALFORMED_JSON", "message": "Invalid JSON format."}
                })
                continue

            msg_type = msg.get("type")

            # 1. Cancellation Request
            if msg_type == "cancel":
                if active_task and not active_task.done():
                    active_task.cancel()
                service.cancel_speech()
                await manager.send_json(websocket, {
                    "type": "cancelled",
                    "status": "ok"
                })
                continue

            # 1.5 Chat Command Input (Phase 2.5)
            if msg_type == "chat_command" or (msg_type == "command" and msg.get("source") == "chat"):
                text = msg.get("text", "").strip()
                enable_audio = msg.get("enable_audio_tts", True)
                import uuid
                req_id = msg.get("request_id") or f"req_{uuid.uuid4().hex[:8]}"

                if not text:
                    await manager.send_json(websocket, {
                        "type": "chat_error",
                        "request_id": req_id,
                        "error": {"code": "EMPTY_CHAT_COMMAND", "message": "Chat command text cannot be empty."}
                    })
                    continue

                if active_task and not active_task.done():
                    active_task.cancel()
                    service.cancel_speech()

                async def _chat_job():
                    try:
                        from datetime import datetime
                        await manager.send_json(websocket, {
                            "type": "execution_start",
                            "event": "execution_start",
                            "request_id": req_id,
                            "task": text,
                            "stage": "PLANNING"
                        })
                        resp_text = await service.execute_chat_command(text, source="chat", enable_audio_tts=enable_audio, request_id=req_id)
                        await manager.send_json(websocket, {
                            "type": "chat_response",
                            "request_id": req_id,
                            "text": resp_text,
                            "source": "chat",
                            "timestamp": datetime.now().isoformat()
                        })
                        await manager.send_json(websocket, {
                            "type": "execution_complete",
                            "event": "execution_complete",
                            "request_id": req_id,
                            "text": "Boss, kaam complete ho gaya."
                        })
                    except Exception as ex:
                        logger.error(f"Chat command processing error: {ex}")
                        await manager.send_json(websocket, {
                            "type": "chat_error",
                            "request_id": req_id,
                            "error": {"code": "CHAT_EXECUTION_ERROR", "message": str(ex)}
                        })

                active_task = asyncio.create_task(_chat_job())
                continue

            # 2. Command Execution Request
            if msg_type == "command":
                text = msg.get("text", "").strip()
                enable_audio = msg.get("enable_audio_tts", False)
                import uuid
                req_id = msg.get("request_id") or f"req_{uuid.uuid4().hex[:8]}"

                if not text:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "request_id": req_id,
                        "error": {"code": "INVALID_COMMAND", "message": "Command text cannot be empty."}
                    })
                    continue

                # Cancel previous active task if running
                if active_task and not active_task.done():
                    active_task.cancel()
                    service.cancel_speech()

                async def _stream_job():
                    queue: asyncio.Queue = asyncio.Queue()
                    loop = asyncio.get_running_loop()

                    def _sync_chunk_callback(chunk: str):
                        if chunk and chunk.strip():
                            loop.call_soon_threadsafe(queue.put_nowait, chunk.strip())

                    await manager.send_json(websocket, {
                        "type": "execution_start",
                        "event": "execution_start",
                        "request_id": req_id,
                        "task": text,
                        "stage": "PLANNING"
                    })
                    await manager.send_json(websocket, {"type": "response_start", "request_id": req_id})

                    collected_chunks = []

                    async def _run_service():
                        try:
                            await service.stream_command(text, _sync_chunk_callback, enable_audio_tts=enable_audio, request_id=req_id)
                        except Exception as ex:
                            loop.call_soon_threadsafe(queue.put_nowait, ("__ERROR__", str(ex)))
                        finally:
                            loop.call_soon_threadsafe(queue.put_nowait, "__END__")

                    service_task = asyncio.create_task(_run_service())

                    try:
                        while True:
                            try:
                                item = await asyncio.wait_for(queue.get(), timeout=5.0)
                            except asyncio.TimeoutError:
                                # Send heartbeat frame to prevent WebSocket keepalive timeouts during long CPU inference
                                await manager.send_json(websocket, {"type": "ping", "request_id": req_id})
                                continue

                            if item == "__END__":
                                break
                            if isinstance(item, tuple) and item[0] == "__ERROR__":
                                await manager.send_json(websocket, {
                                    "type": "error",
                                    "request_id": req_id,
                                    "error": {"code": "EXECUTION_ERROR", "message": item[1]}
                                })
                                break

                            collected_chunks.append(item)
                            await manager.send_json(websocket, {
                                "type": "response_chunk",
                                "request_id": req_id,
                                "text": item
                            })
                    except asyncio.CancelledError:
                        service.cancel_speech()
                        raise
                    finally:
                        await service_task
                        full_text = " ".join(collected_chunks)
                        await manager.send_json(websocket, {
                            "type": "response_end",
                            "request_id": req_id,
                            "full_text": full_text
                        })
                        await manager.send_json(websocket, {
                            "type": "execution_complete",
                            "event": "execution_complete",
                            "request_id": req_id,
                            "text": "Boss, kaam complete ho gaya."
                        })

                active_task = asyncio.create_task(_stream_job())
            else:
                await manager.send_json(websocket, {
                    "type": "error",
                    "error": {"code": "UNKNOWN_MESSAGE_TYPE", "message": f"Unrecognized message type: '{msg_type}'"}
                })

    except WebSocketDisconnect:
        if active_task and not active_task.done():
            active_task.cancel()
        service.cancel_speech()
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket unhandled exception: {e}")
        if active_task and not active_task.done():
            active_task.cancel()
        service.cancel_speech()
        manager.disconnect(websocket)
