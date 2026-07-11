"""FastAPI application factory used by every service.

Centralizes the cross-cutting concerns each service would otherwise
duplicate: health/readiness endpoints, structured request logging, and a
consistent JSON error envelope for domain exceptions.
"""

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from rag_common.config import BaseServiceSettings
from rag_common.exceptions import RagPlatformError
from rag_common.logging import configure_logging, get_logger


def create_app(settings: BaseServiceSettings, *, title: str, version: str = "0.1.0") -> FastAPI:
    """Build a FastAPI app with the platform's standard wiring.

    Args:
        settings: Service settings (name, environment, log level, bind info).
        title: Human-readable API title shown in OpenAPI docs.
        version: API version string.

    Returns:
        A configured FastAPI application.
    """
    configure_logging(settings)
    logger = get_logger(settings.service_name)
    app = FastAPI(title=title, version=version)

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        """Liveness probe: process is up."""
        return {"status": "ok", "service": settings.service_name}

    @app.get("/ready", tags=["ops"])
    async def ready() -> dict[str, str]:
        """Readiness probe: safe to receive traffic."""
        return {"status": "ready"}

    @app.exception_handler(RagPlatformError)
    async def platform_error_handler(_request: Request, exc: RagPlatformError) -> JSONResponse:
        """Render domain errors as the standard JSON error envelope."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "detail": exc.detail}},
        )

    @app.middleware("http")
    async def log_requests(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Log one structured line per request with latency."""
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        return response

    return app
