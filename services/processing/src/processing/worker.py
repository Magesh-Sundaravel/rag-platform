"""Job-queue worker: claim, run, retry, dead-letter (ADR-0005)."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from processing.chunking import Chunker
from processing.pipeline import process_document
from rag_common.logging import get_logger
from rag_db.models import Document, Job

logger = get_logger("processing.worker")

PROCESS_JOB_TYPE = "process_document"


async def claim_job(session: AsyncSession) -> Job | None:
    """Claim one pending job using FOR UPDATE SKIP LOCKED.

    The claim (status → ``in_progress``) is committed immediately so
    concurrent workers skip this row.

    Args:
        session: Active async session.

    Returns:
        The claimed job, or None when the queue is empty.
    """
    job = await session.scalar(
        select(Job)
        .where(Job.status == "pending")
        .order_by(Job.created_at)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if job is None:
        return None
    job.status = "in_progress"
    await session.commit()
    return job


async def _mark_failure(session: AsyncSession, job: Job, error: str) -> None:
    """Record a failed attempt: retry or dead-letter.

    Args:
        session: Active async session.
        job: The failed job.
        error: Error description stored on the job.
    """
    job.attempts += 1
    job.last_error = error[:2000]
    if job.attempts >= job.max_attempts:
        job.status = "dead"
        document = await session.get(Document, job.document_id)
        if document is not None:
            document.status = "failed"
        logger.error("job dead-lettered", job_id=str(job.id), error=error)
    else:
        job.status = "pending"
        logger.warning("job retry scheduled", job_id=str(job.id), attempts=job.attempts)
    await session.commit()


async def run_job(session: AsyncSession, job: Job, chunker: Chunker) -> None:
    """Execute one claimed job and persist the outcome.

    Args:
        session: Active async session.
        job: A job in ``in_progress`` state.
        chunker: Chunking strategy passed to the pipeline.
    """
    try:
        if job.job_type != PROCESS_JOB_TYPE:
            raise ValueError(f"unknown job type: {job.job_type}")
        document = await session.get(Document, job.document_id)
        if document is None:
            raise ValueError(f"document {job.document_id} not found")
        await process_document(session, document, chunker)
        job.status = "done"
        await session.commit()
        logger.info("job done", job_id=str(job.id), document_id=str(job.document_id))
    except Exception as exc:
        await session.rollback()
        job_row = await session.get(Job, job.id)
        if job_row is not None:
            await _mark_failure(session, job_row, str(exc))


async def run_once(factory: async_sessionmaker[AsyncSession], chunker: Chunker) -> bool:
    """Claim and run at most one job.

    Args:
        factory: Session factory.
        chunker: Chunking strategy passed to the pipeline.

    Returns:
        True if a job was processed, False if the queue was empty.
    """
    async with factory() as session:
        job = await claim_job(session)
        if job is None:
            return False
        await run_job(session, job, chunker)
        return True


async def worker_loop(
    factory: async_sessionmaker[AsyncSession],
    chunker: Chunker,
    *,
    poll_interval: float,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Poll the job queue until cancelled or the stop event is set.

    Args:
        factory: Session factory.
        chunker: Chunking strategy passed to the pipeline.
        poll_interval: Seconds to sleep when the queue is empty.
        stop_event: Optional cooperative stop signal (used by tests and
            graceful shutdown).
    """
    while stop_event is None or not stop_event.is_set():
        processed = await run_once(factory, chunker)
        if not processed:
            await asyncio.sleep(poll_interval)
