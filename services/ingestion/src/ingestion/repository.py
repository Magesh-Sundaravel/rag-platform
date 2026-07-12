"""Persistence operations for documents (dedup, versioning, job outbox)."""

import hashlib
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_common.exceptions import ConflictError, NotFoundError
from rag_db.models import Document, Job

PROCESS_JOB_TYPE = "process_document"


def sha256_hex(data: bytes) -> str:
    """Return the sha256 hex digest of the given bytes.

    Args:
        data: Raw bytes to hash.

    Returns:
        64-character lowercase hex digest.
    """
    return hashlib.sha256(data).hexdigest()


async def create_document(
    session: AsyncSession,
    *,
    filename: str,
    content_type: str,
    raw_bytes: bytes,
    raw_text: str,
) -> Document:
    """Insert a document with dedup + versioning and a pending job row.

    Exact duplicates (same content hash) are rejected. A re-upload of the
    same filename with different content gets ``version = max(version) + 1``.
    A ``pending`` processing job is written in the same transaction (outbox).

    Args:
        session: Active async session (caller controls transaction scope).
        filename: Original filename.
        content_type: MIME type reported by the client.
        raw_bytes: Original file bytes (hashed for dedup).
        raw_text: Extracted text to persist.

    Returns:
        The persisted :class:`Document`.

    Raises:
        ConflictError: If a document with identical content already exists.
    """
    content_hash = sha256_hex(raw_bytes)
    existing = await session.scalar(select(Document).where(Document.content_hash == content_hash))
    if existing is not None:
        raise ConflictError(f"duplicate content: already ingested as document {existing.id}")

    max_version = await session.scalar(
        select(func.max(Document.version)).where(Document.filename == filename)
    )
    document = Document(
        filename=filename,
        content_type=content_type,
        content_hash=content_hash,
        version=(max_version or 0) + 1,
        status="pending",
        raw_text=raw_text,
    )
    session.add(document)
    await session.flush()
    session.add(Job(document_id=document.id, job_type=PROCESS_JOB_TYPE, status="pending"))
    await session.commit()
    return document


async def get_document(session: AsyncSession, document_id: uuid.UUID) -> Document:
    """Fetch one document by id.

    Args:
        session: Active async session.
        document_id: Primary key.

    Returns:
        The :class:`Document`.

    Raises:
        NotFoundError: If no such document exists.
    """
    document = await session.get(Document, document_id)
    if document is None:
        raise NotFoundError(f"document {document_id} not found")
    return document


async def list_documents(
    session: AsyncSession, *, offset: int, limit: int
) -> tuple[list[Document], int]:
    """List documents ordered by creation time (newest first).

    Args:
        session: Active async session.
        offset: Rows to skip.
        limit: Max rows to return.

    Returns:
        Tuple of (documents page, total count).
    """
    total = await session.scalar(select(func.count()).select_from(Document)) or 0
    rows = await session.scalars(
        select(Document).order_by(Document.created_at.desc()).offset(offset).limit(limit)
    )
    return list(rows), total


async def delete_document(session: AsyncSession, document_id: uuid.UUID) -> None:
    """Delete a document (jobs cascade via FK).

    Args:
        session: Active async session.
        document_id: Primary key.

    Raises:
        NotFoundError: If no such document exists.
    """
    document = await get_document(session, document_id)
    await session.execute(delete(Job).where(Job.document_id == document.id))
    await session.delete(document)
    await session.commit()
