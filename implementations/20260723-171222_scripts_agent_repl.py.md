## Goal

Wrap `ctx.session.start()` in `_run_repl_loop()` with a dedicated try/except that catches both `RuntimeError` and `sqlite3.Error`, emitting user-friendly messages before re-raising so the outer handler produces consistent output.

## Scope

**In:**
- `scripts/agent/repl.py`: Add nested try/except around `ctx.session.start()` in `_run_repl_loop()`

**Out:**
- Modifying `session.py` — the existing "no such table" error message there is already correct
- Changing the outer `except RuntimeError` handler behavior beyond what is needed for consistency
- Any other file modifications

## Assumptions

1. The inner handler should catch `RuntimeError` and `sqlite3.Error`, write a user-friendly message via `self._view.write_fatal()`, then re-raise as `RuntimeError` so the outer handler handles cleanup uniformly.
2. The outer `except RuntimeError` handler will always receive a `RuntimeError` after this change, producing consistent formatting regardless of the original exception type.
3. The `sqlite3.Error` message should suggest checking DB connectivity or running `bash deploy/init_db.sh`.

## Design decisions

- Re-raise as `RuntimeError` rather than letting the original exception propagate, ensuring the outer handler sees a uniform exception type.
- Use `from None` to suppress the chained exception traceback, preventing operator confusion about the root cause.

## Alternatives considered

- Catch `sqlite3.Error` in the outer handler alongside `RuntimeError`: would require duplicating the error message logic in two places.
- Do not re-raise and let the finally block handle cleanup: would prevent the REPL loop from exiting cleanly after an unrecoverable error.

## Implementation

### Target file

`scripts/agent/repl.py`

### Procedure

1. Locate `_run_repl_loop()` method in `AgentREPL` class (line ~413)
2. Find `ctx.session.start()` call (line ~418)
3. Wrap the call in a nested try/except block
4. Add RuntimeError handler with "no such table" detection
5. Add sqlite3.Error handler with database availability messaging
6. Both handlers re-raise as `RuntimeError` with `from None`

### Method

Inline modification of existing method — no new methods or classes required.

### Details

```python
try:
    ctx.session.start()
except RuntimeError as e:
    msg = str(e)
    if "no such table" in msg.lower():
        self._view.write_fatal("Session schema missing. Run: bash deploy/init_db.sh to initialize the database.")
    else:
        self._view.write_fatal(f"Session start failed: {msg}")
    # Re-raise as RuntimeError with a clean message so the outer handler
    # produces consistent formatting regardless of the original exception type.
    raise RuntimeError(msg) from None
except sqlite3.Error as e:
    self._view.write_fatal(f"Database unavailable during session start: {e}. Check DB connectivity or run: bash deploy/init_db.sh")
    # Wrap in RuntimeError so the outer handler treats it uniformly.
    raise RuntimeError(f"Database unavailable: {e}") from None
```

## Compatibility considerations

N/A — only affects error handling path; no API changes.

## Security considerations

N/A — no security impact; only improves error message clarity.

## Rollback considerations

Simple revert of the try/except block addition; no data migration or config changes required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/repl.py | Lint | `ruff check scripts/agent/repl.py` | 0 errors |
| scripts/agent/repl.py | Type check | `mypy scripts/agent/repl.py` | no new errors |
| scripts/agent/repl.py | Architecture | `lint-imports` | 0 violations |
| scripts/agent/repl.py | Tests | `pytest tests/test_agent/ -k repl` | all pass |
| scripts/agent/repl.py | Manual test | Remove the session table, start REPL | Verify the startup banner shows the correct error message without tracebacks |

## Out of scope

- Modifying `session.py` — the existing "no such table" error message there is already correct
- Changing the outer `except RuntimeError` handler behavior beyond what is needed for consistency
- Any other file modifications

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-144652_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-171222
- Related target files: scripts/agent/repl.py
