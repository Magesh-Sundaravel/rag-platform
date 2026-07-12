"""Heuristic PII redaction: email, phone, credit-card, and SSN patterns."""

import re

# Applied in this order so more specific patterns (SSN, credit card) claim
# their digits before the looser phone pattern gets a chance at them.
_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
    "phone": re.compile(r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b"),
}


def redact_pii(text: str) -> str:
    """Replace PII patterns in ``text`` with ``[REDACTED_<KIND>]`` markers.

    Args:
        text: The text to scan and redact.

    Returns:
        ``text`` with every match of every pattern replaced, applied in a
        fixed order (email, SSN, credit card, phone).
    """
    for kind, pattern in _PII_PATTERNS.items():
        text = pattern.sub(f"[REDACTED_{kind.upper()}]", text)
    return text
