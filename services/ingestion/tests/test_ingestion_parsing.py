"""Unit tests for file parsing."""

import pytest
from ingestion_test_helpers import make_pdf

from ingestion.parsing import extract_text
from rag_common.exceptions import InvalidInputError


def test_txt_roundtrip() -> None:
    assert extract_text("a.txt", b"hello world") == "hello world"


def test_md_roundtrip() -> None:
    assert extract_text("notes.MD", b"# Title\ncontent") == "# Title\ncontent"


def test_invalid_utf8_rejected() -> None:
    with pytest.raises(InvalidInputError):
        extract_text("a.txt", b"\xff\xfe\xff")


def test_unsupported_type_rejected() -> None:
    with pytest.raises(InvalidInputError, match="unsupported"):
        extract_text("image.png", b"\x89PNG")


def test_pdf_extraction() -> None:
    assert "Hello PDF" in extract_text("doc.pdf", make_pdf("Hello PDF"))


def test_corrupt_pdf_rejected() -> None:
    with pytest.raises(InvalidInputError):
        extract_text("bad.pdf", b"%PDF-1.4 garbage")
