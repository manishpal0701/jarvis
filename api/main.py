"""
api/main.py
Production FastAPI Application Entry Point for Jarvis AI Assistant Backend.
Exposes REST endpoints, Server-Sent Events, OpenAPI Swagger docs, and WebSocket streaming.
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Ensure root workspace directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("JarvisAPI")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown routines."""
    logger.info("==========================================")
    logger.info("      JARVIS FASTAPI SERVICE STARTUP      ")
    logger.info("==========================================")
    
    # Pre-initialize Jarvis Conversation Engine
    from api.services.jarvis_service import get_jarvis_service
    service = get_jarvis_service()
    logger.info("Jarvis Conversation Engine initialized.")

    import asyncio
    from api.websocket.jarvis import set_main_event_loop
    set_main_event_loop(asyncio.get_running_loop())

    import speech
    speech.initialize()

    service.engine.start_in_background()
    logger.info("Jarvis Voice & Wake Word Listener thread started.")

    # Pre-warm desktop AppLauncher installed app cache in background thread
    def _prewarm_app_launcher():
        try:
            from tools.computer.app_launcher import AppLauncher
            AppLauncher.get_installed_apps()
            logger.info("AppLauncher installed applications cache pre-warmed.")
        except Exception as ex:
            logger.warning(f"AppLauncher prewarm notice: {ex}")

    import threading
    threading.Thread(target=_prewarm_app_launcher, name="AppLauncherPrewarmThread", daemon=True).start()

    yield

    logger.info("Jarvis FastAPI Service shutting down...")
    from conversation.conversation_engine import ConversationEngine
    engine = ConversationEngine()
    if hasattr(engine, "speech_coordinator"):
        engine.speech_coordinator.cancel_speech()

app = FastAPI(
    title="JARVIS AI Assistant API",
    version="1.0.0",
    description="Production-ready FastAPI REST and WebSocket API for Jarvis Personal AI Assistant.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS Middleware
cors_origins_env = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173")
origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Error Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "INVALID_COMMAND",
                "message": "Malformed request parameters or invalid JSON body."
            }
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred."
            }
        }
    )

# Include API Routers
from api.routes.jarvis import router as jarvis_rest_router
from api.routes.apps import router as apps_router
from api.websocket.jarvis import router as jarvis_ws_router
from fastapi.staticfiles import StaticFiles

SPEECH_CACHE_DIR = os.path.join(BASE_DIR, "speech", "cache")
os.makedirs(SPEECH_CACHE_DIR, exist_ok=True)
app.mount("/speech/cache", StaticFiles(directory=SPEECH_CACHE_DIR), name="speech_cache")

app.include_router(jarvis_rest_router)
app.include_router(apps_router)
app.include_router(jarvis_ws_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
