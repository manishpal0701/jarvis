# JARVIS AI ASSISTANT — API DOCUMENTATION & FRONTEND CONTRACT

This document provides the complete, production-ready frontend integration contract for communicating with the Jarvis AI Assistant backend.

---

## 1. SERVER CONFIGURATION & STARTUP

- **Base HTTP URL**: `http://localhost:8000`
- **Base WebSocket URL**: `ws://localhost:8000/ws/jarvis`
- **API Version**: `v1` (`1.0.0`)
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **OpenAPI Schema JSON**: `http://localhost:8000/openapi.json`

### Development Startup Command
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Startup Command
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1
```

### Environment Variables
| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated list of allowed CORS origins for Next.js/React frontend |
| `MODEL_NAME` | `qwen3:8b` | Ollama model used for conversational response generation |
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | Local Ollama API endpoint |

---

## 2. EXACT API FILE MAP

| Endpoint | Method | Implementation File | Router Name | Request Schema | Response Schema | Service Layer Function | Existing Jarvis Backend Module |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| `/health` | GET | `api/routes/jarvis.py` | `router` | None | `HealthResponse` | Direct return | API Layer Health |
| `/api/v1/jarvis/state` | GET | `api/routes/jarvis.py` | `router` | None | `JarvisStateResponse` | `JarvisService.get_state()` | `core.state_machine.StateMachine` & `speech.speech_coordinator.SpeechCoordinator` |
| `/api/v1/jarvis/command` | POST | `api/routes/jarvis.py` | `router` | `CommandRequest` | `CommandResponse` | `JarvisService.execute_command()` | `conversation.command_router.CommandRouter` |
| `/api/v1/jarvis/stream` | POST | `api/routes/jarvis.py` | `router` | `CommandRequest` | `text/event-stream` (SSE) | `JarvisService.stream_command()` | `ai.ask_ollama.ask_ollama_streaming` & `conversation.command_router.CommandRouter` |
| `/api/v1/jarvis/cancel` | POST | `api/routes/jarvis.py` | `router` | None | `CancelResponse` | `JarvisService.cancel_speech()` | `speech.speech_coordinator.SpeechCoordinator.cancel_speech()` |
| `/ws/jarvis` | WS | `api/websocket/jarvis.py` | `router` | `WebSocketClientMessage` | `WebSocketServerEvent` | `JarvisService.stream_command()` / `cancel_speech()` | `conversation.command_router.CommandRouter` & `speech.speech_coordinator.SpeechCoordinator` |

---

## 3. HTTP ENDPOINTS CONTRACT

### A. Health Check
- **Endpoint**: `GET /health`
- **Response `200 OK`**:
```json
{
  "status": "ok",
  "service": "jarvis-api"
}
```

---

### B. Get Jarvis State
- **Endpoint**: `GET /api/v1/jarvis/state`
- **Response `200 OK`**:
```json
{
  "state": "WAITING_FOR_NEXT_COMMAND",
  "is_speaking": false,
  "is_listening": true
}
```

---

### C. Execute Text Command
- **Endpoint**: `POST /api/v1/jarvis/command`
- **Header**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "text": "open calculator",
  "enable_audio_tts": false
}
```
- **Response `200 OK`**:
```json
{
  "success": true,
  "text": "Opening Calculator, Boss.",
  "command": "open calculator"
}
```
- **Error Response `400 Bad Request`**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_COMMAND",
    "message": "Command text cannot be empty."
  }
}
```

---

### D. Streaming SSE Response
- **Endpoint**: `POST /api/v1/jarvis/stream`
- **Header**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "text": "Python kya hai?",
  "enable_audio_tts": false
}
```
- **Response Header**: `Content-Type: text/event-stream`
- **Stream Event Format**:
```text
event: response_start
data: {"status": "started"}

event: response_chunk
data: {"text": "Python is a high-level programming language."}

event: response_chunk
data: {"text": "It is widely used for artificial intelligence and web development."}

event: response_end
data: {"status": "completed", "full_text": "Python is a high-level programming language. It is widely used for artificial intelligence and web development."}
```

---

### E. Cancel Speech Playback
- **Endpoint**: `POST /api/v1/jarvis/cancel`
- **Response `200 OK`**:
```json
{
  "success": true,
  "message": "Speech playback and session cancelled successfully.",
  "status": "ok"
}
```

---

## 4. WEBSOCKET REAL-TIME CHANNEL

- **WebSocket URL**: `ws://localhost:8000/ws/jarvis`

### Client -> Server Messages

#### 1. Send Command
```json
{
  "type": "command",
  "text": "Jarvis, what time is it?",
  "enable_audio_tts": false
}
```

#### 2. Cancel Active Stream / Speech
```json
{
  "type": "cancel"
}
```

---

### Server -> Client Events

#### 1. Stream Start Event
```json
{
  "type": "response_start"
}
```

#### 2. Incremental Sentence Chunk Event
```json
{
  "type": "response_chunk",
  "text": "It's 11:45 AM, Boss."
}
```

#### 3. Stream End Event
```json
{
  "type": "response_end",
  "full_text": "It's 11:45 AM, Boss."
}
```

#### 4. Cancellation Event
```json
{
  "type": "cancelled",
  "status": "ok"
}
```

#### 5. Heartbeat Ping Event (Sent every 5s during long LLM inference)
```json
{
  "type": "ping"
}
```

#### 6. Error Event
```json
{
  "type": "error",
  "error": {
    "code": "INVALID_COMMAND",
    "message": "Command text cannot be empty."
  }
}
```

---

## 5. FRONTEND INTEGRATION CODE EXAMPLES (NEXT.JS / REACT)

### REST API Fetch Example
```javascript
async function sendCommand(text) {
  const response = await fetch('http://localhost:8000/api/v1/jarvis/command', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, enable_audio_tts: false })
  });
  const data = await response.json();
  if (data.success) {
    console.log('Jarvis Spoke:', data.text);
  }
}
```

### WebSocket Real-Time Connection Example
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/jarvis');

ws.onopen = () => {
  console.log('Connected to Jarvis WebSocket API');
  // Send a command
  ws.send(JSON.stringify({
    type: 'command',
    text: 'Jarvis, kya scene hai?',
    enable_audio_tts: false
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  switch (msg.type) {
    case 'response_start':
      console.log('Jarvis started responding...');
      break;
    case 'response_chunk':
      console.log('Chunk received:', msg.text);
      // Append text progressively to UI
      break;
    case 'response_end':
      console.log('Full Response Complete:', msg.full_text);
      break;
    case 'cancelled':
      console.log('Playback Cancelled');
      break;
    case 'error':
      console.error('API Error:', msg.error.message);
      break;
  }
};

// Trigger cancellation on UI stop button click
function handleCancel() {
  ws.send(JSON.stringify({ type: 'cancel' }));
}
```
