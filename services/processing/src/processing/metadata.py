"""Metadata extraction heuristics (title, language, size counts)."""

import re

from rag_contracts.processing import DocMetadata

_MD_HEADING = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)

# Most frequent English function words; a cheap language signal that avoids a
# model dependency. Documented approximation (spec §Scope 3).
_EN_STOPWORDS = frozenset(
    {
        "the",
        "of",
        "and",
        "to",
        "in",
        "a",
        "is",
        "that",
        "it",
        "for",
        "on",
        "was",
        "as",
        "with",
        "be",
        "by",
        "are",
        "this",
        "have",
        "from",
        "or",
        "an",
        "they",
        "which",
        "you",
        "not",
        "at",
        "his",
        "her",
        "had",
        "we",
        "all",
        "can",
        "has",
        "but",
        "will",
    }
)

CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Estimate token count using the ~4 chars/token approximation.

    Args:
        text: Input text.

    Returns:
        Estimated token count (minimum 1 for non-empty text).
    """
    if not text:
        return 0
    return max(1, len(text) // CHARS_PER_TOKEN)


def detect_language(text: str) -> str:
    """Detect language via English stopword ratio (``en`` or ``unknown``).

    Args:
        text: Input text; only the first 200 words are inspected.

    Returns:
        ``"en"`` when at least 15% of inspected words are common English
        stopwords, otherwise ``"unknown"``.
    """
    words = re.findall(r"[a-zA-Z']+", text.lower())[:200]
    if not words:
        return "unknown"
    ratio = sum(1 for w in words if w in _EN_STOPWORDS) / len(words)
    return "en" if ratio >= 0.15 else "unknown"


def extract_title(filename: str, text: str) -> str:
    """Extract a document title heuristically.

    Prefers the first markdown heading, then the first non-empty line
    (truncated to 120 chars), then the filename.

    Args:
        filename: Original filename fallback.
        text: Normalized document text.

    Returns:
        The extracted title.
    """
    heading = _MD_HEADING.search(text)
    if heading:
        return heading.group(1).strip()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:120]
    return filename


def extract_metadata(filename: str, text: str) -> DocMetadata:
    """Extract full document metadata.

    Args:
        filename: Original filename.
        text: Normalized document text.

    Returns:
        A :class:`DocMetadata` with title, language, and size counts.
    """
    return DocMetadata(
        title=extract_title(filename, text),
        language=detect_language(text),
        char_count=len(text),
        token_count=estimate_tokens(text),
    )
