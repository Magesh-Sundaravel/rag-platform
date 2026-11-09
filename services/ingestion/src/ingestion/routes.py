"""HTTP routes for the ingestion service."""

import uuid
from typing import Annotated

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ingestion import repository
from ingestion.db import get_session
from ingestion.parsing import extract_text
from ingestion.queue import ProcessingQueue, get_queue
from rag_common.exceptions import ServiceUnavailableError
from rag_common.logging import get_logger
from rag_contracts.documents import DocumentListOut, DocumentOut

logger = get_logger("ingestion.routes")

router = APIRouter(prefix="/documents", tags=["documents"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
QueueDep = Annotated[ProcessingQueue, Depends(get_queue)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile, session: SessionDep, queue: QueueDep) -> DocumentOut:
    """Upload a document (txt/md/pdf); dedups by content hash and versions by filename.

    The document is committed, then a processing message is sent to SQS. If
    the send fails the new document is deleted again so the client can retry;
    boto errors map to 503. Re-uploading content that is still ``pending``
    re-sends its message instead of returning 409 (ADR-0009).
    """
    data = await file.read()
    filename = file.filename or "upload"
    document = await repository.find_pending_duplicate(session, data)
    created = document is None
    if document is None:
        document = await repository.create_document(
            session,
            filename=filename,
            content_type=file.content_type or "application/octet-stream",
            raw_bytes=data,
            raw_text=extract_text(filename, data),
        )
    try:
        await queue.enqueue(document.id)
    except Exception as exc:
        logger.error("enqueue failed", document_id=str(document.id), error=str(exc))
        if created:
            try:
                await repository.delete_document(session, document.id)
            except Exception as cleanup_exc:
                # Left pending; a re-upload of the same content re-sends it.
                logger.error(
                    "rollback of upload failed",
                    document_id=str(document.id),
                    error=str(cleanup_exc),
                )
        if isinstance(exc, BotoCoreError | ClientError):
            raise ServiceUnavailableError("processing queue unavailable; retry the upload") from exc
        raise
    return DocumentOut.model_validate(document)


@router.get("/{document_id}")
async def get_document(document_id: uuid.UUID, session: SessionDep) -> DocumentOut:
    """Fetch a single document by id."""
    return DocumentOut.model_validate(await repository.get_document(session, document_id))


@router.get("")
async def list_documents(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> DocumentListOut:
    """List documents, newest first, with offset/limit pagination."""
    items, total = await repository.list_documents(session, offset=offset, limit=limit)
    return DocumentListOut(
        items=[DocumentOut.model_validate(d) for d in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: uuid.UUID, session: SessionDep) -> None:
    """Delete a document and its chunks."""
    await repository.delete_document(session, document_id)
