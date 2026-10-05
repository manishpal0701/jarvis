"""
api/schemas/jarvis.py
Pydantic schemas for Jarvis REST API and WebSocket contracts.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "jarvis-api"

class CommandRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Natural language command or prompt for Jarvis")
    enable_audio_tts: Optional[bool] = Field(default=False, description="Whether to trigger local server TTS audio output")

class CommandResponse(BaseModel):
    success: bool = True
    text: str = Field(..., description="Spoken text response from Jarvis")
    command: str = Field(..., description="Original command executed")

class JarvisStateResponse(BaseModel):
    state: str = Field(..., description="Current StateMachine state name")
    is_speaking: bool = Field(..., description="True if TTS audio output is currently active")
    is_listening: bool = Field(..., description="True if microphone listening is active")

class CancelResponse(BaseModel):
    success: bool = True
    message: str = "Speech playback and session cancelled successfully."
    status: str = "ok"

class ErrorDetail(BaseModel):
    code: str = Field(..., description="Standardized machine-readable error code")
    message: str = Field(..., description="Human-readable error description")

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail

class WebSocketClientMessage(BaseModel):
    type: str = Field(..., description="Message type: 'command' or 'cancel'")
    text: Optional[str] = Field(default=None, description="Command text when type is 'command'")
    enable_audio_tts: Optional[bool] = Field(default=False, description="Whether to trigger local TTS audio output")

class WebSocketServerEvent(BaseModel):
    type: str = Field(..., description="Event type: 'response_start', 'response_chunk', 'response_end', 'response', 'cancelled', 'error'")
    text: Optional[str] = None
    status: Optional[str] = None
    full_text: Optional[str] = None
    error: Optional[ErrorDetail] = None
