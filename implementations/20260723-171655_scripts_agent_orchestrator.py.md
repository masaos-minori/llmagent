## Goal

Detect silent background task failures and alert operators with escalating severity based on consecutive failure count.

## Scope

**In:**
- `scripts/agent/orchestrator.py`: Add consecutive failure tracking and escalation logic to `_discard_and_log()`

**Out:**
- Modifying the background task lifecycle beyond error detection
- Adding new configuration options for failure thresholds
- Any other file modifications

## Assumptions

1. The `_discard_and_log()` callback is only invoked for first-turn background tasks (`_on_first_turn`).
2. Cancelled tasks should not count toward consecutive failure count — they are intentional cancellations.
3. A threshold constant (`BG_FAILURE_THRESHOLD`) should trigger FATAL escalation after N consecutive failures.
4. The counter should persist across turns but reset when a successful first-turn background task completes.

## Design decisions

- Convert `_discard_and_log` from a local closure to a method of the Orchestrator class to cleanly access `self._consecutive_bg_failures`.
- Reset the counter on successful task completion (not just cancellation), ensuring the counter tracks actual consecutive failures.
- Use a module-level constant for the failure threshold to allow easy tuning.

## Alternatives considered

- Keep `_discard_and_log` as a closure with `nonlocal`: would require wrapping the counter in a mutable container (e.g., `[0]`) to work correctly in Python closures.
- Add operator-visible REPL warning on first failure: would clutter the REPL output with maintenance warnings during normal operation.
- Send external notification on repeated failures: out of scope for this change; logging is sufficient for now.

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

1. Locate `Orchestrator.__init__()` and add `self._consecutive_bg_failures: int = 0`
2. Convert `_discard_and_log` from a local closure to an instance method
3. Define `BG_FAILURE_THRESHOLD` as a module-level constant
4. Update the callback registration in `_handle_turn_start()` to use the method reference

### Method

Convert existing closure to instance method; add new instance variable and module-level constant.

### Details

```python
# Module-level constant
BG_FAILURE_THRESHOLD: int = 5

# In __init__:
self._consecutive_bg_failures: int = 0

# Replace closure with method:
def _discard_and_log(self, task: asyncio.Task[Any]) -> None:
    exc = task.exception()
    if exc is not None:
        if isinstance(exc, asyncio.CancelledError):
            # Task was cancelled — do not log as error.
            self._consecutive_bg_failures = 0
        else:
            self._consecutive_bg_failures += 1
            if self._consecutive_bg_failures == 1:
                logger.warning("First background task failure: %s", exc)
            elif self._consecutive_bg_failures >= BG_FAILURE_THRESHOLD:
                logger.error("Consecutive background task failures (%d): %s",
                            self._consecutive_bg_failures, exc)
            else:
                logger.warning("Background task failure #%d: %s",
                              self._consecutive_bg_failures, exc)
    else:
        # Task completed successfully — reset counter
        self._consecutive_bg_failures = 0
    self._background_tasks.discard(task)

# In _handle_turn_start():
_task.add_done_callback(self._discard_and_log)
```

## Compatibility considerations

N/A — only affects error handling path; no API changes.

## Security considerations

N/A — no security impact; only improves operational visibility for background task failures.

## Rollback considerations

Simple revert of the consecutive failure tracking addition; no data migration or config changes required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/orchestrator.py | Lint | `ruff check scripts/agent/orchestrator.py` | 0 errors |
| scripts/agent/orchestrator.py | Type check | `mypy scripts/agent/orchestrator.py` | no new errors |
| scripts/agent/orchestrator.py | Architecture | `lint-imports` | 0 violations |
| scripts/agent/orchestrator.py | Tests | `pytest tests/test_agent/ -k orchestrator` | all pass |
| scripts/agent/orchestrator.py | Manual test | Break the memory backend, trigger multiple turns | Observe escalating log messages |

## Out of scope

- Modifying the background task lifecycle beyond error detection
- Adding new configuration options for failure thresholds
- Any other file modifications

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-150433_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-171655
- Related target files: scripts/agent/orchestrator.py
