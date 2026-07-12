"""API tests for the ingestion document endpoints (SQLite-backed)."""

import uuid

from httpx import AsyncClient
from ingestion_test_helpers import make_pdf, upload_payload
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rag_db.models import Job


async def test_upload_txt_returns_201(client: AsyncClient) -> None:
    resp = await client.post("/documents", files=upload_payload("a.txt", b"hello"))
    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "a.txt"
    assert body["version"] == 1
    assert body["status"] == "pending"
    assert len(body["content_hash"]) == 64


async def test_exact_duplicate_conflicts(client: AsyncClient) -> None:
    await client.post("/documents", files=upload_payload("a.txt", b"same"))
    resp = await client.post("/documents", files=upload_payload("other-name.txt", b"same"))
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


async def test_changed_content_same_filename_increments_version(client: AsyncClient) -> None:
    r1 = await client.post("/documents", files=upload_payload("a.txt", b"v1"))
    r2 = await client.post("/documents", files=upload_payload("a.txt", b"v2"))
    assert r1.json()["version"] == 1
    assert r2.json()["version"] == 2


async def test_upload_writes_pending_job(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    resp = await client.post("/documents", files=upload_payload("a.txt", b"job me"))
    doc_id = uuid.UUID(resp.json()["id"])
    async with session_factory() as session:
        job = (await session.scalars(select(Job).where(Job.document_id == doc_id))).one()
    assert job.status == "pending"
    assert job.job_type == "process_document"
    assert job.attempts == 0


async def test_get_document(client: AsyncClient) -> None:
    doc_id = (await client.post("/documents", files=upload_payload("a.txt", b"get me"))).json()[
        "id"
    ]
    resp = await client.get(f"/documents/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == doc_id


async def test_get_missing_document_404(client: AsyncClient) -> None:
    resp = await client.get(f"/documents/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_list_pagination(client: AsyncClient) -> None:
    for i in range(3):
        await client.post("/documents", files=upload_payload(f"f{i}.txt", f"content {i}".encode()))
    resp = await client.get("/documents", params={"offset": 1, "limit": 2})
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["offset"] == 1
    assert body["limit"] == 2


async def test_delete_document(client: AsyncClient) -> None:
    doc_id = (await client.post("/documents", files=upload_payload("a.txt", b"bye"))).json()["id"]
    assert (await client.delete(f"/documents/{doc_id}")).status_code == 204
    assert (await client.get(f"/documents/{doc_id}")).status_code == 404
    assert (await client.delete(f"/documents/{doc_id}")).status_code == 404


async def test_unsupported_file_422(client: AsyncClient) -> None:
    resp = await client.post("/documents", files=upload_payload("x.png", b"\x89PNG", "image/png"))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_input"


async def test_upload_pdf(client: AsyncClient) -> None:
    resp = await client.post(
        "/documents", files=upload_payload("doc.pdf", make_pdf("From PDF"), "application/pdf")
    )
    assert resp.status_code == 201
