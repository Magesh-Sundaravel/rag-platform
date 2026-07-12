"""API contracts for the document ingestion service."""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class DocumentStatus(StrEnum):
    """Lifecycle status of an ingested document."""

    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentOut(BaseModel):
    """A document as returned by the ingestion API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str
    content_hash: str
    version: int
    status: DocumentStatus
    created_at: datetime


class DocumentListOut(BaseModel):
    """A paginated page of documents."""

    items: list[DocumentOut]
    total: int
    offset: int
    limit: int
