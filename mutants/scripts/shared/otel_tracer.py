#!/usr/bin/env python3
"""scripts/shared/otel_tracer.py

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
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, Protocol, cast

from shared.otel_noop import NoOpTracer

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


class SpanProtocol(Protocol):
    """Minimal protocol for OTel-compatible spans used by the agent pipeline."""

    def __enter__(self) -> SpanProtocol:
        """Enter the span context manager."""
        ...

    def __exit__(self, *args: object) -> None:
        """Exit the span context manager."""
        ...

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the span."""
        ...


class TracerProtocol(Protocol):
    """Minimal protocol for OTel-compatible tracers used by the agent pipeline."""

    def start_as_current_span(self, name: str, **kwargs: Any) -> SpanProtocol:
        """Start a new span with the given name."""
        ...
mutants_x_build_tracer__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_build_tracer__mutmut)
def build_tracer(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_orig(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_1(
    enabled: bool,
    service_name: str = "XXllm-agentXX",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_2(
    enabled: bool,
    service_name: str = "LLM-AGENT",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_3(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "XXXX",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_4(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = None
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_5(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_6(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = None
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_7(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is not None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_8(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning(None)
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_9(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("XXopentelemetry-sdk not installed; falling back to NoOp tracerXX")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_10(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to noop tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_11(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("OPENTELEMETRY-SDK NOT INSTALLED; FALLING BACK TO NOOP TRACER")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_12(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = None
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_13(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create(None)
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_14(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"XXservice.nameXX": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_15(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"SERVICE.NAME": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_16(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = None
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_17(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=None)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_18(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(None, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_19(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, None, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_20(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, None)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_21(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_22(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, service_name)
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_23(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, )
    return cast(TracerProtocol, provider.get_tracer(service_name))


def x_build_tracer__mutmut_24(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(None, provider.get_tracer(service_name))


def x_build_tracer__mutmut_25(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, None)


def x_build_tracer__mutmut_26(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(provider.get_tracer(service_name))


def x_build_tracer__mutmut_27(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, )


def x_build_tracer__mutmut_28(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol:
    """Build and return a private OTel Tracer (or NoOp) without modifying the global provider."""
    noop: TracerProtocol = NoOpTracer()
    if not enabled:
        return noop

    sdk = _import_sdk()
    if sdk is None:
        logger.warning("opentelemetry-sdk not installed; falling back to NoOp tracer")
        return noop

    resource = sdk.Resource.create({"service.name": service_name})
    provider = sdk.TracerProvider(resource=resource)
    _attach_exporter(provider, otlp_endpoint, service_name)
    return cast(TracerProtocol, provider.get_tracer(None))

mutants_x_build_tracer__mutmut['_mutmut_orig'] = x_build_tracer__mutmut_orig # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_1'] = x_build_tracer__mutmut_1 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_2'] = x_build_tracer__mutmut_2 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_3'] = x_build_tracer__mutmut_3 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_4'] = x_build_tracer__mutmut_4 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_5'] = x_build_tracer__mutmut_5 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_6'] = x_build_tracer__mutmut_6 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_7'] = x_build_tracer__mutmut_7 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_8'] = x_build_tracer__mutmut_8 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_9'] = x_build_tracer__mutmut_9 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_10'] = x_build_tracer__mutmut_10 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_11'] = x_build_tracer__mutmut_11 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_12'] = x_build_tracer__mutmut_12 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_13'] = x_build_tracer__mutmut_13 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_14'] = x_build_tracer__mutmut_14 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_15'] = x_build_tracer__mutmut_15 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_16'] = x_build_tracer__mutmut_16 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_17'] = x_build_tracer__mutmut_17 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_18'] = x_build_tracer__mutmut_18 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_19'] = x_build_tracer__mutmut_19 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_20'] = x_build_tracer__mutmut_20 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_21'] = x_build_tracer__mutmut_21 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_22'] = x_build_tracer__mutmut_22 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_23'] = x_build_tracer__mutmut_23 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_24'] = x_build_tracer__mutmut_24 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_25'] = x_build_tracer__mutmut_25 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_26'] = x_build_tracer__mutmut_26 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_27'] = x_build_tracer__mutmut_27 # type: ignore # mutmut generated
mutants_x_build_tracer__mutmut['x_build_tracer__mutmut_28'] = x_build_tracer__mutmut_28 # type: ignore # mutmut generated
mutants_x__import_sdk__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__import_sdk__mutmut)
def _import_sdk() -> Any | None:
    """Lazy-import the OpenTelemetry SDK; returns None on ImportError."""
    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        return SimpleNamespace(
            Resource=Resource,
            TracerProvider=TracerProvider,
            ConsoleSpanExporter=ConsoleSpanExporter,
            SimpleSpanProcessor=SimpleSpanProcessor,
        )
    except ImportError:
        return None


def x__import_sdk__mutmut_orig() -> Any | None:
    """Lazy-import the OpenTelemetry SDK; returns None on ImportError."""
    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        return SimpleNamespace(
            Resource=Resource,
            TracerProvider=TracerProvider,
            ConsoleSpanExporter=ConsoleSpanExporter,
            SimpleSpanProcessor=SimpleSpanProcessor,
        )
    except ImportError:
        return None


def x__import_sdk__mutmut_1() -> Any | None:
    """Lazy-import the OpenTelemetry SDK; returns None on ImportError."""
    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        return SimpleNamespace(
            Resource=None,
            TracerProvider=TracerProvider,
            ConsoleSpanExporter=ConsoleSpanExporter,
            SimpleSpanProcessor=SimpleSpanProcessor,
        )
    except ImportError:
        return None


def x__import_sdk__mutmut_2() -> Any | None:
    """Lazy-import the OpenTelemetry SDK; returns None on ImportError."""
    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        return SimpleNamespace(
            Resource=Resource,
            TracerProvider=None,
            ConsoleSpanExporter=ConsoleSpanExporter,
            SimpleSpanProcessor=SimpleSpanProcessor,
        )
    except ImportError:
        return None


def x__import_sdk__mutmut_3() -> Any | None:
    """Lazy-import the OpenTelemetry SDK; returns None on ImportError."""
    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        return SimpleNamespace(
            Resource=Resource,
            TracerProvider=TracerProvider,
            ConsoleSpanExporter=None,
            SimpleSpanProcessor=SimpleSpanProcessor,
        )
    except ImportError:
        return None


def x__import_sdk__mutmut_4() -> Any | None:
    """Lazy-import the OpenTelemetry SDK; returns None on ImportError."""
    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        return SimpleNamespace(
            Resource=Resource,
            TracerProvider=TracerProvider,
            ConsoleSpanExporter=ConsoleSpanExporter,
            SimpleSpanProcessor=None,
        )
    except ImportError:
        return None


def x__import_sdk__mutmut_5() -> Any | None:
    """Lazy-import the OpenTelemetry SDK; returns None on ImportError."""
    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        return SimpleNamespace(
            TracerProvider=TracerProvider,
            ConsoleSpanExporter=ConsoleSpanExporter,
            SimpleSpanProcessor=SimpleSpanProcessor,
        )
    except ImportError:
        return None


def x__import_sdk__mutmut_6() -> Any | None:
    """Lazy-import the OpenTelemetry SDK; returns None on ImportError."""
    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        return SimpleNamespace(
            Resource=Resource,
            ConsoleSpanExporter=ConsoleSpanExporter,
            SimpleSpanProcessor=SimpleSpanProcessor,
        )
    except ImportError:
        return None


def x__import_sdk__mutmut_7() -> Any | None:
    """Lazy-import the OpenTelemetry SDK; returns None on ImportError."""
    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        return SimpleNamespace(
            Resource=Resource,
            TracerProvider=TracerProvider,
            SimpleSpanProcessor=SimpleSpanProcessor,
        )
    except ImportError:
        return None


def x__import_sdk__mutmut_8() -> Any | None:
    """Lazy-import the OpenTelemetry SDK; returns None on ImportError."""
    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        return SimpleNamespace(
            Resource=Resource,
            TracerProvider=TracerProvider,
            ConsoleSpanExporter=ConsoleSpanExporter,
            )
    except ImportError:
        return None

mutants_x__import_sdk__mutmut['_mutmut_orig'] = x__import_sdk__mutmut_orig # type: ignore # mutmut generated
mutants_x__import_sdk__mutmut['x__import_sdk__mutmut_1'] = x__import_sdk__mutmut_1 # type: ignore # mutmut generated
mutants_x__import_sdk__mutmut['x__import_sdk__mutmut_2'] = x__import_sdk__mutmut_2 # type: ignore # mutmut generated
mutants_x__import_sdk__mutmut['x__import_sdk__mutmut_3'] = x__import_sdk__mutmut_3 # type: ignore # mutmut generated
mutants_x__import_sdk__mutmut['x__import_sdk__mutmut_4'] = x__import_sdk__mutmut_4 # type: ignore # mutmut generated
mutants_x__import_sdk__mutmut['x__import_sdk__mutmut_5'] = x__import_sdk__mutmut_5 # type: ignore # mutmut generated
mutants_x__import_sdk__mutmut['x__import_sdk__mutmut_6'] = x__import_sdk__mutmut_6 # type: ignore # mutmut generated
mutants_x__import_sdk__mutmut['x__import_sdk__mutmut_7'] = x__import_sdk__mutmut_7 # type: ignore # mutmut generated
mutants_x__import_sdk__mutmut['x__import_sdk__mutmut_8'] = x__import_sdk__mutmut_8 # type: ignore # mutmut generated
mutants_x__attach_exporter__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__attach_exporter__mutmut)
def _attach_exporter(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if not otlp_endpoint:
        _attach_console_exporter(provider, service_name)
        return
    _attach_otlp_exporter(provider, otlp_endpoint, service_name)


def x__attach_exporter__mutmut_orig(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if not otlp_endpoint:
        _attach_console_exporter(provider, service_name)
        return
    _attach_otlp_exporter(provider, otlp_endpoint, service_name)


def x__attach_exporter__mutmut_1(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if otlp_endpoint:
        _attach_console_exporter(provider, service_name)
        return
    _attach_otlp_exporter(provider, otlp_endpoint, service_name)


def x__attach_exporter__mutmut_2(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if not otlp_endpoint:
        _attach_console_exporter(None, service_name)
        return
    _attach_otlp_exporter(provider, otlp_endpoint, service_name)


def x__attach_exporter__mutmut_3(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if not otlp_endpoint:
        _attach_console_exporter(provider, None)
        return
    _attach_otlp_exporter(provider, otlp_endpoint, service_name)


def x__attach_exporter__mutmut_4(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if not otlp_endpoint:
        _attach_console_exporter(service_name)
        return
    _attach_otlp_exporter(provider, otlp_endpoint, service_name)


def x__attach_exporter__mutmut_5(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if not otlp_endpoint:
        _attach_console_exporter(provider, )
        return
    _attach_otlp_exporter(provider, otlp_endpoint, service_name)


def x__attach_exporter__mutmut_6(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if not otlp_endpoint:
        _attach_console_exporter(provider, service_name)
        return
    _attach_otlp_exporter(None, otlp_endpoint, service_name)


def x__attach_exporter__mutmut_7(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if not otlp_endpoint:
        _attach_console_exporter(provider, service_name)
        return
    _attach_otlp_exporter(provider, None, service_name)


def x__attach_exporter__mutmut_8(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if not otlp_endpoint:
        _attach_console_exporter(provider, service_name)
        return
    _attach_otlp_exporter(provider, otlp_endpoint, None)


def x__attach_exporter__mutmut_9(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if not otlp_endpoint:
        _attach_console_exporter(provider, service_name)
        return
    _attach_otlp_exporter(otlp_endpoint, service_name)


def x__attach_exporter__mutmut_10(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if not otlp_endpoint:
        _attach_console_exporter(provider, service_name)
        return
    _attach_otlp_exporter(provider, service_name)


def x__attach_exporter__mutmut_11(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach either OTLP or Console exporter to the given provider."""
    if not otlp_endpoint:
        _attach_console_exporter(provider, service_name)
        return
    _attach_otlp_exporter(provider, otlp_endpoint, )

mutants_x__attach_exporter__mutmut['_mutmut_orig'] = x__attach_exporter__mutmut_orig # type: ignore # mutmut generated
mutants_x__attach_exporter__mutmut['x__attach_exporter__mutmut_1'] = x__attach_exporter__mutmut_1 # type: ignore # mutmut generated
mutants_x__attach_exporter__mutmut['x__attach_exporter__mutmut_2'] = x__attach_exporter__mutmut_2 # type: ignore # mutmut generated
mutants_x__attach_exporter__mutmut['x__attach_exporter__mutmut_3'] = x__attach_exporter__mutmut_3 # type: ignore # mutmut generated
mutants_x__attach_exporter__mutmut['x__attach_exporter__mutmut_4'] = x__attach_exporter__mutmut_4 # type: ignore # mutmut generated
mutants_x__attach_exporter__mutmut['x__attach_exporter__mutmut_5'] = x__attach_exporter__mutmut_5 # type: ignore # mutmut generated
mutants_x__attach_exporter__mutmut['x__attach_exporter__mutmut_6'] = x__attach_exporter__mutmut_6 # type: ignore # mutmut generated
mutants_x__attach_exporter__mutmut['x__attach_exporter__mutmut_7'] = x__attach_exporter__mutmut_7 # type: ignore # mutmut generated
mutants_x__attach_exporter__mutmut['x__attach_exporter__mutmut_8'] = x__attach_exporter__mutmut_8 # type: ignore # mutmut generated
mutants_x__attach_exporter__mutmut['x__attach_exporter__mutmut_9'] = x__attach_exporter__mutmut_9 # type: ignore # mutmut generated
mutants_x__attach_exporter__mutmut['x__attach_exporter__mutmut_10'] = x__attach_exporter__mutmut_10 # type: ignore # mutmut generated
mutants_x__attach_exporter__mutmut['x__attach_exporter__mutmut_11'] = x__attach_exporter__mutmut_11 # type: ignore # mutmut generated
mutants_x__attach_console_processor__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__attach_console_processor__mutmut)
def _attach_console_processor(
    provider: Any, log_fn: Callable[..., None], message: str, *args: Any
) -> None:
    """Attach a ConsoleSpanExporter-backed processor and log the given message."""
    processor = _ConsoleProcessor()
    provider.add_span_processor(processor)
    log_fn(message, *args)


def x__attach_console_processor__mutmut_orig(
    provider: Any, log_fn: Callable[..., None], message: str, *args: Any
) -> None:
    """Attach a ConsoleSpanExporter-backed processor and log the given message."""
    processor = _ConsoleProcessor()
    provider.add_span_processor(processor)
    log_fn(message, *args)


def x__attach_console_processor__mutmut_1(
    provider: Any, log_fn: Callable[..., None], message: str, *args: Any
) -> None:
    """Attach a ConsoleSpanExporter-backed processor and log the given message."""
    processor = None
    provider.add_span_processor(processor)
    log_fn(message, *args)


def x__attach_console_processor__mutmut_2(
    provider: Any, log_fn: Callable[..., None], message: str, *args: Any
) -> None:
    """Attach a ConsoleSpanExporter-backed processor and log the given message."""
    processor = _ConsoleProcessor()
    provider.add_span_processor(None)
    log_fn(message, *args)


def x__attach_console_processor__mutmut_3(
    provider: Any, log_fn: Callable[..., None], message: str, *args: Any
) -> None:
    """Attach a ConsoleSpanExporter-backed processor and log the given message."""
    processor = _ConsoleProcessor()
    provider.add_span_processor(processor)
    log_fn(None, *args)


def x__attach_console_processor__mutmut_4(
    provider: Any, log_fn: Callable[..., None], message: str, *args: Any
) -> None:
    """Attach a ConsoleSpanExporter-backed processor and log the given message."""
    processor = _ConsoleProcessor()
    provider.add_span_processor(processor)
    log_fn(*args)


def x__attach_console_processor__mutmut_5(
    provider: Any, log_fn: Callable[..., None], message: str, *args: Any
) -> None:
    """Attach a ConsoleSpanExporter-backed processor and log the given message."""
    processor = _ConsoleProcessor()
    provider.add_span_processor(processor)
    log_fn(message, )

mutants_x__attach_console_processor__mutmut['_mutmut_orig'] = x__attach_console_processor__mutmut_orig # type: ignore # mutmut generated
mutants_x__attach_console_processor__mutmut['x__attach_console_processor__mutmut_1'] = x__attach_console_processor__mutmut_1 # type: ignore # mutmut generated
mutants_x__attach_console_processor__mutmut['x__attach_console_processor__mutmut_2'] = x__attach_console_processor__mutmut_2 # type: ignore # mutmut generated
mutants_x__attach_console_processor__mutmut['x__attach_console_processor__mutmut_3'] = x__attach_console_processor__mutmut_3 # type: ignore # mutmut generated
mutants_x__attach_console_processor__mutmut['x__attach_console_processor__mutmut_4'] = x__attach_console_processor__mutmut_4 # type: ignore # mutmut generated
mutants_x__attach_console_processor__mutmut['x__attach_console_processor__mutmut_5'] = x__attach_console_processor__mutmut_5 # type: ignore # mutmut generated
mutants_x__attach_console_exporter__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__attach_console_exporter__mutmut)
def _attach_console_exporter(provider: Any, service_name: str) -> None:
    """Attach ConsoleSpanExporter to the given provider."""
    _attach_console_processor(
        provider,
        logger.info,
        "OTel tracer configured: ConsoleSpanExporter service=%s",
        service_name,
    )


def x__attach_console_exporter__mutmut_orig(provider: Any, service_name: str) -> None:
    """Attach ConsoleSpanExporter to the given provider."""
    _attach_console_processor(
        provider,
        logger.info,
        "OTel tracer configured: ConsoleSpanExporter service=%s",
        service_name,
    )


def x__attach_console_exporter__mutmut_1(provider: Any, service_name: str) -> None:
    """Attach ConsoleSpanExporter to the given provider."""
    _attach_console_processor(
        None,
        logger.info,
        "OTel tracer configured: ConsoleSpanExporter service=%s",
        service_name,
    )


def x__attach_console_exporter__mutmut_2(provider: Any, service_name: str) -> None:
    """Attach ConsoleSpanExporter to the given provider."""
    _attach_console_processor(
        provider,
        None,
        "OTel tracer configured: ConsoleSpanExporter service=%s",
        service_name,
    )


def x__attach_console_exporter__mutmut_3(provider: Any, service_name: str) -> None:
    """Attach ConsoleSpanExporter to the given provider."""
    _attach_console_processor(
        provider,
        logger.info,
        None,
        service_name,
    )


def x__attach_console_exporter__mutmut_4(provider: Any, service_name: str) -> None:
    """Attach ConsoleSpanExporter to the given provider."""
    _attach_console_processor(
        provider,
        logger.info,
        "OTel tracer configured: ConsoleSpanExporter service=%s",
        None,
    )


def x__attach_console_exporter__mutmut_5(provider: Any, service_name: str) -> None:
    """Attach ConsoleSpanExporter to the given provider."""
    _attach_console_processor(
        logger.info,
        "OTel tracer configured: ConsoleSpanExporter service=%s",
        service_name,
    )


def x__attach_console_exporter__mutmut_6(provider: Any, service_name: str) -> None:
    """Attach ConsoleSpanExporter to the given provider."""
    _attach_console_processor(
        provider,
        "OTel tracer configured: ConsoleSpanExporter service=%s",
        service_name,
    )


def x__attach_console_exporter__mutmut_7(provider: Any, service_name: str) -> None:
    """Attach ConsoleSpanExporter to the given provider."""
    _attach_console_processor(
        provider,
        logger.info,
        service_name,
    )


def x__attach_console_exporter__mutmut_8(provider: Any, service_name: str) -> None:
    """Attach ConsoleSpanExporter to the given provider."""
    _attach_console_processor(
        provider,
        logger.info,
        "OTel tracer configured: ConsoleSpanExporter service=%s",
        )


def x__attach_console_exporter__mutmut_9(provider: Any, service_name: str) -> None:
    """Attach ConsoleSpanExporter to the given provider."""
    _attach_console_processor(
        provider,
        logger.info,
        "XXOTel tracer configured: ConsoleSpanExporter service=%sXX",
        service_name,
    )


def x__attach_console_exporter__mutmut_10(provider: Any, service_name: str) -> None:
    """Attach ConsoleSpanExporter to the given provider."""
    _attach_console_processor(
        provider,
        logger.info,
        "otel tracer configured: consolespanexporter service=%s",
        service_name,
    )


def x__attach_console_exporter__mutmut_11(provider: Any, service_name: str) -> None:
    """Attach ConsoleSpanExporter to the given provider."""
    _attach_console_processor(
        provider,
        logger.info,
        "OTEL TRACER CONFIGURED: CONSOLESPANEXPORTER SERVICE=%S",
        service_name,
    )

mutants_x__attach_console_exporter__mutmut['_mutmut_orig'] = x__attach_console_exporter__mutmut_orig # type: ignore # mutmut generated
mutants_x__attach_console_exporter__mutmut['x__attach_console_exporter__mutmut_1'] = x__attach_console_exporter__mutmut_1 # type: ignore # mutmut generated
mutants_x__attach_console_exporter__mutmut['x__attach_console_exporter__mutmut_2'] = x__attach_console_exporter__mutmut_2 # type: ignore # mutmut generated
mutants_x__attach_console_exporter__mutmut['x__attach_console_exporter__mutmut_3'] = x__attach_console_exporter__mutmut_3 # type: ignore # mutmut generated
mutants_x__attach_console_exporter__mutmut['x__attach_console_exporter__mutmut_4'] = x__attach_console_exporter__mutmut_4 # type: ignore # mutmut generated
mutants_x__attach_console_exporter__mutmut['x__attach_console_exporter__mutmut_5'] = x__attach_console_exporter__mutmut_5 # type: ignore # mutmut generated
mutants_x__attach_console_exporter__mutmut['x__attach_console_exporter__mutmut_6'] = x__attach_console_exporter__mutmut_6 # type: ignore # mutmut generated
mutants_x__attach_console_exporter__mutmut['x__attach_console_exporter__mutmut_7'] = x__attach_console_exporter__mutmut_7 # type: ignore # mutmut generated
mutants_x__attach_console_exporter__mutmut['x__attach_console_exporter__mutmut_8'] = x__attach_console_exporter__mutmut_8 # type: ignore # mutmut generated
mutants_x__attach_console_exporter__mutmut['x__attach_console_exporter__mutmut_9'] = x__attach_console_exporter__mutmut_9 # type: ignore # mutmut generated
mutants_x__attach_console_exporter__mutmut['x__attach_console_exporter__mutmut_10'] = x__attach_console_exporter__mutmut_10 # type: ignore # mutmut generated
mutants_x__attach_console_exporter__mutmut['x__attach_console_exporter__mutmut_11'] = x__attach_console_exporter__mutmut_11 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__attach_otlp_exporter__mutmut)
def _attach_otlp_exporter(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_orig(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_1(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = None
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_2(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is not None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_3(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            None,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_4(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            None,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_5(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            None,
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_6(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_7(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_8(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_9(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "XXopentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporterXX",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_10(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to consolespanexporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_11(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "OPENTELEMETRY-EXPORTER-OTLP NOT INSTALLED; FALLING BACK TO CONSOLESPANEXPORTER",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_12(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = None
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_13(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=None)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_14(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(None)
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_15(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(None))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_16(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        None,
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_17(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        None,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_18(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        None,
    )


def x__attach_otlp_exporter__mutmut_19(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_20(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        service_name,
    )


def x__attach_otlp_exporter__mutmut_21(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTel tracer configured: OTLP endpoint=%s service=%s",
        otlp_endpoint,
        )


def x__attach_otlp_exporter__mutmut_22(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "XXOTel tracer configured: OTLP endpoint=%s service=%sXX",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_23(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "otel tracer configured: otlp endpoint=%s service=%s",
        otlp_endpoint,
        service_name,
    )


def x__attach_otlp_exporter__mutmut_24(provider: Any, otlp_endpoint: str, service_name: str) -> None:
    """Attach OTLP exporter to the given provider."""
    otlp = _import_otlp()
    if otlp is None:
        _attach_console_processor(
            provider,
            logger.warning,
            "opentelemetry-exporter-otlp not installed; falling back to ConsoleSpanExporter",
        )
        return

    exporter = otlp.OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(otlp.BatchSpanProcessor(exporter))
    logger.info(
        "OTEL TRACER CONFIGURED: OTLP ENDPOINT=%S SERVICE=%S",
        otlp_endpoint,
        service_name,
    )

mutants_x__attach_otlp_exporter__mutmut['_mutmut_orig'] = x__attach_otlp_exporter__mutmut_orig # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_1'] = x__attach_otlp_exporter__mutmut_1 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_2'] = x__attach_otlp_exporter__mutmut_2 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_3'] = x__attach_otlp_exporter__mutmut_3 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_4'] = x__attach_otlp_exporter__mutmut_4 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_5'] = x__attach_otlp_exporter__mutmut_5 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_6'] = x__attach_otlp_exporter__mutmut_6 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_7'] = x__attach_otlp_exporter__mutmut_7 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_8'] = x__attach_otlp_exporter__mutmut_8 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_9'] = x__attach_otlp_exporter__mutmut_9 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_10'] = x__attach_otlp_exporter__mutmut_10 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_11'] = x__attach_otlp_exporter__mutmut_11 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_12'] = x__attach_otlp_exporter__mutmut_12 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_13'] = x__attach_otlp_exporter__mutmut_13 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_14'] = x__attach_otlp_exporter__mutmut_14 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_15'] = x__attach_otlp_exporter__mutmut_15 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_16'] = x__attach_otlp_exporter__mutmut_16 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_17'] = x__attach_otlp_exporter__mutmut_17 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_18'] = x__attach_otlp_exporter__mutmut_18 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_19'] = x__attach_otlp_exporter__mutmut_19 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_20'] = x__attach_otlp_exporter__mutmut_20 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_21'] = x__attach_otlp_exporter__mutmut_21 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_22'] = x__attach_otlp_exporter__mutmut_22 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_23'] = x__attach_otlp_exporter__mutmut_23 # type: ignore # mutmut generated
mutants_x__attach_otlp_exporter__mutmut['x__attach_otlp_exporter__mutmut_24'] = x__attach_otlp_exporter__mutmut_24 # type: ignore # mutmut generated
mutants_x__import_otlp__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__import_otlp__mutmut)
def _import_otlp() -> Any | None:
    """Lazy-import the OTLP exporter; returns None on ImportError."""
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        return SimpleNamespace(
            OTLPSpanExporter=OTLPSpanExporter,
            BatchSpanProcessor=BatchSpanProcessor,
        )
    except ImportError:
        return None


def x__import_otlp__mutmut_orig() -> Any | None:
    """Lazy-import the OTLP exporter; returns None on ImportError."""
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        return SimpleNamespace(
            OTLPSpanExporter=OTLPSpanExporter,
            BatchSpanProcessor=BatchSpanProcessor,
        )
    except ImportError:
        return None


def x__import_otlp__mutmut_1() -> Any | None:
    """Lazy-import the OTLP exporter; returns None on ImportError."""
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        return SimpleNamespace(
            OTLPSpanExporter=None,
            BatchSpanProcessor=BatchSpanProcessor,
        )
    except ImportError:
        return None


def x__import_otlp__mutmut_2() -> Any | None:
    """Lazy-import the OTLP exporter; returns None on ImportError."""
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        return SimpleNamespace(
            OTLPSpanExporter=OTLPSpanExporter,
            BatchSpanProcessor=None,
        )
    except ImportError:
        return None


def x__import_otlp__mutmut_3() -> Any | None:
    """Lazy-import the OTLP exporter; returns None on ImportError."""
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        return SimpleNamespace(
            BatchSpanProcessor=BatchSpanProcessor,
        )
    except ImportError:
        return None


def x__import_otlp__mutmut_4() -> Any | None:
    """Lazy-import the OTLP exporter; returns None on ImportError."""
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        return SimpleNamespace(
            OTLPSpanExporter=OTLPSpanExporter,
            )
    except ImportError:
        return None

mutants_x__import_otlp__mutmut['_mutmut_orig'] = x__import_otlp__mutmut_orig # type: ignore # mutmut generated
mutants_x__import_otlp__mutmut['x__import_otlp__mutmut_1'] = x__import_otlp__mutmut_1 # type: ignore # mutmut generated
mutants_x__import_otlp__mutmut['x__import_otlp__mutmut_2'] = x__import_otlp__mutmut_2 # type: ignore # mutmut generated
mutants_x__import_otlp__mutmut['x__import_otlp__mutmut_3'] = x__import_otlp__mutmut_3 # type: ignore # mutmut generated
mutants_x__import_otlp__mutmut['x__import_otlp__mutmut_4'] = x__import_otlp__mutmut_4 # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_ConsoleProcessorǁon_start__mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_ConsoleProcessorǁon_end__mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_ConsoleProcessorǁshutdown__mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_ConsoleProcessorǁforce_flush__mutmut: MutantDict = {}  # type: ignore


class _ConsoleProcessor:
    """Thin wrapper that delegates to SimpleSpanProcessor(ConsoleSpanExporter())."""

    @_mutmut_mutated(mutants_xǁ_ConsoleProcessorǁ__init____mutmut)
    def __init__(self) -> None:
        """Initialize by creating the underlying OpenTelemetry processor."""
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        self._processor = SimpleSpanProcessor(ConsoleSpanExporter())

    def xǁ_ConsoleProcessorǁ__init____mutmut_orig(self) -> None:
        """Initialize by creating the underlying OpenTelemetry processor."""
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        self._processor = SimpleSpanProcessor(ConsoleSpanExporter())

    def xǁ_ConsoleProcessorǁ__init____mutmut_1(self) -> None:
        """Initialize by creating the underlying OpenTelemetry processor."""
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        self._processor = None

    def xǁ_ConsoleProcessorǁ__init____mutmut_2(self) -> None:
        """Initialize by creating the underlying OpenTelemetry processor."""
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        self._processor = SimpleSpanProcessor(None)

    @_mutmut_mutated(mutants_xǁ_ConsoleProcessorǁon_start__mutmut)
    def on_start(self, span: Any, parent_context: Any = None) -> None:
        """Delegate span-start callback to the underlying processor."""
        self._processor.on_start(span, parent_context)

    def xǁ_ConsoleProcessorǁon_start__mutmut_orig(self, span: Any, parent_context: Any = None) -> None:
        """Delegate span-start callback to the underlying processor."""
        self._processor.on_start(span, parent_context)

    def xǁ_ConsoleProcessorǁon_start__mutmut_1(self, span: Any, parent_context: Any = None) -> None:
        """Delegate span-start callback to the underlying processor."""
        self._processor.on_start(None, parent_context)

    def xǁ_ConsoleProcessorǁon_start__mutmut_2(self, span: Any, parent_context: Any = None) -> None:
        """Delegate span-start callback to the underlying processor."""
        self._processor.on_start(span, None)

    def xǁ_ConsoleProcessorǁon_start__mutmut_3(self, span: Any, parent_context: Any = None) -> None:
        """Delegate span-start callback to the underlying processor."""
        self._processor.on_start(parent_context)

    def xǁ_ConsoleProcessorǁon_start__mutmut_4(self, span: Any, parent_context: Any = None) -> None:
        """Delegate span-start callback to the underlying processor."""
        self._processor.on_start(span, )

    @_mutmut_mutated(mutants_xǁ_ConsoleProcessorǁon_end__mutmut)
    def on_end(self, *args: Any, **kwargs: Any) -> None:
        """Delegate span-end callback to the underlying processor."""
        self._processor.on_end(*args, **kwargs)

    def xǁ_ConsoleProcessorǁon_end__mutmut_orig(self, *args: Any, **kwargs: Any) -> None:
        """Delegate span-end callback to the underlying processor."""
        self._processor.on_end(*args, **kwargs)

    def xǁ_ConsoleProcessorǁon_end__mutmut_1(self, *args: Any, **kwargs: Any) -> None:
        """Delegate span-end callback to the underlying processor."""
        self._processor.on_end(**kwargs)

    def xǁ_ConsoleProcessorǁon_end__mutmut_2(self, *args: Any, **kwargs: Any) -> None:
        """Delegate span-end callback to the underlying processor."""
        self._processor.on_end(*args, )

    @_mutmut_mutated(mutants_xǁ_ConsoleProcessorǁshutdown__mutmut)
    def shutdown(self, *args: Any, **kwargs: Any) -> None:
        """Delegate shutdown callback to the underlying processor."""
        self._processor.shutdown(*args, **kwargs)

    def xǁ_ConsoleProcessorǁshutdown__mutmut_orig(self, *args: Any, **kwargs: Any) -> None:
        """Delegate shutdown callback to the underlying processor."""
        self._processor.shutdown(*args, **kwargs)

    def xǁ_ConsoleProcessorǁshutdown__mutmut_1(self, *args: Any, **kwargs: Any) -> None:
        """Delegate shutdown callback to the underlying processor."""
        self._processor.shutdown(**kwargs)

    def xǁ_ConsoleProcessorǁshutdown__mutmut_2(self, *args: Any, **kwargs: Any) -> None:
        """Delegate shutdown callback to the underlying processor."""
        self._processor.shutdown(*args, )

    @_mutmut_mutated(mutants_xǁ_ConsoleProcessorǁforce_flush__mutmut)
    def force_flush(self, *args: Any, **kwargs: Any) -> bool:
        """Delegate force-flush callback to the underlying processor."""
        result = self._processor.force_flush(*args, **kwargs)
        return bool(result)

    def xǁ_ConsoleProcessorǁforce_flush__mutmut_orig(self, *args: Any, **kwargs: Any) -> bool:
        """Delegate force-flush callback to the underlying processor."""
        result = self._processor.force_flush(*args, **kwargs)
        return bool(result)

    def xǁ_ConsoleProcessorǁforce_flush__mutmut_1(self, *args: Any, **kwargs: Any) -> bool:
        """Delegate force-flush callback to the underlying processor."""
        result = None
        return bool(result)

    def xǁ_ConsoleProcessorǁforce_flush__mutmut_2(self, *args: Any, **kwargs: Any) -> bool:
        """Delegate force-flush callback to the underlying processor."""
        result = self._processor.force_flush(**kwargs)
        return bool(result)

    def xǁ_ConsoleProcessorǁforce_flush__mutmut_3(self, *args: Any, **kwargs: Any) -> bool:
        """Delegate force-flush callback to the underlying processor."""
        result = self._processor.force_flush(*args, )
        return bool(result)

    def xǁ_ConsoleProcessorǁforce_flush__mutmut_4(self, *args: Any, **kwargs: Any) -> bool:
        """Delegate force-flush callback to the underlying processor."""
        result = self._processor.force_flush(*args, **kwargs)
        return bool(None)

mutants_xǁ_ConsoleProcessorǁ__init____mutmut['_mutmut_orig'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁ__init____mutmut['xǁ_ConsoleProcessorǁ__init____mutmut_1'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁ__init____mutmut['xǁ_ConsoleProcessorǁ__init____mutmut_2'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁ__init____mutmut_2 # type: ignore # mutmut generated

mutants_xǁ_ConsoleProcessorǁon_start__mutmut['_mutmut_orig'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁon_start__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁon_start__mutmut['xǁ_ConsoleProcessorǁon_start__mutmut_1'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁon_start__mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁon_start__mutmut['xǁ_ConsoleProcessorǁon_start__mutmut_2'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁon_start__mutmut_2 # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁon_start__mutmut['xǁ_ConsoleProcessorǁon_start__mutmut_3'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁon_start__mutmut_3 # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁon_start__mutmut['xǁ_ConsoleProcessorǁon_start__mutmut_4'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁon_start__mutmut_4 # type: ignore # mutmut generated

mutants_xǁ_ConsoleProcessorǁon_end__mutmut['_mutmut_orig'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁon_end__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁon_end__mutmut['xǁ_ConsoleProcessorǁon_end__mutmut_1'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁon_end__mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁon_end__mutmut['xǁ_ConsoleProcessorǁon_end__mutmut_2'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁon_end__mutmut_2 # type: ignore # mutmut generated

mutants_xǁ_ConsoleProcessorǁshutdown__mutmut['_mutmut_orig'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁshutdown__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁshutdown__mutmut['xǁ_ConsoleProcessorǁshutdown__mutmut_1'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁshutdown__mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁshutdown__mutmut['xǁ_ConsoleProcessorǁshutdown__mutmut_2'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁshutdown__mutmut_2 # type: ignore # mutmut generated

mutants_xǁ_ConsoleProcessorǁforce_flush__mutmut['_mutmut_orig'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁforce_flush__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁforce_flush__mutmut['xǁ_ConsoleProcessorǁforce_flush__mutmut_1'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁforce_flush__mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁforce_flush__mutmut['xǁ_ConsoleProcessorǁforce_flush__mutmut_2'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁforce_flush__mutmut_2 # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁforce_flush__mutmut['xǁ_ConsoleProcessorǁforce_flush__mutmut_3'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁforce_flush__mutmut_3 # type: ignore # mutmut generated
mutants_xǁ_ConsoleProcessorǁforce_flush__mutmut['xǁ_ConsoleProcessorǁforce_flush__mutmut_4'] = _ConsoleProcessor.xǁ_ConsoleProcessorǁforce_flush__mutmut_4 # type: ignore # mutmut generated
