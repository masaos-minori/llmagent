# Strengthen recovery drills and correct RPO/RTO reporting

## Priority
Medium

## Summary
Make recovery drills validate production-equivalent logical integrity of the restored RAG and session copies, and report backup duration, RPO, and RTO with distinct, correct definitions.

## Background
Verified against current source on 2026-11-04 (confirmed by repository evidence):

- `_verify_rag_session` in `scripts/db/recovery_drill.py` runs only `run_integrity_check` on the isolated copy; it does not call the RAG or session consistency verification, so FTS, vector, chunk, message, and memory relationships are not exercised.
- `_drill_one_domain` computes `rpo_window = time.time() - drill_start` around the archive step and stores it as `rpo_window_seconds`, which is the archive duration, not the age of the recovery point at the assumed failure time. `rto_seconds` is measured from a separate `started` timestamp.
- Drill fixtures are minimal (a required table such as `documents` or `sessions`), per the existing drill tests (`tests/db/test_recovery_drill.py`; fixture contents to be confirmed in planning).

## Problem
A logically damaged archive can pass a drill while `PRAGMA integrity_check` passes, and the mislabeled metric overstates recoverability.

## Reason for Change
Recoverability evidence is misleading today. Not time-sensitive beyond that.

## Implementation Intent
Turn the drill into evidence that a realistic restored copy is usable: run full RAG consistency and a read-only session consistency check against production-equivalent schemas, isolated from live databases, and emit correctly defined `backup_duration_seconds`, RPO, and RTO values.

## Target Files or Areas
- `scripts/db/recovery_drill.py`
- `tests/db/test_recovery_drill.py`, `tests/db/test_rag_consistency.py` (fixtures)

## Required Changes
- Run full RAG consistency verification on the restored copy and a read-only session consistency verification on the restored copy.
- Use fixtures with canonical FTS and vector structures; add negative fixtures for missing FTS rows, missing vectors, orphaned messages, and orphaned memories.
- Rename the archive elapsed measurement to `backup_duration_seconds` (note the artifact-field rename for existing consumers).
- Define RPO as recovery-point age at the assumed failure time and define exact RTO start and completion events.
- Keep and test the guarantee that live databases are not modified.

## Constraints
- Live databases must stay unchanged in success and failure.
- The session verification must not write (depends on the smoke-test issue).
- Artifact consumers of `rpo_window_seconds`: unknown; the rename is a contract change that must be stated.
- sqlite-vec may be unavailable in some environments.

## Acceptance Criteria
- A logically damaged RAG or session archive fails the drill even when `PRAGMA integrity_check` passes.
- Healthy production-equivalent fixtures pass, including sqlite-vec where available.
- The live database remains unchanged in success and failure cases.
- `backup_duration_seconds`, RPO, and RTO have separate documented definitions and values.
- Tests assert timestamp relationships, not only non-negative numbers.

## Testing Expectations
- Unit and integration tests with healthy and negative fixtures; a live-database checksum test.
- Run `uv run pytest tests/db/test_recovery_drill.py -q`, ruff, and mypy.

## Documentation Impact
Update the recovery drill section of the operations runbook and the design document with the metric definitions and the field rename.

## Out of Scope
- Changing the consistency checks and the recovery path themselves.

## Dependencies
- `issues/20261104-143443_ragverify001_complete-fail-closed-rag-consistency.md`: depends on it (the drill reuses the RAG verification).
- `issues/20261104-143443_sessmoke001_atomic-session-smoke-test.md`: depends on it for a read-only session verification.

## Unresolved Questions
- Recovery RPO and RTO objectives: unknown.
- sqlite-vec CI availability and loading method: unknown.
- Production-equivalent anonymized schema fixtures: unknown.
- Consumers of the drill artifact fields: unknown.

## AI Implementation Instruction
Do not invent RPO/RTO objectives; define the measurements only. Keep the drill isolated from live databases and add the failing negative-fixture tests before the change.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-143443
- **Related target files**: `scripts/db/recovery_drill.py`, `tests/db/test_recovery_drill.py`
