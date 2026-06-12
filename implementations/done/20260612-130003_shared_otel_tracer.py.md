# Goal

Fix the `_ConsoleProcessor.start_span()` bug (calls nonexistent method on
`SimpleSpanProcessor`), add a `TracerProtocol` Protocol, and change
`build_tracer()` to return `TracerProtocol` instead of `Any`.

# Scope

- `scripts/shared/otel_tracer.py`

# Assumptions

1. `SimpleSpanProcessor` implements `SpanProcessor` interface which has `on_start()`
   and `on_end()` — NOT `start_span()`. The `start_span()` method does not exist on
   `SimpleSpanProcessor`, causing the current mypy `attr-defined` error.
2. The correct method to forward is `on_start(span, parent_context)`.
3. `TracerProtocol` only needs `start_as_current_span()` since that is the only
   method called by agent code.
4. Both `_NoOpTracer` and the real OTel tracer implement `start_as_current_span()`,
   so the Protocol is satisfied by both.

# Implementation

## Target file

`scripts/shared/otel_tracer.py`

## Procedure

1. Add `TracerProtocol` Protocol class before `build_tracer()`:
   ```python
   from typing import Protocol

   class TracerProtocol(Protocol):
       def start_as_current_span(self, name: str, **kwargs: Any) -> Any: ...
   ```

2. Change `build_tracer()` signature:
   ```python
   def build_tracer(
       enabled: bool,
       service_name: str = "llm-agent",
       otlp_endpoint: str = "",
   ) -> TracerProtocol:
   ```

3. Replace `_ConsoleProcessor.start_span()` with `on_start()`:
   ```python
   # Before
   def start_span(self, *args: Any, **kwargs: Any) -> Any:
       return self._processor.start_span(*args, **kwargs)

   # After
   def on_start(self, span: Any, parent_context: Any = None) -> None:
       self._processor.on_start(span, parent_context)
   ```

4. Run ruff + mypy (the existing `attr-defined` error on line 126 must disappear).

## Method

- Remove one method (`start_span`), add one method (`on_start`)
- Add `TracerProtocol` Protocol
- Change return type annotation of `build_tracer()`

# Validation plan

- `grep -n "start_span" scripts/shared/otel_tracer.py` → 0 hits
- `uv run mypy scripts/shared/otel_tracer.py` → 0 errors (currently has 1)
- `uv run ruff check scripts/shared/otel_tracer.py`
- `uv run pytest tests/test_otel_tracer.py -v`
