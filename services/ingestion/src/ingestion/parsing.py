"""Extract raw text from uploaded files (txt, md, pdf)."""

from io import BytesIO
from pathlib import PurePosixPath

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from rag_common.exceptions import InvalidInputError

_TEXT_SUFFIXES = {".txt", ".md"}


def extract_text(filename: str, data: bytes) -> str:
    """Extract raw text from an uploaded file based on its extension.

    Args:
        filename: Original filename; the suffix selects the parser.
        data: Raw file bytes.

    Returns:
        The extracted text.

    Raises:
        InvalidInputError: Unsupported file type, undecodable text, or a
            corrupt PDF.
    """
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix in _TEXT_SUFFIXES:
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InvalidInputError(f"{filename} is not valid UTF-8 text") from exc
    if suffix == ".pdf":
        try:
            reader = PdfReader(BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except PyPdfError as exc:
            raise InvalidInputError(f"{filename} is not a readable PDF") from exc
    raise InvalidInputError(f"unsupported file type: {suffix or '(no extension)'}")
