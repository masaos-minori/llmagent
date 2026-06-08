# Implementation: LifecycleState, HttpStartupError, TransportHandle

## Goal

Add LifecycleState enum to lifecycle.py, HttpStartupError to http_lifecycle.py,
and TransportHandle to stdio_lifecycle.py for better diagnostics and state unification.

## Scope

**In:**
- `lifecycle.py`: add `LifecycleState` enum; update `get_transport_state()` to return
  `LifecycleState` (mapped from `TransportState`)
- `http_lifecycle.py`: add `HttpStartupError(RuntimeError)`; replace two bare
  `raise RuntimeError(...)` calls
- `stdio_lifecycle.py`: add `TransportHandle(transport, state, last_error)` dataclass;
  replace `_transport_states: dict[str, TransportState]` with
  `_handles: dict[str, TransportHandle]`; keep `_stdio_procs` to maintain the
  external shared-dict reference used by AppServices

**Out:**
- Removing `_stdio_procs` from StdioServerLifecycleManager (external ref preserved)
- Changing `get_transport_state()` return type in repl_health.py callers

## Assumptions

- `_stdio_procs` is a shared dict reference passed from factory.py; must not be removed
- Existing 57 tests in test_lifecycle.py act as behavioral guard
- `TransportState` is not deleted; LifecycleState maps from it

## Implementation

### lifecycle.py

Add after imports:
```python
from enum import Enum
class LifecycleState(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED  = "failed"
    UNKNOWN = "unknown"
```

Update `get_transport_state()` to return `LifecycleState`:
- `TransportState.RUNNING` → `LifecycleState.RUNNING`
- `TransportState.STOPPED` → `LifecycleState.STOPPED`
- `TransportState.FAILED`  → `LifecycleState.FAILED`
- HTTP transport / None    → `LifecycleState.UNKNOWN`

### http_lifecycle.py

Add after StartupFailure:
```python
class HttpStartupError(RuntimeError):
    def __init__(self, failure: StartupFailure) -> None:
        self.failure = failure
        super().__init__(failure.reason)
```

Replace two bare `raise RuntimeError(...)` with `raise HttpStartupError(failure)`.

### stdio_lifecycle.py

Add after TransportState:
```python
@dataclass
class TransportHandle:
    transport: StdioTransport | None
    state: TransportState
    last_error: str | None = None
```

Replace `_transport_states` with `_handles: dict[str, TransportHandle]`.
Keep `_stdio_procs` unchanged for AppServices shared-dict compat.

## Validation plan

```bash
uv run ruff check scripts/agent/lifecycle.py scripts/agent/http_lifecycle.py \
                   scripts/agent/stdio_lifecycle.py
uv run mypy scripts/
uv run pytest tests/test_lifecycle.py -v
```
