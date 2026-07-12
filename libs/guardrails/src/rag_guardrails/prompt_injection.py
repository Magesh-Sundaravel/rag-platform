"""Heuristic detection of common prompt-injection phrasing."""

import re

_INJECTION_PATTERNS = [
    re.compile(r"ignore (all |the )?(previous|prior|above) instructions", re.IGNORECASE),
    re.compile(r"disregard (the |all )?(above|prior|previous)", re.IGNORECASE),
    re.compile(r"reveal (your |the )?(system )?prompt", re.IGNORECASE),
    re.compile(r"you are now", re.IGNORECASE),
    re.compile(r"act as (if )?you (have no|are not) restrictions", re.IGNORECASE),
]


def detect_prompt_injection(text: str) -> bool:
    """Check whether ``text`` contains a known prompt-injection phrase.

    Args:
        text: The user-supplied text to check (e.g. a question).

    Returns:
        ``True`` if any known injection pattern matches.
    """
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)
