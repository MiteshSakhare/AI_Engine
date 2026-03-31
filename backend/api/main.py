"""
FastAPI Application — Bravola AI Engine

Registers all 4 engine routers and manages lifecycle.

File: backend/api/main.py
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import settings
from shared.logging import setup_logging, get_logger
from shared.db import init_db, close_db
from shared.model_registry import model_registry
from api.middleware import add_middleware
from api.health import health_router
from api.chat import router as chat_router

# Engine routers
from engines.discovery.router import router as discovery_router
from engines.benchmark.router import router as benchmark_router
from engines.strategy.router import router as strategy_router
from engines.feedback.router import router as feedback_router

# Ollama client
from shared.ollama_client import ollama_client

logger = get_logger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""

    # ── STARTUP ──────────────────────────────────────
    setup_logging()
    logger.info("Starting Bravola AI Engine", version=settings.MODEL_VERSION)

    # Database
    try:
        await init_db()
        logger.info("Database initialised")
    except Exception:
        logger.exception("Database initialisation failed")
        raise

    # Model registry
    try:
        model_registry.start_polling()
        logger.info("Model registry polling started")
    except Exception:
        logger.warning("Model registry not available — engines will use defaults")

    # Ollama health check
    try:
        await ollama_client.check_health()
    except Exception:
        logger.warning("Ollama not available — reasoning will use heuristic fallback")

    yield

    # ── SHUTDOWN ─────────────────────────────────────
    logger.info("Shutting down Bravola AI Engine")
    model_registry.stop_polling()
    await close_db()


# ── App instance ──────────────────────────────────────

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered growth marketing strategist platform for Shopify merchants",
    version=settings.MODEL_VERSION,
    openapi_url="/engine/openapi.json",
    docs_url="/docs",
    debug=settings.DEBUG,
    lifespan=lifespan,
)


# ── CORS ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Middleware ────────────────────────────────────────

add_middleware(app)


# ── Routers ──────────────────────────────────────────

app.include_router(health_router)
app.include_router(discovery_router,  prefix="/engine/v1", tags=["Discovery Engine"])
app.include_router(benchmark_router,  prefix="/engine/v1", tags=["Benchmark Engine"])
app.include_router(strategy_router,   prefix="/engine/v1", tags=["Strategy Engine"])
app.include_router(feedback_router,   prefix="/engine/v1", tags=["Feedback Engine"])
app.include_router(chat_router,       prefix="/api/v1",    tags=["Chat (Ollama)"])


# ── Root ─────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "Bravola AI Engine is Online",
        "docs": "/docs",
        "health": "/health",
        "version": settings.MODEL_VERSION,
    }
