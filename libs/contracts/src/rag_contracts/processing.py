"""Contracts for the processing pipeline."""

from pydantic import BaseModel


class DocMetadata(BaseModel):
    """Metadata extracted from a document during processing."""

    title: str
    language: str
    char_count: int
    token_count: int
