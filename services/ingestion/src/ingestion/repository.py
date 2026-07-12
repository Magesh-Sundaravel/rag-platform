"""Persistence operations for documents: dedup, versioning, and the job outbox."""

import hashlib
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_common.exceptions import ConflictError, NotFoundError
from rag_db.models import Document, Job

PROCESS_DOCUMENT_JOB = "process_document"


async def create_document(
    session: AsyncSession, *, filename: str, content_type: str, data: bytes, raw_text: str
) -> Document:
    """Insert a document plus its pending processing job in one transaction.

    Dedup: an existing row with the same sha256 of the raw bytes is a
    conflict. Versioning: a changed file re-uploaded under the same filename
    gets ``max(version) + 1``.

    Args:
        session: Open async session; committed on success.
        filename: Original filename.
        content_type: MIME type reported by the client.
        data: Raw uploaded bytes (hashed for dedup).
        raw_text: Text extracted from the upload.

    Returns:
        The persisted document.

    Raises:
        ConflictError: A document with identical content already exists.
    """
    content_hash = hashlib.sha256(data).hexdigest()
    existing = await session.scalar(
        select(Document.id).where(Document.content_hash == content_hash)
    )
    if existing is not None:
        raise ConflictError(f"identical content already ingested as document {existing}")

    max_version = await session.scalar(
        select(func.max(Document.version)).where(Document.filename == filename)
    )
    document = Document(
        filename=filename,
        content_type=content_type,
        content_hash=content_hash,
        version=(max_version or 0) + 1,
        raw_text=raw_text,
    )
    session.add(document)
    await session.flush()
    session.add(Job(document_id=document.id, job_type=PROCESS_DOCUMENT_JOB))
    await session.commit()
    return document


async def get_document(session: AsyncSession, document_id: uuid.UUID) -> Document:
    """Return the document with the given id.

    Args:
        session: Open async session.
        document_id: Primary key to look up.

    Returns:
        The matching document.

    Raises:
        NotFoundError: No document with that id exists.
    """
    document = await session.get(Document, document_id)
    if document is None:
        raise NotFoundError(f"document {document_id} not found")
    return document


async def list_documents(
    session: AsyncSession, *, offset: int, limit: int
) -> tuple[list[Document], int]:
    """Return one page of documents (newest first) and the total count.

    Args:
        session: Open async session.
        offset: Rows to skip.
        limit: Maximum rows to return.

    Returns:
        The page of documents and the total number of documents.
    """
    total = await session.scalar(select(func.count()).select_from(Document)) or 0
    rows = await session.scalars(
        select(Document)
        .order_by(Document.created_at.desc(), Document.id)
        .offset(offset)
        .limit(limit)
    )
    return list(rows), total


async def delete_document(session: AsyncSession, document_id: uuid.UUID) -> None:
    """Delete a document (jobs cascade at the database level).

    Args:
        session: Open async session; committed on success.
        document_id: Primary key of the document to delete.

    Raises:
        NotFoundError: No document with that id exists.
    """
    document = await get_document(session, document_id)
    await session.delete(document)
    await session.commit()
