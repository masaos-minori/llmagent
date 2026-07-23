## Goal

Aggregate resource close errors during shutdown and emit a consolidated summary log entry for better situational awareness.

## Scope

**In:**
- `scripts/agent/repl.py`: Add error collection mechanism to `_close_resources()`

**Out:**
- Modifying the resource close logic itself
- Adding new configuration options for error thresholds
- Any other file modifications

## Assumptions

1. Each resource close operation currently has its own try/except — this pattern will be preserved.
2. Individual error logs must remain for traceability — the summary supplements, not replaces, them.
3. The summary format uses semicolon-separated `"resource_name: error_message"` pairs.
4. If no errors occur, no summary is emitted (no noise for successful shutdowns).

## Design decisions

- Collect errors as `(resource_name, error_message)` tuples rather than raw exceptions to avoid serialization issues in log handlers.
- Include exception type in the summary for clarity: `"resource_name: TypeError(...)"` instead of just `"resource_name: <exception string>"`.
- Emit summary after all individual logs so operators can see both granular and aggregate views.

## Alternatives considered

- Replace individual error logs with only the summary: loses traceability of which specific resource failed first.
- Use structured logging with a custom handler that automatically aggregates shutdown errors: adds complexity and coupling to the logging infrastructure.
- Send external notification on multiple failures: out of scope for this change; logging is sufficient for now.

## Implementation

### Target file

`scripts/agent/repl.py`

### Procedure

1. Locate `AgentREPL._close_resources()` method (line ~255)
2. Add error collection list at the start of the method
3. Modify each resource close operation's try/except to append errors instead of logging immediately
4. Add summary log at the end of the method

### Method

Inline modification of existing method — no new methods or classes required.

### Details

```python
# At start of _close_resources():
errors: list[tuple[str, str]] = []

# Modify each resource close operation:
try:
    with SQLiteHelper("session").open(write_mode=True) as db:
        db.checkpoint("TRUNCATE")
    logger.info("WAL checkpoint completed on shutdown")
except sqlite3.Error as e:
    errors.append(("wal_checkpoint", f"{type(e).__name__}: {e}"))
    logger.warning("WAL checkpoint failed on shutdown: %s", e)

if svc is not None:
    try:
        await svc.lifecycle.shutdown_all()
    except Exception as e:
        errors.append(("lifecycle_shutdown", f"{type(e).__name__}: {e}"))
        logger.error("Lifecycle shutdown failed: %s", e)
    
    try:
        await svc.http.aclose()
    except Exception as e:
        errors.append(("http_close", f"{type(e).__name__}: {e}"))
        logger.error("HTTP client close failed: %s", e)

# At end of method:
if errors:
    summary = "; ".join(f"{name}: {err}" for name, err in errors)
    logger.error("Resource close errors (%d): %s", len(errors), summary)
```

## Compatibility considerations

N/A — only affects error handling path; no API changes.

## Security considerations

N/A — no security impact; only improves operational visibility for shutdown errors.

## Rollback considerations

Simple revert of the error aggregation addition; no data migration or config changes required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/repl.py | Lint | `ruff check scripts/agent/repl.py` | 0 errors |
| scripts/agent/repl.py | Type check | `mypy scripts/agent/repl.py` | no new errors |
| scripts/agent/repl.py | Architecture | `lint-imports` | 0 violations |
| scripts/agent/repl.py | Tests | `pytest tests/test_agent/ -k repl` | all pass |
| scripts/agent/repl.py | Manual test | Lock SQLite DB during shutdown | Observe summary log with multiple errors |

## Out of scope

- Modifying the resource close logic itself
- Adding new configuration options for error thresholds
- Any other file modifications

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-151329_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-171831
- Related target files: scripts/agent/repl.py
