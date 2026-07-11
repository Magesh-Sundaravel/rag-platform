"""Tests for rag_common.config.BaseServiceSettings."""

import pytest

from rag_common.config import BaseServiceSettings


def test_defaults() -> None:
    settings = BaseServiceSettings()
    assert settings.service_name == "service"
    assert settings.environment == "dev"
    assert settings.log_level == "INFO"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_SERVICE_NAME", "ingestion")
    monkeypatch.setenv("RAG_PORT", "8001")
    monkeypatch.setenv("RAG_ENVIRONMENT", "prod")
    settings = BaseServiceSettings()
    assert settings.service_name == "ingestion"
    assert settings.port == 8001
    assert settings.environment == "prod"


def test_is_dev_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    assert BaseServiceSettings().is_dev is True
    monkeypatch.setenv("RAG_ENVIRONMENT", "prod")
    assert BaseServiceSettings().is_dev is False
