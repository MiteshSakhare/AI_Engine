"""
Health check endpoint.

File: backend/api/health.py
"""

from fastapi import APIRouter

from shared.config import settings
from shared.db import ping_db
from shared.feature_store import feature_store_client
from shared.model_registry import model_registry

health_router = APIRouter(tags=["Health"])


@health_router.get("/health")
async def health_check():
    """Readiness / liveness probe."""

    db_ok = await ping_db()

    return {
        "status": "ok" if db_ok else "degraded",
        "version": settings.MODEL_VERSION,
        "environment": settings.ENVIRONMENT,
        "engines": [
            "discovery",
            "benchmark",
            "strategy",
            "feedback",
        ],
        "database": "connected" if db_ok else "disconnected",
        "feature_store": "connected" if feature_store_client.available else "offline_fallback",
        "model_registry": "connected" if model_registry.available else "offline_fallback",
    }
