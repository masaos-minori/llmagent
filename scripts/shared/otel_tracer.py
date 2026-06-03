#!/usr/bin/env python3
"""otel_tracer.py
OpenTelemetry tracer initialisation for the agent pipeline.

Design (R10):
  build_tracer() creates a private TracerProvider instance and does NOT call
  trace.set_tracer_provider().  This prevents cross-test provider pollution and
  allows multiple independent tracer instances to coexist in the same process.

When enabled=False, a NoOp-compatible tracer is returned without importing the
OpenTelemetry SDK, so the dependency remains optional for environments that do
not install opentelemetry-sdk.

When enabled=True and otlp_endpoint is non-empty, an OTLP HTTP exporter is
configured.  Otherwise, ConsoleSpanExporter is used (useful for development /
testing with otel_enabled=true and empty otel_endpoint).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def build_tracer(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> Any:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider; OTLP exporter when otlp_endpoint is set, ConsoleSpanExporter otherwise."""
    if not enabled:
        return _NoOpTracer()

    try:
        # Lazy imports: opentelemetry-sdk is optional; loaded only when enabled=True.
        from opentelemetry.sdk.resources import Resource  # noqa: PLC0415 isort:skip
        from opentelemetry.sdk.trace import TracerProvider  # noqa: PLC0415 isort:skip
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter  # noqa: PLC0415 isort:skip
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: PLC0415 isort:skip
    except ImportError as e:
        logger.warning(
            "opentelemetry-sdk not installed; falling back to NoOp tracer: %s", e
        )
        return _NoOpTracer()

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        try:
            # Lazy imports: opentelemetry-exporter-otlp is optional.
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )  # noqa: PLC0415 isort:skip
            from opentelemetry.sdk.trace.export import BatchSpanProcessor  # noqa: PLC0415 isort:skip

            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(
                "OTel tracer configured: OTLP endpoint=%s service=%s",
                otlp_endpoint,
                service_name,
            )
        except ImportError as e:
            logger.warning(
                "opentelemetry-exporter-otlp not installed;"
                " falling back to ConsoleSpanExporter: %s",
                e,
            )
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    else:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        logger.info(
            "OTel tracer configured: ConsoleSpanExporter service=%s", service_name
        )

    # Return a tracer bound to the private provider (not the global one)
    return provider.get_tracer(service_name)


class _NoOpTracer:
    """Minimal tracer stub for otel_enabled=False; implements start_as_current_span() as a no-op so callers need not check enabled status."""

    def start_as_current_span(self, name: str, **kwargs: Any) -> _NoOpSpan:
        """Return a no-op span context manager."""
        return _NoOpSpan()

    def __repr__(self) -> str:
        return "_NoOpTracer()"


class _NoOpSpan:
    """No-op span that supports context manager protocol and set_attribute()."""

    def __enter__(self) -> _NoOpSpan:
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def set_attribute(self, _key: str, _value: Any) -> None:
        """Accept attribute calls without recording anything."""
