"""Document processing pipeline: normalize, extract metadata, mark processed."""

from sqlalchemy.ext.asyncio import AsyncSession

from processing.metadata import extract_metadata
from processing.normalize import normalize_text
from rag_contracts.processing import DocMetadata
from rag_db.models import Document


async def process_document(session: AsyncSession, document: Document) -> DocMetadata:
    """Run the processing pipeline for one document.

    Normalizes the raw text in place, extracts metadata, and marks the
    document ``processed``. Chunking and embedding are attached here in
    Phases 3 and 5.

    Args:
        session: Active async session (caller commits).
        document: The document to process.

    Returns:
        The extracted metadata.
    """
    normalized = normalize_text(document.raw_text)
    metadata = extract_metadata(document.filename, normalized)
    document.raw_text = normalized
    document.status = "processed"
    session.add(document)
    return metadata
