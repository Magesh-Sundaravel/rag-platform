"""Unit tests for metadata extraction heuristics."""

from processing.metadata import detect_language, estimate_tokens, extract_metadata, extract_title

ENGLISH = "The quick brown fox jumps over the lazy dog and it was not the end of the story."
NON_ENGLISH = "zxq vbnm qwrt plok mnbv cxza qazw sxed crfv tgbn yhnm ujmi kolp"


def test_title_from_markdown_heading() -> None:
    assert extract_title("f.md", "intro\n## My Heading\nbody") == "My Heading"


def test_title_from_first_line() -> None:
    assert extract_title("f.txt", "\n\nFirst line here\nmore") == "First line here"


def test_title_falls_back_to_filename() -> None:
    assert extract_title("f.txt", "") == "f.txt"


def test_title_truncated_to_120_chars() -> None:
    assert len(extract_title("f.txt", "x" * 500)) == 120


def test_detect_language_english() -> None:
    assert detect_language(ENGLISH) == "en"


def test_detect_language_unknown() -> None:
    assert detect_language(NON_ENGLISH) == "unknown"
    assert detect_language("12345 67890") == "unknown"


def test_estimate_tokens() -> None:
    assert estimate_tokens("") == 0
    assert estimate_tokens("ab") == 1
    assert estimate_tokens("x" * 400) == 100


def test_extract_metadata_bundle() -> None:
    meta = extract_metadata("doc.md", f"# Title\n{ENGLISH}")
    assert meta.title == "Title"
    assert meta.language == "en"
    assert meta.char_count > 0
    assert meta.token_count > 0
