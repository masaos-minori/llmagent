# Make turn persistence strict, count-verified, and recovery-aware

## Priority
Medium

## Summary
Reject silently skipped session messages, verify inserted counts, and surface compensation failure as a degraded session state.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 10). Related archived work: `issues/done/20261115-081702_persis001_persistence-compensation-sqlite-only.md`, `plans/done/20261027-070403_turn001_atomic-turn-persistence.md`.

Evidence (`Explicit in code`, by `rg`): `scripts/agent/turn_persistence.py` logs a compensation failure ("Turn compensation failed after persistence error") and raises the original error (around lines 218-225), so the caller cannot tell a clean rollback from a failed one. The repository skip-and-warn behavior and the missing inserted-count return are from the backlog and `Needs confirmation`.

## Problem
The message repository can warn and skip invalid roles or a missing session id without raising, while turn persistence treats the phase group as committed; a failed compensation is indistinguishable from a clean rollback.

## Reason for Change
These gaps undermine the all-or-nothing persistence contract despite transaction support.

## Implementation Intent
Validate each phase group before writing, require inserted count to equal expected count, report compensation status explicitly, and pause the session when compensation fails until recovery or a health check succeeds.

## Target Files or Areas
- `scripts/agent/turn_persistence.py`, `session_message_repo.py`, `turn_result.py`
- Session health and recovery paths; tests under `tests/agent/`

## Required Changes
- Require strict repository mode for turn persistence; reject the whole phase group on any invalid role; treat a missing session id as an error; return the inserted-row count and compare it with the expected count; never mark a zero-row write committed.
- Add compensation status `completed`, `failed`, or `not_needed` to persistence errors and the turn result; mark the session degraded or paused when compensation fails; require health or recovery before the next turn; use safe public errors without SQLite details.

## Constraints
- Compensation behavior from the archived persis001 work stays intact.
- Session degraded state integrates with the generation model of `issues/20261119-145300_cliplc002_session-transition-generation.md`.

## Acceptance Criteria
- [ ] Invalid or incomplete phase groups roll back fully; persisted count equals expected count.
- [ ] The caller can distinguish compensation success and failure.
- [ ] A degraded session cannot silently continue.

## Testing Expectations
- Invalid role mixed with valid messages; missing session id; inserted-count mismatch; compensation success and failure fault injection.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Compensation statuses and the degraded-session behavior.

## Out of Scope
- Session transitions and generations (`issues/20261119-145300_cliplc002_session-transition-generation.md`).

## Dependencies
- Depends on `issues/20261119-145300_cliplc002_session-transition-generation.md`.

## Unresolved Questions
- `不明`: how recovery or a health check clears the degraded state (command and criteria).

## AI Implementation Instruction
Write the invalid-role and compensation-failure fault-injection tests first. Keep changes within turn persistence and the message repository. Stop and report if strict mode changes behavior for other repository callers.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145308
- **Related target files**: `scripts/agent/turn_persistence.py`, `scripts/agent/session_message_repo.py`, `scripts/agent/turn_result.py`
