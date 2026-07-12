"""Tests for text extraction from uploaded files."""

from collections.abc import Callable

import pytest

from ingestion.parsing import extract_text
from rag_common.exceptions import InvalidInputError


def test_txt() -> None:
    assert extract_text("notes.txt", b"hello world") == "hello world"


def test_md() -> None:
    assert extract_text("README.md", b"# Title\nbody") == "# Title\nbody"


def test_pdf(pdf_factory: Callable[[str], bytes]) -> None:
    assert "Hello PDF" in extract_text("doc.pdf", pdf_factory("Hello PDF"))


def test_bad_utf8() -> None:
    with pytest.raises(InvalidInputError, match="not valid UTF-8"):
        extract_text("notes.txt", b"\xff\xfe\xfa")


def test_corrupt_pdf() -> None:
    with pytest.raises(InvalidInputError, match="not a readable PDF"):
        extract_text("doc.pdf", b"%PDF-1.4 garbage")


def test_unsupported_extension() -> None:
    with pytest.raises(InvalidInputError, match=r"unsupported file type: \.docx"):
        extract_text("report.docx", b"anything")


def test_no_extension() -> None:
    with pytest.raises(InvalidInputError, match="no extension"):
        extract_text("Makefile", b"anything")
