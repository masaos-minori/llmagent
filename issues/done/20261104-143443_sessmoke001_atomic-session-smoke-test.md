# Make session consistency smoke tests atomic and concurrency-safe

## Priority
Medium

## Summary
Ensure the session write smoke test cannot leave a diagnostic row in the session database or interfere with a concurrent run.

## Background
Verified against current source on 2026-11-04 (confirmed by repository evidence): `_check_write_smoke_test` in `scripts/db/session_consistency.py` inserts a `session_diagnostics` row with the fixed kind `'smoke'`, calls `db.commit()`, looks the row up with `WHERE kind='smoke' ORDER BY id DESC LIMIT 1`, deletes it by id, and commits again.

## Problem
A crash or exception after the first commit leaves a row in the session database. The lookup by the shared kind can pick another concurrent run's row, so the delete can remove the wrong row. Existing tests cover normal cleanup but not interruption or concurrency.

## Reason for Change
The diagnostic writes durable application data. Timing: not time-sensitive; severity is limited to leftover diagnostic rows and cross-run interference.

## Implementation Intent
Keep the diagnostic useful without changing durable data: prove write/read behavior inside an isolated transaction or SAVEPOINT that is always rolled back, and identify the row by `lastrowid` or a token owned by that run instead of a shared marker.

## Target Files or Areas
- `scripts/db/session_consistency.py`
- Recovery verification that calls it: `scripts/db/recovery_verification.py` (`_verify_session_logic`)
- `tests/db/test_session_consistency.py`

## Required Changes
- Execute the smoke write under a SAVEPOINT and always roll it back.
- Identify the inserted row with `lastrowid` or a run-unique token.
- Remove cleanup logic that depends on the fixed `'smoke'` marker.
- Keep recovery verification read-only where the recovery contract requires it.
- Add interruption-after-insert and concurrent-run tests.

## Constraints
- The test must still prove the session write/read behavior.
- Whether production diagnostics are permitted to write: unknown; do not extend writes.
- Preserve the public function signatures.

## Acceptance Criteria
- No smoke row remains after success, handled failure, or injected interruption.
- Two concurrent smoke tests cannot read or delete each other's rows.
- The test still proves the required write/read behavior.
- Recovery verification commits no diagnostic rows.

## Testing Expectations
- Unit tests for success, failure, and injected interruption; a concurrency test with two connections in WAL mode.
- Run `uv run pytest tests/db/test_session_consistency.py -q`, ruff, and mypy.

## Documentation Impact
Update the session consistency design note only if the write/read-only contract changes (failure behavior, operational notes).

## Out of Scope
- Other session consistency checks and the orphan detection logic.

## Dependencies
- `issues/20261104-143443_sqliterec001_atomic-fail-closed-sqlite-recovery.md`: shares the read-only verification contract.
- `issues/20261104-143443_drillmetrics001_strengthen-recovery-drills-and-rpo-rto.md`: the drill needs a read-only session verification.

## Unresolved Questions
- Session consistency operational requirements and the concurrent execution model: unknown.
- Whether production diagnostics may write at all: unknown.

## AI Implementation Instruction
Use a SAVEPOINT that is always rolled back; never commit the smoke row. Do not widen the scope to other checks.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-143443
- **Related target files**: `scripts/db/session_consistency.py`, `scripts/db/recovery_verification.py`, `tests/db/test_session_consistency.py`
