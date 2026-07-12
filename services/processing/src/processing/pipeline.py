"""Document processing pipeline: normalize, extract metadata, chunk, persist."""

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from processing.chunking import Chunker
from processing.metadata import estimate_tokens, extract_metadata
from processing.normalize import normalize_text
from rag_contracts.processing import DocMetadata
from rag_db.models import Chunk, Document
from rag_providers.embedding import EmbeddingProvider


async def process_document(
    session: AsyncSession, document: Document, chunker: Chunker, embedder: EmbeddingProvider
) -> DocMetadata:
    """Run the processing pipeline for one document.

    Normalizes the raw text, extracts metadata, replaces the document's
    chunks with freshly embedded ones (idempotent re-processing), and marks
    the document ``processed``.

    Args:
        session: Active async session (caller commits).
        document: The document to process.
        chunker: Configured chunking strategy.
        embedder: Embedding provider for chunk vectors.

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
    texts = chunker.chunk(normalized)
    vectors = await embedder.embed(texts) if texts else []
    for index, (text, vector) in enumerate(zip(texts, vectors, strict=True)):
        session.add(
            Chunk(
                document_id=document.id,
                chunk_index=index,
                text=text,
                token_count=estimate_tokens(text),
                meta=chunk_meta,
                embedding=vector,
            )
        )
    document.raw_text = normalized
    document.status = "processed"
    session.add(document)
    return metadata
