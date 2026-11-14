# Recovery drill can abort without an artifact and reports an RTO that excludes the restore copy

## Priority
Medium

## Summary
`db.recovery_drill._drill_one_domain` promises to always write an audit artifact, but it handles only `FileNotFoundError` from the archive step. Its RTO measurement also starts after the restore copy, and the module carries an unused helper.

## Background
Found by an adversarial review of `scripts/db` at commit 0fe68d3 (Review finding F-009). Evidence label: `Explicit in code`, confidence High for the exception path and Medium for the metric interpretation.

## Problem
- `_archive_db_file` raises `RuntimeError` when `_verify_archive` fails and may raise `sqlite3.Error`. These propagate out of `_drill_one_domain` and `run_drill`: no artifact is written for that domain, and with `--domain all` the remaining domains are not drilled, contrary to the docstring ("always return its audit artifact").
- `started = time.time()` is taken after `shutil.copy2(recovery_point, isolated)`, and the timed block is only the verification. `rto_seconds` therefore excludes the file restore it names.
- `_last_archive` has no caller (only its definition exists under `scripts`).
- `run_drill` uses `print` in a library module; confirm it against the `rules/coding.md` print constraint.

## Reason for Change
The drill is the evidence that recovery works. A drill that crashes without a record, or under-reports its recovery time, weakens that evidence.

## Implementation Intent
Catch archive-stage failures per domain and persist a failed artifact, start the RTO clock before the restore copy, and remove or use the dead helper.

## Target Files or Areas
- `scripts/db/recovery_drill.py` (`_drill_one_domain`, `run_drill`, `_last_archive`)
- `tests/db/test_recovery_drill.py`

## Required Changes
- Catch `RuntimeError` and `sqlite3.Error` around `_archive_db_file`, record the error in the artifact, and continue with the next domain.
- Move `started` before the copy to the isolated path, or rename the metric to what it measures.
- Delete `_last_archive` if no consumer is planned.
- Add tests for an archive-verification failure and for the timing boundaries.

## Constraints
- The exit code contract (0 all pass, 1 any fail) stays.
- Artifact field names remain compatible for existing readers.

## Acceptance Criteria
- A failing archive verification yields a written artifact with a non-passing verdict and exit code 1.
- All requested domains are attempted.
- `rto_seconds` covers the copy plus verification, or the field is renamed and documented.

## Testing Expectations
Unit tests in `tests/db/test_recovery_drill.py` with a patched `_archive_db_file` raising each error type.

## Documentation Impact
Update the drill/RTO description if the metric definition changes.

## Out of Scope
- Retention of drill outputs (`issues/20261114-092857_dbreview008_artifact-retention-gaps.md`).

## Dependencies
N/A: none

## Unresolved Questions
- Is `rto_seconds` intentionally verification-only? Needs confirmation from the drill owner.

## AI Implementation Instruction
Follow `skills/python-implementation/SKILL.md`. Do not change artifact schema keys. English comments and logs.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261114-092858
- **Related target files**: scripts/db/recovery_drill.py, tests/db/test_recovery_drill.py
