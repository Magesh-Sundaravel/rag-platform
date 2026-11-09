"""API tests for the ingestion document endpoints (SQLite-backed)."""

import json
import uuid

import pytest
from botocore.exceptions import EndpointConnectionError
from httpx import AsyncClient
from ingestion_test_helpers import FakeSqsClient, make_pdf, upload_payload
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rag_db.models import Document


async def test_upload_txt_returns_201(client: AsyncClient) -> None:
    resp = await client.post("/documents", files=upload_payload("a.txt", b"hello"))
    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "a.txt"
    assert body["version"] == 1
    assert body["status"] == "pending"
    assert len(body["content_hash"]) == 64


async def test_exact_duplicate_of_processed_document_conflicts(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await client.post("/documents", files=upload_payload("a.txt", b"same"))
    async with session_factory() as session:
        await session.execute(update(Document).values(status="processed"))
        await session.commit()
    resp = await client.post("/documents", files=upload_payload("other-name.txt", b"same"))
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


async def test_reupload_of_pending_document_resends_message(
    client: AsyncClient, sqs: FakeSqsClient
) -> None:
    first = await client.post("/documents", files=upload_payload("a.txt", b"stuck"))
    again = await client.post("/documents", files=upload_payload("a.txt", b"stuck"))
    assert again.status_code == 201
    assert again.json()["id"] == first.json()["id"]
    assert [json.loads(m["MessageBody"])["document_id"] for m in sqs.sent] == [
        first.json()["id"]
    ] * 2


async def test_failed_resend_keeps_existing_pending_document(
    client: AsyncClient, sqs: FakeSqsClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    first = await client.post("/documents", files=upload_payload("a.txt", b"keep me"))
    sqs.error = EndpointConnectionError(endpoint_url="http://sqs")
    resp = await client.post("/documents", files=upload_payload("a.txt", b"keep me"))
    assert resp.status_code == 503
    async with session_factory() as session:
        docs = (await session.scalars(select(Document))).all()
    assert [str(d.id) for d in docs] == [first.json()["id"]]


async def test_changed_content_same_filename_increments_version(client: AsyncClient) -> None:
    r1 = await client.post("/documents", files=upload_payload("a.txt", b"v1"))
    r2 = await client.post("/documents", files=upload_payload("a.txt", b"v2"))
    assert r1.json()["version"] == 1
    assert r2.json()["version"] == 2


async def test_upload_sends_processing_message(client: AsyncClient, sqs: FakeSqsClient) -> None:
    resp = await client.post("/documents", files=upload_payload("a.txt", b"queue me"))
    assert resp.status_code == 201
    assert len(sqs.sent) == 1
    assert sqs.sent[0]["QueueUrl"] == "test-queue"
    assert json.loads(sqs.sent[0]["MessageBody"]) == {"document_id": resp.json()["id"]}


async def test_enqueue_failure_rolls_back_upload_with_503(
    client: AsyncClient, sqs: FakeSqsClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    sqs.error = EndpointConnectionError(endpoint_url="http://sqs")
    resp = await client.post("/documents", files=upload_payload("a.txt", b"lost"))
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "service_unavailable"
    async with session_factory() as session:
        assert (await session.scalars(select(Document))).all() == []

    # The client's retry succeeds once SQS is back (no duplicate-content 409).
    sqs.error = None
    retry = await client.post("/documents", files=upload_payload("a.txt", b"lost"))
    assert retry.status_code == 201


async def test_non_boto_enqueue_error_still_rolls_back_upload(
    client: AsyncClient, sqs: FakeSqsClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    sqs.error = RuntimeError("cannot schedule new futures after shutdown")
    with pytest.raises(RuntimeError):
        await client.post("/documents", files=upload_payload("a.txt", b"orphan?"))
    async with session_factory() as session:
        assert (await session.scalars(select(Document))).all() == []

    sqs.error = None
    retry = await client.post("/documents", files=upload_payload("a.txt", b"orphan?"))
    assert retry.status_code == 201


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
