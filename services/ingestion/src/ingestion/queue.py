"""SQS publisher for processing hand-off (ADR-0009)."""

import asyncio
import uuid
from typing import Any

import boto3

from ingestion.config import Settings
from rag_contracts.processing import ProcessDocumentMessage


class ProcessingQueue:
    """Sends ``process_document`` messages to the processing SQS queue."""

    def __init__(self, queue_url: str, client: Any) -> None:
        """Bind the queue URL and a boto3 SQS client.

        Args:
            queue_url: Target SQS queue URL.
            client: boto3 SQS client (or a test double with ``send_message``).
        """
        self.queue_url = queue_url
        self._client = client

    async def enqueue(self, document_id: uuid.UUID) -> None:
        """Ask processing to process one document.

        Args:
            document_id: The committed document's primary key.
        """
        body = ProcessDocumentMessage(document_id=document_id).model_dump_json()
        await asyncio.to_thread(
            self._client.send_message, QueueUrl=self.queue_url, MessageBody=body
        )


_queue: ProcessingQueue | None = None


def get_queue() -> ProcessingQueue:
    """FastAPI dependency returning the process-wide queue, creating it lazily.

    Returns:
        The shared :class:`ProcessingQueue`.
    """
    global _queue
    if _queue is None:
        settings = Settings()
        client = boto3.client("sqs", endpoint_url=settings.sqs_endpoint_url)
        _queue = ProcessingQueue(settings.processing_queue_url, client)
    return _queue
