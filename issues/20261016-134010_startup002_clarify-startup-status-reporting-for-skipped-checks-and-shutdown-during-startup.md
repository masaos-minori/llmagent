# Clarify startup status reporting for skipped checks and shutdown-during-startup

## Priority
Low

## Summary
Two operator-visibility gaps in the agent startup reporting path: the readiness summary
under-reports the RAG consistency check (a skipped check reads as a generic "WARN"), and the
REPL prints "Startup failed" even when startup was interrupted by a user shutdown request
(`StartupInterrupted`). Make both signals accurate.

## Background
`ReadinessReporter.report_readiness()` prints a per-service summary. Readiness, tool
discovery, and (partly) security show OK/FAIL with fatal/warning/skipped counts. The RAG
line is:

```
RAG consistency: {'OK' if ok else 'WARN'} ({fatal} fatal, {warning} warnings)
```

It omits the skipped count. When the RAG check is skipped (timeout or any exception, see
`scripts/agent/startup_validation.py`), `ok` is false, so the line renders as "WARN" with
zero fatal and zero warnings and no indication that the check did not actually run.

Separately, `AgentREPL.run()` wraps `StartupOrchestrator.run()` and, on any exception,
writes `f"Startup failed: {e}"`. `StartupInterrupted` (raised when a SIGINT/SIGTERM shutdown
request fires during startup) is a normal, expected exit, not a failure, but it flows through
the same `except Exception` branch and is reported identically.

## Problem
An operator scanning the startup banner cannot tell whether "RAG consistency: WARN" means the
check found problems or was never completed. And a clean user-initiated shutdown during
startup is displayed as a failure, which is misleading in logs and interactive sessions.

## Reason for Change
These are low-risk reporting-accuracy improvements. They cost little to fix and remove two
sources of operator confusion during startup triage. Neither changes startup behavior or the
fail-fast security gate.

## Implementation Intent
- In `ReadinessReporter.report_readiness()`, include the RAG skipped count (or a
  dedicated "skipped" label) so a skipped RAG check is not rendered as a bare "WARN".
- In `AgentREPL.run()`, distinguish `StartupInterrupted` from other startup failures when
  composing the user-facing message, so an intentional shutdown is not labeled "Startup
  failed".

## Target Files or Areas
- `scripts/agent/startup_reporter.py`
- `scripts/agent/repl.py`

## Required Changes
- Add the RAG `SKIPPED` count (or an explicit "skipped" token) to the RAG consistency line
  so a skipped check is distinguishable from a warning-bearing check.
- In the `repl.py` startup exception handler, print a shutdown/interrupt-appropriate message
  for `StartupInterrupted` instead of the generic "Startup failed: ..." text. Keep the
  re-raise and the `finally` resource cleanup unchanged.

## Constraints
- Do not change what is reported for the other three checks or their counts.
- Do not change startup control flow, rollback, or resource shutdown.
- Keep log/output text English per `rules/coding.md`.

## Acceptance Criteria
- A skipped RAG check renders with a visible skipped indicator, not a bare "WARN" with zero
  counts.
- A `StartupInterrupted` during startup does not print "Startup failed"; an actual failure
  still does.
- Existing startup/reporter tests still pass.

## Testing Expectations
- Add/extend `tests/agent/test_startup_reporter.py` to assert the RAG skipped count appears
  in the reported lines.
- Add a test asserting the `repl.py` path emits a non-"Startup failed" message for
  `StartupInterrupted`.
- Run `uv run pytest tests/agent/test_startup_reporter.py`.
- Run `uv run ruff check` and `uv run mypy --no-namespace-packages` on the touched files.

## Documentation Impact
None required.

## Out of Scope
- Any change to the validation pipeline itself or the RAG classification behavior.
- Refactoring the readiness summary layout beyond adding the skipped indicator.
- Changing signal-handling semantics.

## Dependencies
- Depends on `issues/20261016-133921_startup001_classify-rag-consistency-startup-exceptions-instead-of-skipping-all.md`
  only insofar as that issue may add a RAG category; this issue surfaces the skipped count
  independently and can be implemented without it.

## Unresolved Questions
- Should the RAG skipped indicator reuse the existing `{skipped}` count column pattern used
  by the readiness and tool-discovery lines, or a distinct "skipped" token?

## AI Implementation Instruction
Keep changes cosmetic to the reported strings only; do not alter control flow, counts for
other checks, or shutdown behavior. For the `repl.py` change, branch on `StartupInterrupted`
before the generic `except Exception` handler and preserve the re-raise and `finally` block.
Stay within `startup_reporter.py` and `repl.py` plus their tests.

## Traceability
- **Workflow phase**: python-code review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261016-134010
- **Related target files**: scripts/agent/startup_reporter.py, scripts/agent/repl.py
