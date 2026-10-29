# Decide and implement an SQLite-backed outbox for EventBus DLQ file generation

## Priority
Medium

## Summary
Decide whether EventBus dead-letter file generation should move from synchronous, lock-held file writes to an SQLite outbox processed by a retryable worker, and implement it if so: `events.dlq_at` and an outbox request commit in one transaction, files are generated from committed outbox rows with persisted failure and retry metadata, and reconciliation also reports orphaned and mismatched files.

## Background
Source: `memo-issue.md` item H-03 (original task H-04), re-verified against current source on 2026-10-29. The memo rates it High and describes several defects; most of them are already handled, so this issue is narrowed to what remains.

Already handled (`Explicit in code`):
- Write order: `scripts/eventbus/dlq.py` writes the file first (`_atomic_write`, lines 214 onward) and only then sets `events.dlq_at` and commits (`_shared_promote_single` lines 156-166 and `_shared_promote` lines 121-127). A committed DLQ row therefore implies the file existed at commit time; the reachable crash outcome is an orphan file with the event still live, which the sweep repairs. If the file write fails, "the DB row is not updated and the event remains live" (`promote_single` docstring).
- NACK independence: `scripts/eventbus/ack_route.py:207-218` catches `OSError` from inline promotion, logs it, and defers to the sweep, so a NACK still succeeds.
- Per-event isolation: the sweep (`_shared_promote`) catches `OSError` for one event, increments `eventbus_dlq_file_write_failure_total`, and continues with the next event (`sweep_orphans` docstring).
- Authority model: SQLite `events.dlq_at` is authoritative and the file is derived data (`docs/24_eventbus/eventbus_03_dlq_operations.md:120`, `docs/24_eventbus/eventbus_09_publish_durability.md:23`, `Documentation only`).
- Missing-file repair is planned and its procedures exist but are not implemented: `plans/done/20261028-231610_ebdlqrecon002_rebuild-missing-dlq-files.md` with `implementations/20261029-085348_01_scripts_eventbus_dlq.py.md`, `_02_tests_eventbus_test_eventbus_dlq.py.md`, `_03_docs_24_eventbus_eventbus_03_dlq_operations.md.md`.
- Shutdown ordering was settled by `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md`.

Still true:
- No outbox table or concept exists in `scripts/eventbus/` or `schema.sql` (`Explicit by absence search`).
- Inline promotion runs inside the database-lock critical section (`_nack_and_promote` is executed through `run_with_db_lock`, `ack_route.py:221`), so a slow file write holds the shared database lock (`Explicit in code`).
- A failed file write is recorded only as a counter and a log line; there is no persisted failure detail or retry state (`Explicit in code`).

## Problem
Two residual weaknesses remain: DLQ file I/O happens while the shared database lock is held, and artifact-generation failures leave no durable record beyond a counter. Orphan and content-mismatch files are not reported by any planned reconciliation (`ebdlqrecon002` rebuilds missing files only). Whether these justify an outbox redesign is not established by the evidence above.

## Reason for Change
An outbox would take file I/O out of the lock-held transaction and make artifact generation observable and retryable. Priority is Medium (not the memo's High) because the canonical-data risks named in the memo are already prevented by the write order, the NACK handling, and the sweep; what remains concerns lock hold time and observability. It is not time-sensitive, and it should be re-evaluated after `ebdlqrecon002` is implemented.

## Implementation Intent
First decide, with the owner and after the `ebdlqrecon002` reconciliation exists, whether an outbox is warranted; a lighter alternative (moving file writes out of the lock, adding persisted failure metadata to the existing sweep) may satisfy the residual weaknesses. If the outbox is chosen: keep SQLite canonical and the DLQ file derived, add an outbox table written in the same transaction as `events.dlq_at`, generate files from committed rows in a background worker that records completion idempotently with failure and retry metadata, and extend reconciliation to report orphan and mismatched files. Schema changes should use the migration framework tracked in `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`.

## Target Files or Areas
- `scripts/eventbus/dlq.py`, `scripts/eventbus/dlq_repo.py`
- `scripts/eventbus/ack_route.py`, `scripts/eventbus/app.py`, `scripts/eventbus/route_helpers.py`
- `scripts/eventbus/schema.sql`
- EventBus DLQ and shutdown tests under `tests/eventbus/` (`test_eventbus_dlq.py`, `test_eventbus_shutdown.py`; others to be confirmed)
- `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_09_publish_durability.md`

## Required Changes
- Record the decision (outbox versus lighter alternative) and its rationale in the issue's resolution or the resulting Plan.
- If the outbox is chosen: add the outbox table and commit `events.dlq_at` with the outbox request in one transaction.
- Generate files from committed outbox rows in a retryable background worker; record completion idempotently and persist failure details and retry metadata.
- Keep per-event isolation and keep NACK success independent of file creation (preserve current behavior).
- Extend reconciliation to report orphaned files, interrupted temporary files, and content mismatches (missing files are covered by `ebdlqrecon002`).
- Define shutdown behavior so an in-flight worker cannot use a closed shared connection.
- Add fault-injection tests for each crash point and file-system failure mode, and update the EventBus operations and DLQ documents.

## Constraints
- Preserve the existing requeue and archive behavior and the DLQ endpoint contracts.
- Keep the shutdown sequence from `ebshutdown002` (one lock-guarded close of the shared connection).
- Fail closed: a file-system failure must be reported, never hidden as success.
- The file stays derived data; do not create a second source of truth.

## Acceptance Criteria
- Every committed DLQ state can regenerate its file repeatedly without duplicate canonical state.
- A file-system failure does not undo or misreport a committed NACK or DLQ transition (existing behavior is preserved).
- Outbox processing resumes safely after a process restart, and one failed artifact does not block unrelated artifacts.
- Artifact-generation failures leave a persisted record with retry state.
- Reconciliation repairs missing files and reports orphaned or conflicting files.
- Shutdown waits for or safely cancels in-flight outbox work before the database closes.
- All crash-window tests pass.

## Testing Expectations
- Fault-injection tests for: crash after the SQLite commit and before file creation, crash during the temporary-file write, a file-system error for one event among several, restart with pending outbox rows, and shutdown with an in-flight worker.
- Regression tests in `tests/eventbus/test_eventbus_dlq.py` and `tests/eventbus/test_eventbus_shutdown.py`.
- `uv run pytest tests/eventbus`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run python tools/check_db_separation.py`, `uv run python tools/generate_reference_table.py --check`.

## Documentation Impact
Yes, if the outbox is built. The DLQ operations and publish-durability documents must state that SQLite is the recovery source, how artifact generation is retried, and the failure behavior; document operational behavior and failure semantics only (`skills/DESIGN.md` Docs content policy).

## Out of Scope
- Changing the DLQ promotion rule (ADR-006 INV-13) or the requeue transaction.
- JSONL event archive reconciliation (a separate derived artifact; see `docs/24_eventbus/eventbus_09_publish_durability.md`).
- Unrelated refactoring or formatting-only changes.

## Dependencies
- Depends on the `ebdlqrecon002` reconciliation landing first (`plans/done/20261028-231610_ebdlqrecon002_rebuild-missing-dlq-files.md`; procedures `implementations/20261029-085348_01_scripts_eventbus_dlq.py.md`, `implementations/20261029-085348_02_tests_eventbus_test_eventbus_dlq.py.md`, `implementations/20261029-085348_03_docs_24_eventbus_eventbus_03_dlq_operations.md.md`). Re-verify this issue against current source after it is implemented, because it may remove part of this issue.
- Depends on `issues/20261029-104500_dbmig001_forward-only-db-migrations.md` for the schema change (recommended order: migrations first).
- Coordinate with `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md`, which also edits `scripts/eventbus/dlq.py` and `tests/eventbus/test_eventbus_dlq.py` (audit arguments and assertions); different regions, land the audit plan first or rebase.

## Unresolved Questions
- `Needs confirmation`: whether the residual weaknesses justify an outbox at all, or the lighter alternative suffices (owner decision after `ebdlqrecon002`); if neither is wanted, close this issue as not needed.
- `Needs confirmation`: where the DLQ background worker lives today (the sweep in `scripts/eventbus/app.py` versus a separate task); the memo refers to a "DLQ worker implementation" without a path.
- `Needs confirmation`: whether the outbox should also cover requeue and archive file operations, and the retry policy (attempt limit, backoff) and the operator surface for permanently failed artifacts.

## AI Implementation Instruction
- Read `scripts/eventbus/dlq.py`, `scripts/eventbus/ack_route.py`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, and the `ebdlqrecon002` procedures before editing; do not duplicate their reconciliation.
- Do not start implementing until the outbox-versus-lighter-alternative decision is recorded; stop and report instead of choosing.
- Keep changes confined to the EventBus DLQ path with its tests and docs; do not change the promotion rule or the DLQ endpoints.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-104501
- **Related target files**: `scripts/eventbus/dlq.py`, `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/app.py`, `scripts/eventbus/route_helpers.py`, `scripts/eventbus/schema.sql`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_09_publish_durability.md`
