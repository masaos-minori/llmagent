# Implementation: stdio_lifecycle.py

## Goal

Replace `TransportState` enum with `LifecycleState` (from `lifecycle.py`), replace `except Exception` handlers with specific exception types, and call `assert_valid_transition` before every state change.

## Scope

- Target: `scripts/agent/stdio_lifecycle.py`
- Delete `TransportState` class; replace all references with `LifecycleState`
- Replace `except Exception` in `_start()` and `_stop_stdio()` with specific types
- Call `assert_valid_transition(old_state, new_state)` in `_start()`, `_stop_stdio()`, `restart()`
- `TransportHandle.state` type changes from `TransportState` to `LifecycleState`

## Assumptions

1. `lifecycle.py` already exports `LifecycleState` and `assert_valid_transition` (after `lifecycle_py.md` is implemented).
2. `STARTING` state from `LifecycleState` is used when `_start()` begins (before `await new_transport.start()` completes).
3. `StdioTransport.start()` raises on failure — likely `OSError` or `RuntimeError`; catch only those.

## Implementation

### Target file

`scripts/agent/stdio_lifecycle.py`

### Procedure

1. Remove `class TransportState(Enum): ...`.
2. Add `from agent.lifecycle import LifecycleState, assert_valid_transition`.
3. Replace all `TransportState.*` references with `LifecycleState.*`.
4. In `_start()`:
   - Before `await new_transport.start()`, set handle to `STARTING` state.
   - On success, transition to `RUNNING` via `assert_valid_transition`.
   - Replace `except Exception as e:` with `except (OSError, RuntimeError) as e:`.
   - On exception, transition to `FAILED` via `assert_valid_transition`.
5. In `_stop_stdio()`:
   - Replace `except Exception as e:` with `except (OSError, RuntimeError) as e:`.
   - Call `assert_valid_transition` before setting `STOPPED` and `FAILED`.
6. In `restart()`: call `assert_valid_transition` after stop and before start.

### Method

Import-and-replace for the enum. Wrap each `handle.state = X` with `assert_valid_transition(old, X)` to enforce the state machine.

### Details

```python
from agent.lifecycle import LifecycleState, assert_valid_transition

# _start() — key changes
old = (self._handles.get(server_key) or TransportHandle(None, LifecycleState.STOPPED)).state
assert_valid_transition(old, LifecycleState.STARTING)
self._handles[server_key] = TransportHandle(transport=None, state=LifecycleState.STARTING)
try:
    await new_transport.start()
    assert_valid_transition(LifecycleState.STARTING, LifecycleState.RUNNING)
    self._handles[server_key] = TransportHandle(transport=new_transport, state=LifecycleState.RUNNING)
except (OSError, RuntimeError) as e:
    assert_valid_transition(LifecycleState.STARTING, LifecycleState.FAILED)
    self._handles[server_key] = TransportHandle(transport=None, state=LifecycleState.FAILED, last_error=str(e))
    raise
```

Update `factory.py`'s `_transport_state_to_lifecycle()` function: it converts `TransportState → LifecycleState`, which is no longer needed after this change. Remove it.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/stdio_lifecycle.py scripts/agent/factory.py` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Tests | `uv run pytest tests/ -k "stdio_lifecycle or lifecycle"` | all pass |
