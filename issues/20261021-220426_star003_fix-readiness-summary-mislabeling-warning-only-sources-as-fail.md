# Fix readiness summary mislabeling warning-only sources as FAIL

## Priority
Low

## Summary
`ReadinessReporter.report_readiness()` (`scripts/agent/startup_reporter.py`) labels a validation source as `FAIL` whenever it has zero `OK` outcomes, even when the source produced only `WARNING` outcomes and no `FATAL`. A source with warnings but no OK is therefore shown as failed, which overstates the problem. Make the summary reflect warnings correctly and use a single consistent status word across all three sources.

## Background
`report_readiness()` builds three summary lines, one per source (`readiness`, `mcp_tool_discovery`, `rag_consistency`), using `_count_by_status()`:
```python
f"Service readiness: {'OK' if mcp_counts['OK'] else 'FAIL'} ({mcp_counts['FATAL']} fatal, {mcp_counts['WARNING']} warnings, {mcp_counts['SKIPPED']} skipped)"
```
In `StartupValidationPipeline.check_services()` (`scripts/agent/startup_validation.py`), `pipeline.add_ok("readiness")` is called only when `result.has_issues` is False. When the readiness probe emits warnings, `has_issues` is True, so no `OK` outcome is recorded and `mcp_counts['OK']` is 0. The summary line then prints `FAIL` despite there being no fatal error. The RAG line uses a different word — `'OK' if rag_counts['OK'] else 'WARN'` — so the three lines are inconsistent in their vocabulary.

## Problem
The readiness summary is operator-facing output printed at every startup. Reporting `FAIL` for a source that only has warnings misleads anyone scanning the summary into thinking a service is down when it is merely degraded/warning. The inconsistent `FAIL` vs `WARN` wording across the three lines also makes parsing the summary unreliable.

## Reason for Change
The summary is derived from the same `outcomes` the pipeline already classified, so it can express the true state (OK / WARNING / FATAL / SKIPPED) instead of a binary OK/FAIL. Correct reporting matters for startup observability and for anyone alerting on the summary text.

## Implementation Intent
- Derive the status word from the source's own outcomes rather than from "any OK": print `FATAL` if any `FATAL` exists, else `WARNING` if any `WARNING` exists, else `SKIPPED` if all are `SKIPPED`, else `OK`.
- Use one consistent status word across all three summary lines.
- Keep the parenthetical fatal/warning/skipped counts unchanged.

## Target Files or Areas
- `scripts/agent/startup_reporter.py` (`report_readiness()` and optionally `_count_by_status()`)

## Required Changes
- Replace the `{'OK' if X['OK'] else 'FAIL'}` expression with a status computed from the counts (FATAL > WARNING > SKIPPED > OK ordering).
- Make the RAG line use the same status word as the other two lines.
- No change to the numeric counts appended in parentheses.

## Constraints
- Preserve the exact overall line format and the parenthetical counts so logs/tests that match them are not broken.
- Do not change the pipeline classification in `startup_validation.py`; only the display.

## Acceptance Criteria
- A source with only `WARNING` outcomes reports `WARNING` (not `FAIL`) in the summary.
- All three summary lines use the same status vocabulary.
- A source with a `FATAL` still reports `FATAL`.

## Testing Expectations
- Unit test: build a `StartupValidationResult` with only warnings for one source and assert the printed summary line contains the warning status, not FAIL.
- Existing reporter tests pass.
- `uv run ruff check`, `uv run mypy`, `uv run bandit` on edited files.

## Documentation Impact
None required.

## Out of Scope
- Any change to how the pipeline classifies OK/FATAL/WARNING/SKIPPED.
- Changes to `display_pipeline_results()`.

## Dependencies
- N/A: none

## Unresolved Questions
- Whether existing log-based tests assert the literal `FAIL` token for warning-only sources; if so, update those assertions in the same change.

## AI Implementation Instruction
- Change only the status-word computation in `report_readiness()`; keep counts and line structure.
- Grep tests for the literal summary tokens before editing to avoid breaking string-matching assertions.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-220426
- **Related target files**: `scripts/agent/startup_reporter.py`
