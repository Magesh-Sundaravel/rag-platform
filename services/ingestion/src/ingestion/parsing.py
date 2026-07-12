"""File parsing: turn an uploaded file into raw text."""

import io

from pypdf import PdfReader

from rag_common.exceptions import InvalidInputError

_TEXT_SUFFIXES = (".txt", ".md")


def extract_text(filename: str, data: bytes) -> str:
    """Extract raw text from an uploaded file.

    Args:
        filename: Original filename; the suffix selects the parser.
        data: Raw file bytes.

    Returns:
        The extracted text.

    Raises:
        InvalidInputError: If the file type is unsupported, the text is not
            valid UTF-8, or the PDF contains no extractable text.
    """
    lowered = filename.lower()
    if lowered.endswith(_TEXT_SUFFIXES):
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InvalidInputError(f"{filename} is not valid UTF-8 text") from exc
    if lowered.endswith(".pdf"):
        return _extract_pdf(filename, data)
    raise InvalidInputError(f"unsupported file type: {filename} (allowed: .txt, .md, .pdf)")


def _extract_pdf(filename: str, data: bytes) -> str:
    """Extract text from PDF bytes using pypdf.

    Args:
        filename: Original filename (for error messages).
        data: Raw PDF bytes.

    Returns:
        Concatenated page text.

    Raises:
        InvalidInputError: If the PDF cannot be parsed or has no text.
    """
    try:
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as exc:  # pypdf raises many exception types
        raise InvalidInputError(f"could not parse PDF {filename}") from exc
    if not text:
        raise InvalidInputError(f"PDF {filename} contains no extractable text")
    return text
