"""Tests for rag_common.app_factory.create_app."""

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from rag_common.app_factory import create_app
from rag_common.config import BaseServiceSettings
from rag_common.exceptions import NotFoundError


@pytest.fixture()
def app() -> FastAPI:
    settings = BaseServiceSettings(service_name="testsvc")
    return create_app(settings, title="Test Service", version="1.2.3")


@pytest.fixture()
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_health(client: httpx.AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "testsvc"}


async def test_ready(client: httpx.AsyncClient) -> None:
    resp = await client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


async def test_platform_error_rendered_as_json(app: FastAPI) -> None:
    @app.get("/boom")
    async def boom() -> None:
        raise NotFoundError("document 42 not found")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/boom")
    assert resp.status_code == 404
    assert resp.json() == {"error": {"code": "not_found", "detail": "document 42 not found"}}


def test_app_metadata(app: FastAPI) -> None:
    assert app.title == "Test Service"
    assert app.version == "1.2.3"
