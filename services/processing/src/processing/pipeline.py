"""Document processing pipeline: normalize, extract metadata, chunk, persist."""

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from processing.chunking import Chunker
from processing.metadata import estimate_tokens, extract_metadata
from processing.normalize import normalize_text
from rag_contracts.processing import DocMetadata
from rag_db.models import Chunk, Document


async def process_document(
    session: AsyncSession, document: Document, chunker: Chunker
) -> DocMetadata:
    """Run the processing pipeline for one document.

    Normalizes the raw text, extracts metadata, replaces the document's
    chunks (idempotent re-processing), and marks the document ``processed``.
    Embedding is attached in Phase 5.

    Args:
        session: Active async session (caller commits).
        document: The document to process.
        chunker: Configured chunking strategy.

    Returns:
        The extracted metadata.
    """
    normalized = normalize_text(document.raw_text)
    metadata = extract_metadata(document.filename, normalized)
    await session.execute(delete(Chunk).where(Chunk.document_id == document.id))
    chunk_meta = {
        "title": metadata.title,
        "language": metadata.language,
        "filename": document.filename,
    }
    for index, text in enumerate(chunker.chunk(normalized)):
        session.add(
            Chunk(
                document_id=document.id,
                chunk_index=index,
                text=text,
                token_count=estimate_tokens(text),
                meta=chunk_meta,
            )
        )
    document.raw_text = normalized
    document.status = "processed"
    session.add(document)
    return metadata
