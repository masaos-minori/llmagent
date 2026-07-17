#!/usr/bin/env python3
"""shared/otel_noop.py — No-op OpenTelemetry tracer and span for disabled tracing."""

from typing import Any


class NoOpTracer:
    """Minimal tracer stub for otel_enabled=False.

    Returns a NoOpSpan from start_as_current_span().
    """

    def start_as_current_span(self, name: str, **kwargs: Any) -> "NoOpSpan":
        """Return a no-op span without recording any telemetry."""
        return NoOpSpan()

    def __repr__(self) -> str:
        """Return string representation of this no-op tracer."""
        return "_NoOpTracer()"


class NoOpSpan:
    """No-op span that supports context manager protocol and set_attribute()."""

    def __enter__(self) -> "NoOpSpan":
        """Enter the span context manager (no-op)."""
        return self

    def __exit__(self, *args: object) -> None:
        """Exit the span context manager (no-op)."""
        pass

    def set_attribute(self, _key: str, _value: Any) -> None:
        """Set an attribute on this no-op span (no-op)."""
        pass
