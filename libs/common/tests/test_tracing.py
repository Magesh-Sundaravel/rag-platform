"""Tests for OpenTelemetry tracing setup (ADR-0008: gated on exporter config)."""

from unittest.mock import patch

from rag_common.config import BaseServiceSettings
from rag_common.tracing import configure_tracing


def test_no_op_without_endpoint() -> None:
    settings = BaseServiceSettings(service_name="test-service")
    with patch("rag_common.tracing.trace.set_tracer_provider") as set_provider:
        configure_tracing(settings)
    set_provider.assert_not_called()


def test_installs_provider_and_httpx_instrumentation_with_endpoint() -> None:
    settings = BaseServiceSettings(
        service_name="test-service", otel_exporter_endpoint="http://collector:4318/v1/traces"
    )
    with (
        patch("rag_common.tracing.trace.set_tracer_provider") as set_provider,
        patch("rag_common.tracing.OTLPSpanExporter") as exporter_cls,
        patch("rag_common.tracing.HTTPXClientInstrumentor") as instrumentor_cls,
    ):
        configure_tracing(settings)

    exporter_cls.assert_called_once_with(endpoint="http://collector:4318/v1/traces")
    set_provider.assert_called_once()
    instrumentor_cls.return_value.instrument.assert_called_once()
