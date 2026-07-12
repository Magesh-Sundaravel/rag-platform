"""HTTP routes for document ingestion."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ingestion import parsing, repository
from ingestion.db import get_session
from rag_contracts.documents import DocumentListOut, DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile, session: SessionDep) -> DocumentOut:
    """Ingest an uploaded file: parse, dedup, version, and enqueue processing."""
    filename = file.filename or "upload"
    data = await file.read()
    raw_text = parsing.extract_text(filename, data)
    document = await repository.create_document(
        session,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        data=data,
        raw_text=raw_text,
    )
    return DocumentOut.model_validate(document)


@router.get("/{document_id}")
async def get_document(document_id: uuid.UUID, session: SessionDep) -> DocumentOut:
    """Return one document by id."""
    return DocumentOut.model_validate(await repository.get_document(session, document_id))


@router.get("")
async def list_documents(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> DocumentListOut:
    """Return one page of documents, newest first."""
    items, total = await repository.list_documents(session, offset=offset, limit=limit)
    return DocumentListOut(
        items=[DocumentOut.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: uuid.UUID, session: SessionDep) -> Response:
    """Delete a document and its queued jobs."""
    await repository.delete_document(session, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
