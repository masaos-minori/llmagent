# Implementation and Test Procedure: Graceful SIGTERM Shutdown

## Goal

Implement graceful SIGTERM shutdown with 10-second timeout. Adds `is_processing` flag to `ConvState` and a SIGTERM handler to `repl.py`.

## Scope

**In:**
- `scripts/agent/context.py` — add `is_processing: bool = False` to `ConvState`
- `scripts/agent/repl.py` — register SIGTERM handler; set `shutdown_requested=True` and wait up to 10s for current turn to finish before exiting

**Out:**
- Changing existing `shutdown_requested` flag semantics
- Timeout configuration (hardcoded 10s per requirement)

## Assumptions

1. `ConvState` (or `AgentContext`) already has `shutdown_requested: bool = False` at `context.py:64`.
2. `repl.py` has a main REPL loop that processes one turn at a time.
3. `is_processing` is set to `True` at the start of turn processing and `False` at the end.
4. SIGTERM handler: sets `shutdown_requested=True`; main loop checks this flag and exits gracefully.

## Implementation

### Target files
- `scripts/agent/context.py`
- `scripts/agent/repl.py`

### Details

**context.py — add to ConvState:**
```python
is_processing: bool = False  # True while handle_turn() is executing
```

**repl.py — SIGTERM handler:**
```python
import signal
import time

def _register_sigterm_handler(ctx: AgentContext) -> None:
    def _handler(signum: int, frame: object) -> None:
        ctx.shutdown_requested = True
        if ctx.is_processing:
            # Wait up to 10s for current turn to complete
            deadline = time.monotonic() + 10.0
            while ctx.is_processing and time.monotonic() < deadline:
                time.sleep(0.1)
        # Force exit after timeout
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, _handler)
```

**repl.py — set is_processing around handle_turn():**
```python
ctx.is_processing = True
try:
    await orchestrator.handle_turn(line)
finally:
    ctx.is_processing = False
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Flag exists | `grep -n "is_processing" scripts/agent/context.py` | found |
| Handler registered | `grep -n "SIGTERM\|sigterm" scripts/agent/repl.py` | found |
| Lint | `uv run ruff check scripts/agent/context.py scripts/agent/repl.py` | 0 errors |
| Tests | `uv run pytest tests/test_graceful_shutdown.py -v` | all pass |
