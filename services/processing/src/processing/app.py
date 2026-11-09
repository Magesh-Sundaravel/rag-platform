"""ASGI entrypoint for the processing service (API + background worker)."""

import asyncio
import contextlib
from collections.abc import AsyncIterator

import boto3
from fastapi import FastAPI

from processing import __version__
from processing.chunking import build_chunker
from processing.config import Settings
from processing.worker import QueueConfig, worker_loop
from rag_common.app_factory import create_app
from rag_db.session import create_engine, create_session_factory
from rag_providers.factory import build_embedding_provider

settings = Settings()


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Start the SQS consumer for the app's lifetime (if enabled)."""
    if not settings.worker_enabled:
        yield
        return
    engine = create_engine(settings.database_url)
    factory = create_session_factory(engine)
    chunker = build_chunker(settings.chunk_strategy, settings.chunk_size, settings.chunk_overlap)
    embedder = build_embedding_provider(settings.embedding_provider)
    queue = QueueConfig(
        client=boto3.client("sqs", endpoint_url=settings.sqs_endpoint_url),
        url=settings.processing_queue_url,
        wait_seconds=settings.queue_wait_seconds,
        max_receive_count=settings.max_receive_count,
    )
    stop = asyncio.Event()
    task = asyncio.create_task(worker_loop(factory, queue, chunker, embedder, stop_event=stop))
    try:
        yield
    finally:
        stop.set()
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        await engine.dispose()


app = create_app(settings, title="Processing Service", version=__version__, lifespan=lifespan)
