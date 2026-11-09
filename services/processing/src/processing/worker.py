"""SQS consumer: receive, process, delete; retries and DLQ via redrive (ADR-0009)."""

import asyncio
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from processing.chunking import Chunker
from processing.pipeline import process_document
from rag_common.logging import get_logger
from rag_contracts.processing import ProcessDocumentMessage
from rag_db.models import Document
from rag_providers.embedding import EmbeddingProvider

logger = get_logger("processing.worker")

LOOP_ERROR_BACKOFF_SECONDS = 1.0


@dataclass(frozen=True)
class QueueConfig:
    """Where and how to consume processing messages.

    Attributes:
        client: boto3 SQS client (or a test double).
        url: SQS queue URL.
        wait_seconds: Long-poll duration per receive call.
        max_receive_count: Must equal the queue's redrive ``maxReceiveCount``;
            the attempt with this receive count marks the document ``failed``.
    """

    client: Any
    url: str
    wait_seconds: int
    max_receive_count: int


async def handle_message(
    factory: async_sessionmaker[AsyncSession],
    message: dict[str, Any],
    chunker: Chunker,
    embedder: EmbeddingProvider,
    *,
    max_receive_count: int,
) -> bool:
    """Process one SQS message.

    Args:
        factory: Session factory.
        message: Raw SQS message (``Body`` and ``Attributes``).
        chunker: Chunking strategy passed to the pipeline.
        embedder: Embedding provider passed to the pipeline.
        max_receive_count: Receive count at which a failure is final.

    Returns:
        True if the message should be deleted (done, or nothing to do);
        False to leave it for SQS to redeliver or dead-letter.
    """
    try:
        body = ProcessDocumentMessage.model_validate_json(message["Body"])
    except ValidationError as exc:
        logger.error("invalid message body", message_id=message.get("MessageId"), error=str(exc))
        return False

    receive_count = int(message.get("Attributes", {}).get("ApproximateReceiveCount", "1"))
    async with factory() as session:
        document = await session.get(Document, body.document_id)
        if document is None:
            logger.warning(
                "document not found; dropping message", document_id=str(body.document_id)
            )
            return True
        try:
            await process_document(session, document, chunker, embedder)
            await session.commit()
        except Exception as exc:
            await session.rollback()
            if receive_count >= max_receive_count:
                # Conditional so a concurrent duplicate delivery that already
                # succeeded is never overwritten with "failed".
                await session.execute(
                    update(Document)
                    .where(Document.id == body.document_id, Document.status != "processed")
                    .values(status="failed")
                )
                await session.commit()
                logger.error(
                    "processing failed; dead-lettering",
                    document_id=str(body.document_id),
                    attempts=receive_count,
                    error=str(exc),
                )
            else:
                logger.warning(
                    "processing failed; will retry",
                    document_id=str(body.document_id),
                    attempts=receive_count,
                    error=str(exc),
                )
            return False
    logger.info("document processed", document_id=str(body.document_id))
    return True


async def run_once(
    factory: async_sessionmaker[AsyncSession],
    queue: QueueConfig,
    chunker: Chunker,
    embedder: EmbeddingProvider,
) -> bool:
    """Receive and handle at most one message.

    Args:
        factory: Session factory.
        queue: Queue client and settings.
        chunker: Chunking strategy passed to the pipeline.
        embedder: Embedding provider passed to the pipeline.

    Returns:
        True if a message was received, False if the long poll came back empty.
    """
    response = await asyncio.to_thread(
        queue.client.receive_message,
        QueueUrl=queue.url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=queue.wait_seconds,
        AttributeNames=["ApproximateReceiveCount"],
    )
    messages = response.get("Messages", [])
    for message in messages:
        if await handle_message(
            factory, message, chunker, embedder, max_receive_count=queue.max_receive_count
        ):
            await asyncio.to_thread(
                queue.client.delete_message,
                QueueUrl=queue.url,
                ReceiptHandle=message["ReceiptHandle"],
            )
    return bool(messages)


async def worker_loop(
    factory: async_sessionmaker[AsyncSession],
    queue: QueueConfig,
    chunker: Chunker,
    embedder: EmbeddingProvider,
    *,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Consume the queue until cancelled or the stop event is set.

    Args:
        factory: Session factory.
        queue: Queue client and settings.
        chunker: Chunking strategy passed to the pipeline.
        embedder: Embedding provider passed to the pipeline.
        stop_event: Optional cooperative stop signal (used by tests and
            graceful shutdown).
    """
    while stop_event is None or not stop_event.is_set():
        try:
            await run_once(factory, queue, chunker, embedder)
        except Exception as exc:
            # Any error (SQS or database) must not kill the consumer: the app
            # would stay healthy while nothing consumes. Unacked messages are
            # redelivered by SQS after the visibility timeout.
            logger.error("worker iteration failed; backing off", error=str(exc))
            await asyncio.sleep(LOOP_ERROR_BACKOFF_SECONDS)
