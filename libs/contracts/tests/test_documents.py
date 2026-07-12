"""Round-trip tests for the document contracts."""

import uuid
from datetime import UTC, datetime

from rag_contracts.documents import DocumentListOut, DocumentOut, DocumentStatus


def _sample_document() -> DocumentOut:
    return DocumentOut(
        id=uuid.uuid4(),
        filename="report.pdf",
        content_type="application/pdf",
        content_hash="a" * 64,
        version=1,
        status=DocumentStatus.PENDING,
        created_at=datetime.now(tz=UTC),
    )


def test_document_out_round_trip() -> None:
    doc = _sample_document()
    assert DocumentOut.model_validate_json(doc.model_dump_json()) == doc


def test_document_list_out_round_trip() -> None:
    page = DocumentListOut(items=[_sample_document()], total=1, offset=0, limit=20)
    assert DocumentListOut.model_validate_json(page.model_dump_json()) == page


def test_document_out_from_attributes() -> None:
    class Row:
        id = uuid.uuid4()
        filename = "notes.txt"
        content_type = "text/plain"
        content_hash = "b" * 64
        version = 2
        status = "processed"
        created_at = datetime.now(tz=UTC)

    doc = DocumentOut.model_validate(Row())
    assert doc.status is DocumentStatus.PROCESSED
    assert doc.version == 2
