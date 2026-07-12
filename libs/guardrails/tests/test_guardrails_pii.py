"""Tests for regex-based PII redaction."""

from rag_guardrails.pii import redact_pii


def test_redacts_email() -> None:
    result = redact_pii("Contact me at jane.doe@example.com for details.")
    assert "jane.doe@example.com" not in result
    assert "[REDACTED_EMAIL]" in result


def test_redacts_ssn() -> None:
    result = redact_pii("My SSN is 123-45-6789.")
    assert "123-45-6789" not in result
    assert "[REDACTED_SSN]" in result


def test_redacts_credit_card() -> None:
    result = redact_pii("Card number: 4111 1111 1111 1111")
    assert "4111 1111 1111 1111" not in result
    assert "[REDACTED_CREDIT_CARD]" in result


def test_redacts_phone() -> None:
    result = redact_pii("Call me at (415) 555-0132.")
    assert "555-0132" not in result
    assert "[REDACTED_PHONE]" in result


def test_leaves_non_pii_text_untouched() -> None:
    text = "Paris is the capital of France."
    assert redact_pii(text) == text


def test_redacts_multiple_occurrences() -> None:
    result = redact_pii("Emails: a@example.com and b@example.com")
    assert result.count("[REDACTED_EMAIL]") == 2
