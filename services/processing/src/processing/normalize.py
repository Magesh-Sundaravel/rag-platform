"""Text normalization: unicode and whitespace cleanup."""

import re
import unicodedata

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SPACES = re.compile(r"[ \t]+")
_MANY_NEWLINES = re.compile(r"\n{3,}")
_TRAILING = re.compile(r"[ \t]+\n")


def normalize_text(text: str) -> str:
    """Normalize raw document text for downstream chunking.

    Applies NFKC unicode normalization, converts CRLF/CR to LF, strips
    control characters (keeping newlines/tabs), collapses runs of spaces and
    tabs, trims trailing whitespace per line, and limits blank runs to one
    empty line.

    Args:
        text: Raw extracted document text.

    Returns:
        Cleaned text, stripped of leading/trailing whitespace.
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CONTROL_CHARS.sub("", text)
    text = _SPACES.sub(" ", text)
    text = _TRAILING.sub("\n", text)
    text = _MANY_NEWLINES.sub("\n\n", text)
    return text.strip()
