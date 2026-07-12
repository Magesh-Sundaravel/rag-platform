"""Unit tests for text normalization."""

from processing.normalize import normalize_text


def test_crlf_to_lf() -> None:
    assert normalize_text("a\r\nb\rc") == "a\nb\nc"


def test_control_chars_stripped() -> None:
    assert normalize_text("a\x00b\x07c") == "abc"


def test_spaces_collapsed() -> None:
    assert normalize_text("a   b\t\tc") == "a b c"


def test_blank_runs_limited() -> None:
    assert normalize_text("a\n\n\n\n\nb") == "a\n\nb"


def test_trailing_whitespace_trimmed() -> None:
    assert normalize_text("a   \nb") == "a\nb"


def test_unicode_nfkc() -> None:
    assert normalize_text("\ufb01ne caf\u00e9") == "fine caf\u00e9"


def test_strip_outer() -> None:
    assert normalize_text("\n\n  hello  \n\n") == "hello"
