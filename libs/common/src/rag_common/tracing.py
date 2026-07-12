"""OpenTelemetry tracing setup, gated on an exporter endpoint (ADR-0008).

Every service always instruments its FastAPI app (cheap, no-op without a
real exporter). Actually exporting spans, and propagating trace context
over outbound ``httpx`` calls, only happens when
``RAG_OTEL_EXPORTER_ENDPOINT`` is set — the local/CI default is OpenTelemetry's
built-in no-op ``TracerProvider``: no thread, no network, no test noise.
"""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from rag_common.config import BaseServiceSettings


def configure_tracing(settings: BaseServiceSettings) -> None:
    """Install a real tracer provider and httpx instrumentation, if configured.

    Args:
        settings: The service settings; ``otel_exporter_endpoint`` gates
            whether tracing does anything at all.
    """
    if not settings.otel_exporter_endpoint:
        return
    resource = Resource.create({"service.name": settings.service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    HTTPXClientInstrumentor().instrument()
