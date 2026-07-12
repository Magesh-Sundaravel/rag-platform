"""API tests for the /documents endpoints (httpx over ASGI, SQLite backend)."""

from collections.abc import Callable

import httpx


def _upload(
    name: str, data: bytes, content_type: str = "text/plain"
) -> dict[str, tuple[str, bytes, str]]:
    return {"file": (name, data, content_type)}


async def test_upload_txt_returns_201_with_document(client: httpx.AsyncClient) -> None:
    resp = await client.post("/documents", files=_upload("notes.txt", b"hello"))
    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "notes.txt"
    assert body["version"] == 1
    assert body["status"] == "pending"
    assert len(body["content_hash"]) == 64


async def test_upload_pdf(client: httpx.AsyncClient, pdf_factory: Callable[[str], bytes]) -> None:
    resp = await client.post(
        "/documents", files=_upload("doc.pdf", pdf_factory("Hello PDF"), "application/pdf")
    )
    assert resp.status_code == 201
    assert resp.json()["content_type"] == "application/pdf"


async def test_duplicate_upload_conflicts(client: httpx.AsyncClient) -> None:
    await client.post("/documents", files=_upload("a.txt", b"same"))
    resp = await client.post("/documents", files=_upload("a.txt", b"same"))
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


async def test_changed_content_bumps_version(client: httpx.AsyncClient) -> None:
    await client.post("/documents", files=_upload("a.txt", b"v1"))
    resp = await client.post("/documents", files=_upload("a.txt", b"v2"))
    assert resp.status_code == 201
    assert resp.json()["version"] == 2


async def test_unsupported_type_is_422(client: httpx.AsyncClient) -> None:
    resp = await client.post("/documents", files=_upload("x.docx", b"data"))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_input"


async def test_get_and_delete_lifecycle(client: httpx.AsyncClient) -> None:
    created = (await client.post("/documents", files=_upload("a.txt", b"hello"))).json()
    doc_id = created["id"]

    got = await client.get(f"/documents/{doc_id}")
    assert got.status_code == 200
    assert got.json()["id"] == doc_id

    deleted = await client.delete(f"/documents/{doc_id}")
    assert deleted.status_code == 204

    missing = await client.get(f"/documents/{doc_id}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


async def test_list_pagination(client: httpx.AsyncClient) -> None:
    for i in range(3):
        await client.post("/documents", files=_upload(f"f{i}.txt", f"content {i}".encode()))
    resp = await client.get("/documents", params={"offset": 1, "limit": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 1
    assert body["offset"] == 1
    assert body["limit"] == 1
