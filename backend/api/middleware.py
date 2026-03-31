"""
Request logging, error handling, and trace ID injection middleware.

File: backend/api/middleware.py
"""

import time
import uuid
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shared.config import settings

logger = logging.getLogger("bravola.middleware")


def add_middleware(app: FastAPI) -> None:
    """Register all middleware on the app."""

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        """Log every inbound request with merchant_id + latency + trace_id."""

        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        request.state.trace_id = trace_id

        start = time.time()
        response = await call_next(request)
        latency = round(time.time() - start, 4)

        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Process-Time"] = str(latency)

        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_s": latency,
                "trace_id": trace_id,
            },
        )

        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Catch unhandled exceptions → structured error JSON."""

        trace_id = getattr(request.state, "trace_id", "unknown")
        logger.error(
            "Unhandled exception",
            extra={"trace_id": trace_id, "error": str(exc)},
            exc_info=True,
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
                "trace_id": trace_id,
            },
        )
