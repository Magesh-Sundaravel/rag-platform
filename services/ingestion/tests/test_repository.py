"""SQLite unit tests for the document repository."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ingestion import repository
from rag_common.exceptions import ConflictError, NotFoundError
from rag_db.models import Document, Job


async def _create(
    session: AsyncSession, filename: str = "a.txt", data: bytes = b"hello"
) -> Document:
    return await repository.create_document(
        session, filename=filename, content_type="text/plain", data=data, raw_text=data.decode()
    )


async def test_create_writes_document_and_pending_job(session: AsyncSession) -> None:
    doc = await _create(session)
    assert doc.version == 1
    assert doc.status == "pending"
    job = (await session.scalars(select(Job).where(Job.document_id == doc.id))).one()
    assert job.job_type == repository.PROCESS_DOCUMENT_JOB
    assert job.status == "pending"
    assert job.max_attempts == 3


async def test_duplicate_content_conflicts(session: AsyncSession) -> None:
    await _create(session)
    with pytest.raises(ConflictError):
        await _create(session, filename="other-name.txt")


async def test_changed_content_same_filename_bumps_version(session: AsyncSession) -> None:
    first = await _create(session, data=b"v1")
    second = await _create(session, data=b"v2")
    assert first.version == 1
    assert second.version == 2
    assert second.filename == first.filename


async def test_get_missing_raises(session: AsyncSession) -> None:
    with pytest.raises(NotFoundError):
        await repository.get_document(session, uuid.uuid4())


async def test_list_paginates(session: AsyncSession) -> None:
    for i in range(3):
        await _create(session, filename=f"f{i}.txt", data=f"content {i}".encode())
    items, total = await repository.list_documents(session, offset=1, limit=1)
    assert total == 3
    assert len(items) == 1


async def test_delete_removes_document(session: AsyncSession) -> None:
    doc = await _create(session)
    await repository.delete_document(session, doc.id)
    with pytest.raises(NotFoundError):
        await repository.get_document(session, doc.id)
