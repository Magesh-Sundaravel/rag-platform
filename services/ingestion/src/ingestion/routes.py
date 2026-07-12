"""HTTP routes for the ingestion service."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ingestion import repository
from ingestion.db import get_session
from ingestion.parsing import extract_text
from rag_contracts.documents import DocumentListOut, DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile, session: SessionDep) -> DocumentOut:
    """Upload a document (txt/md/pdf); dedups by content hash and versions by filename."""
    data = await file.read()
    filename = file.filename or "upload"
    text = extract_text(filename, data)
    document = await repository.create_document(
        session,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        raw_bytes=data,
        raw_text=text,
    )
    return DocumentOut.model_validate(document)


@router.get("/{document_id}")
async def get_document(document_id: uuid.UUID, session: SessionDep) -> DocumentOut:
    """Fetch a single document by id."""
    return DocumentOut.model_validate(await repository.get_document(session, document_id))


@router.get("")
async def list_documents(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> DocumentListOut:
    """List documents, newest first, with offset/limit pagination."""
    items, total = await repository.list_documents(session, offset=offset, limit=limit)
    return DocumentListOut(
        items=[DocumentOut.model_validate(d) for d in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: uuid.UUID, session: SessionDep) -> None:
    """Delete a document and its jobs."""
    await repository.delete_document(session, document_id)
