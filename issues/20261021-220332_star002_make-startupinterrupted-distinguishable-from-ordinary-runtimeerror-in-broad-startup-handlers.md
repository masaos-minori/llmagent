# Make StartupInterrupted distinguishable from ordinary RuntimeError in broad startup handlers

## Priority
Low

## Summary
`StartupInterrupted` is declared as a subclass of `RuntimeError`, so broad `except RuntimeError` / `except Exception` handlers in the startup path can catch a shutdown-request signal and treat it as an ordinary startup failure. Make the control-flow exception distinguishable (e.g. inherit from `BaseException` instead of `RuntimeError`) so shutdown requests are never retried or misclassified.

## Background
`StartupInterrupted` is defined in `scripts/agent/startup.py`:
```python
class StartupInterrupted(RuntimeError):
    """Raised when a SIGINT/SIGTERM shutdown request interrupts the startup sequence."""
```
It is raised by `McpServerStarter` when a shutdown event fires during MCP subprocess startup, stagger delays, or health checks, and by `retry_once_with_delay` (`scripts/agent/shared/retry_helper.py`) when shutdown fires during a retry delay. `AgentREPL.run()` (`scripts/agent/repl.py`) has an explicit `except StartupInterrupted` branch that treats a startup-time shutdown as non-fatal.

## Problem
Because `StartupInterrupted` is a `RuntimeError`, handlers that intend to catch ordinary startup errors also catch shutdown signals. In `McpServerStarter.start_servers()`, the first-attempt handler is `except (OSError, RuntimeError, TimeoutError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError) as e:`. If `_start_http_subprocess_once()` propagates a `StartupInterrupted` from deep inside the lifecycle start, this clause matches it, routes it through `retry_once_with_delay()`, and performs one extra retry delay before the shutdown signal surfaces. The end result still raises `StartupInterrupted`, but only after an unnecessary retry window, and the coupling makes the intent invisible to readers of any broad handler.

## Reason for Change
A shutdown-request exception is control flow, not a failure. Encoding it as `RuntimeError` lets generic error handlers intercept it, which is fragile: any new broad `except RuntimeError` added to the startup path can silently swallow or delay a shutdown request. This is a Fail-Closed / graceful-shutdown correctness concern even though the current exit path happens to still raise.

## Implementation Intent
- Change `StartupInterrupted` to inherit from `BaseException` instead of `RuntimeError`, so it is not matched by `except Exception` or `except RuntimeError` clauses.
- Audit every broad handler in the startup path (`startup.py`, `startup_mcp_starter.py`, `shared/retry_helper.py`, `startup_validation.py`, `resource_shutdown_coordinator.py`) and confirm the shutdown signal still reaches `AgentREPL.run()`'s `except StartupInterrupted` branch without an intervening retry or swallow.
- Do not change the message format or the public string repr used in logs/warnings.

## Target Files or Areas
- `scripts/agent/startup.py` (`StartupInterrupted` definition and its `except` handling)
- `scripts/agent/startup_mcp_starter.py` (the first-attempt exception tuple)
- `scripts/agent/shared/retry_helper.py` (where `StartupInterrupted` is raised)
- `scripts/agent/repl.py` (`except StartupInterrupted` branch)

## Required Changes
- Rebase `StartupInterrupted` onto `BaseException`.
- Remove `RuntimeError` from the first-attempt catch tuple in `McpServerStarter.start_servers()` where it now over-matches, if doing so keeps the intended error handling.
- Verify no handler relies on catching `StartupInterrupted` as a `RuntimeError` (e.g. `isinstance` checks or `except RuntimeError`).

## Constraints
- Must remain catchable explicitly via `except StartupInterrupted`.
- Must not change shutdown timing semantics for the legitimate interrupt paths.
- Python 3.13 only; `asyncio.CancelledError` already derives from `BaseException`, so aligning `StartupInterrupted` is consistent.

## Acceptance Criteria
- `StartupInterrupted` is not a subclass of `RuntimeError`.
- A `StartupInterrupted` raised inside `_start_http_subprocess_once()` is NOT caught by the first-attempt tuple in `start_servers()` and does not trigger a retry delay.
- `AgentREPL.run()` still receives `StartupInterrupted` and prints the non-fatal interrupted warning.

## Testing Expectations
- Unit test: raise `StartupInterrupted` from a mocked subprocess start and assert `McpServerStarter.start_servers()` propagates it without calling the retry helper.
- Existing startup/shutdown tests still pass.
- `uv run ruff check`, `uv run mypy`, `uv run bandit` on edited files.

## Documentation Impact
None required unless a design note describes `StartupInterrupted` as a `RuntimeError`; update that note if present.

## Out of Scope
- Any change to signal registration, the shutdown event, or graceful-shutdown timing.
- Refactoring other startup exceptions.

## Dependencies
- N/A: none

## Unresolved Questions
- Whether any external caller or test asserts `isinstance(exc, RuntimeError)` for a startup interruption; if so, coordinate that change with this one.

## AI Implementation Instruction
- Only change the base class of `StartupInterrupted` and remove over-matching `RuntimeError` from the specific first-attempt tuple; do not rename the class or change messages.
- Grep the whole `scripts/` tree for `except RuntimeError` and `isinstance.*StartupInterrupted`/`StartupInterrupted` before and after to confirm no reliance on the old base class.
- Do not alter retry-helper behavior for genuine failures.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-220332
- **Related target files**: `scripts/agent/startup.py`, `scripts/agent/startup_mcp_starter.py`, `scripts/agent/shared/retry_helper.py`, `scripts/agent/repl.py`
