"""Contracts for the processing pipeline."""

import uuid

from pydantic import BaseModel


class DocMetadata(BaseModel):
    """Metadata extracted from a document during processing."""

    title: str
    language: str
    char_count: int
    token_count: int


class ProcessDocumentMessage(BaseModel):
    """SQS message body asking processing to (re)process one document."""

    document_id: uuid.UUID
