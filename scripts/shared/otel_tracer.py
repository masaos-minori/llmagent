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
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    if not enabled:
        return _NoOpTracer()

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return _NoOpTracer()

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return provider.get_tracer(service_name)


def _import_sdk() -> Any | None:
    """Lazy-import the OpenTelemetry SDK; returns None on ImportError."""
    try:
        from opentelemetry.sdk.resources import Resource  # noqa: PLC0415
        from opentelemetry.sdk.trace import TracerProvider  # noqa: PLC0415
        from opentelemetry.sdk.trace.export import (  # noqa: PLC0415
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        return type(
            "SDK",
            (),
            {
                "Resource": Resource,
                "TracerProvider": TracerProvider,
                "ConsoleSpanExporter": ConsoleSpanExporter,
                "SimpleSpanProcessor": SimpleSpanProcessor,
            },
        )
    except ImportError:
        return None


def _attach_exporter(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if not otlp_endpoint:
        processor = _ConsoleProcessor()
        provider.add_span_processor(processor)
        logger.info(
            "OTel tracer configured: ConsoleSpanExporter service=%s", service_name
        )
        return

    otlp = _import_otlp()
    if otlp is None:
        provider.add_span_processor(_ConsoleProcessor())
        logger.warning(
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter"
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def _import_otlp() -> Any | None:
    """Lazy-import the OTLP exporter; returns None on ImportError."""
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # noqa: PLC0415
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # noqa: PLC0415

        return type(
            "OTLP",
            (),
            {
                "OTLPSpanExporter": OTLPSpanExporter,
                "BatchSpanProcessor": BatchSpanProcessor,
            },
        )
    except ImportError:
        return None


class _ConsoleProcessor:
    """Thin wrapper that delegates to SimpleSpanProcessor(ConsoleSpanExporter())."""

    def __init__(self) -> None:
        from opentelemetry.sdk.trace.export import (  # noqa: PLC0415
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        self._processor = SimpleSpanProcessor(ConsoleSpanExporter())

    def start_span(self, *args: Any, **kwargs: Any) -> Any:
        return self._processor.start_span(*args, **kwargs)

    def on_end(self, *args: Any, **kwargs: Any) -> None:
        self._processor.on_end(*args, **kwargs)

    def shutdown(self, *args: Any, **kwargs: Any) -> None:
        self._processor.shutdown(*args, **kwargs)

    def force_flush(self, *args: Any, **kwargs: Any) -> bool:
        result = self._processor.force_flush(*args, **kwargs)
        return bool(result)


class _NoOpTracer:
    """Minimal tracer stub for otel_enabled=False."""

    def start_as_current_span(self, name: str, **kwargs: Any) -> _NoOpSpan:
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
        pass
