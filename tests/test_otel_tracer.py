"""
tests/test_otel_tracer.py
Behavior-lock tests for otel_tracer.build_tracer().

Verifies:
  - build_tracer(enabled=False) returns a NoOp tracer that records no spans
  - build_tracer(enabled=True, otlp_endpoint="") returns an OTel tracer bound
    to a private ConsoleSpanExporter provider
  - Multiple build_tracer() calls do NOT modify the global trace provider (R10)
  - _NoOpTracer.start_as_current_span() works as a context manager
  - _NoOpSpan.set_attribute() accepts calls without raising
"""

from __future__ import annotations

from otel_tracer import _NoOpSpan, _NoOpTracer, build_tracer

# ── build_tracer(enabled=False) ───────────────────────────────────────────────


class TestBuildTracerDisabled:
    def test_returns_noop_tracer(self) -> None:
        tracer = build_tracer(enabled=False)
        assert isinstance(tracer, _NoOpTracer)

    def test_noop_tracer_span_is_context_manager(self) -> None:
        tracer = build_tracer(enabled=False)
        # Must not raise; must support 'with' syntax
        with tracer.start_as_current_span("test_span") as span:
            span.set_attribute("key", "value")

    def test_noop_tracer_returns_noop_span(self) -> None:
        tracer = build_tracer(enabled=False)
        span = tracer.start_as_current_span("test")
        assert isinstance(span, _NoOpSpan)

    def test_noop_span_set_attribute_does_not_raise(self) -> None:
        span = _NoOpSpan()
        span.set_attribute("int_key", 42)
        span.set_attribute("bool_key", True)
        span.set_attribute("str_key", "value")


# ── build_tracer(enabled=True) ────────────────────────────────────────────────


class TestBuildTracerEnabled:
    def test_returns_non_noop_tracer(self) -> None:
        tracer = build_tracer(
            enabled=True, service_name="test-service", otlp_endpoint=""
        )
        # Should NOT be a _NoOpTracer when OTel SDK is available
        assert not isinstance(tracer, _NoOpTracer)

    def test_tracer_supports_start_as_current_span(self) -> None:
        tracer = build_tracer(
            enabled=True, service_name="test-service", otlp_endpoint=""
        )
        # Must not raise; the OTel tracer supports context manager protocol
        with tracer.start_as_current_span("test_op"):
            pass

    def test_tracer_service_name_parameter_accepted(self) -> None:
        # No exception expected regardless of service name
        tracer = build_tracer(
            enabled=True, service_name="my-custom-agent", otlp_endpoint=""
        )
        assert tracer is not None


# ── Global provider isolation (R10) ───────────────────────────────────────────


class TestGlobalProviderIsolation:
    def test_global_provider_unchanged_after_two_calls(self) -> None:
        """build_tracer() must NOT call trace.set_tracer_provider().

        The global trace provider should remain the same object before and after
        multiple build_tracer() calls.
        """
        from opentelemetry import trace

        global_provider_before = trace.get_tracer_provider()

        build_tracer(enabled=True, service_name="svc-1", otlp_endpoint="")
        build_tracer(enabled=True, service_name="svc-2", otlp_endpoint="")

        global_provider_after = trace.get_tracer_provider()
        assert global_provider_before is global_provider_after

    def test_disabled_tracer_does_not_touch_global_provider(self) -> None:
        from opentelemetry import trace

        global_provider_before = trace.get_tracer_provider()
        build_tracer(enabled=False)
        assert trace.get_tracer_provider() is global_provider_before
