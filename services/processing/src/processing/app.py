"""ASGI entrypoint for the processing service (API + background worker)."""

import asyncio
import contextlib
from collections.abc import AsyncIterator

from fastapi import FastAPI

from processing import __version__
from processing.config import Settings
from processing.worker import worker_loop
from rag_common.app_factory import create_app
from rag_db.session import create_engine, create_session_factory

settings = Settings()


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Start the job-queue worker for the app's lifetime (if enabled)."""
    if not settings.worker_enabled:
        yield
        return
    engine = create_engine(settings.database_url)
    factory = create_session_factory(engine)
    stop = asyncio.Event()
    task = asyncio.create_task(
        worker_loop(factory, poll_interval=settings.poll_interval_seconds, stop_event=stop)
    )
    try:
        yield
    finally:
        stop.set()
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        await engine.dispose()


app = create_app(settings, title="Processing Service", version=__version__, lifespan=lifespan)
