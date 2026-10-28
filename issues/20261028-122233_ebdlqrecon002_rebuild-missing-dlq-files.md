# Detect and rebuild missing DLQ files from SQLite

## Priority
Medium

## Summary
Give operators a deterministic way to detect dead-letter rows whose JSON file is missing and to rebuild the file from SQLite, and correct the recovery runbook, which tells operators to rebuild from the JSONL archive instead of the canonical store.

## Background
Source: `memo-issue.md` item 03, narrowed after re-verification against current source on 2026-10-28.

- DLQ promotion writes the file with `_atomic_write` and then sets `events.dlq_at` (`scripts/eventbus/dlq.py`). `Explicit in code`.
- The reverse window (file written, `dlq_at` not committed) is already repaired by the background sweep: `_shared_promote` selects events with `dlq_at IS NULL` that meet the promotion rule and rewrites the file atomically. `test_reconciliation_orphan_file` covers it. This part of the memo item is therefore not an open defect. `Confirmed by repository evidence`.
- `docs/24_eventbus/eventbus_03_dlq_operations.md` (section "DLQ Reconciliation", "Missing Files") tells the operator to rebuild a missing DLQ record from the JSONL archive. `eventbus_09_publish_durability.md` states SQLite is canonical and JSONL is best-effort and may be incomplete. `Explicit in docs`.
- The DLQ file content (`DlqEventRecord`) is `seq`, `event_id`, `topic`, `payload`, `producer`, `published_at`, `dlq_at` and the per-consumer failure count; every field is stored in SQLite (`events` and `consumer_delivery`), while the JSONL archive carries no `dlq_at` or failure count. `Explicit in code`.
- `test_reconciliation_missing_file` only asserts that the sweep does not fail when a promoted event's file is gone; nothing detects or repairs it, and the DLQ list endpoint reads SQLite only, so a missing file is silent. `Explicit in code`.
- Prior work: the archived `plans/done/20261028-093155_ebdurable003_define-publish-dlq-durability.md` (procedures pending) records the authority model (SQLite canonical, DLQ file derived), counts inline write failures and isolates sweep failures. It does not add missing-file detection or rebuild.

## Problem
A dead-letter row with no file stays invisible to operators, and the documented repair uses a source that can be incomplete and lacks `dlq_at` and the failure count, although SQLite holds every field.

## Reason for Change
No incident is cited. The runbook can lead an operator to rebuild from a lossy source, which is a documentation/code mismatch on a recovery procedure; severity is Medium. Nothing makes the change time-sensitive.

## Implementation Intent
Add one idempotent reconciliation operation that compares `events.dlq_at IS NOT NULL` rows with the DLQ directory and rebuilds a missing file from SQLite through the existing atomic-write path, reporting what it did. Make the check callable by an operator and safe to run next to the sweep. Then align the runbook with SQLite as the only rebuild source.

## Target Files or Areas
- `scripts/eventbus/dlq.py`
- `scripts/eventbus/dlq_repo.py` (a read helper for promoted rows, if needed)
- a supported entry point for the operator (a `tools/` script, an operator-role route, or a startup check; the choice is open)
- `tests/eventbus/test_eventbus_dlq.py`
- `docs/24_eventbus/eventbus_03_dlq_operations.md`

## Required Changes
- List promoted rows whose `{event_id}.json` is missing, and rebuild each from SQLite with the existing `_atomic_write`, preserving `event_id`, payload, lineage, `published_at`, `dlq_at` and the per-consumer failure count.
- Make the operation idempotent and safe under concurrent inline promotion and the sweep (the DB lock already serializes writers).
- Report counts (checked, rebuilt, failed) in a form an operator can read.
- Replace the JSONL-based "Missing Files" guidance with the SQLite-based procedure, and state that a corrupt or unreadable file is replaced the same way.

## Constraints
- Keep the DLQ file format and location unchanged.
- Do not delete or modify any file that has a matching promoted row; only create missing files.
- Do not add an outbox, a queue or a new persistent state.

## Acceptance Criteria
- A promoted row with a missing file is detected and its file is recreated with the same content a fresh promotion would write.
- Running the operation twice changes nothing the second time.
- A row without `dlq_at` is never turned into a file by this operation (the sweep owns promotion).
- The runbook names SQLite as the rebuild source and describes the operator command.

## Testing Expectations
- Unit tests: missing file rebuilt; existing file untouched; idempotent second run; per-consumer failure count preserved; write failure for one event does not stop the others.
- A test that runs the operation while the sweep runs (explicit synchronization, no sleeps).
- `uv run pytest tests/eventbus`, mypy and ruff; `tools/check_docs_consistency.py --domain eventbus` for the doc.

## Documentation Impact
Yes: replace the "Missing Files" guidance with the SQLite-based procedure and name the operator entry point (operational notes and failure behavior only; no code-level detail).

## Out of Scope
- Backfilling the JSONL archive.
- Changes to promotion, requeue or the NACK route.
- Backup and restore of `eventbus.sqlite`.

## Dependencies
- Coordinate with the archived `plans/done/20261028-093155_ebdurable003_define-publish-dlq-durability.md`: its pending procedures (`implementations/20261028-115345_01_scripts_eventbus_dlq.py.md`, `implementations/20261028-115345_03_tests_eventbus_test_eventbus_dlq.py.md`, `implementations/20261028-115345_06_docs_24_eventbus_eventbus_03_dlq_operations.md.md`) edit `scripts/eventbus/dlq.py`, `tests/eventbus/test_eventbus_dlq.py` and `docs/24_eventbus/eventbus_03_dlq_operations.md`. Implement after them or rebase.

## Unresolved Questions
- Which operator entry point is wanted: a `tools/` script, an operator-role route, or a startup check? `Needs confirmation` (owner decision).
- Should a startup check only report, or also rebuild? `Needs confirmation`.

## AI Implementation Instruction
Create missing files only; never touch an existing file or a row without `dlq_at`. Reuse `_atomic_write`; do not add a second writer. If the entry point choice is unclear, implement the library function and its tests first and stop and report the open question.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261028-122233
- **Related target files**: `scripts/eventbus/dlq.py`, `scripts/eventbus/dlq_repo.py`, `tests/eventbus/test_eventbus_dlq.py`, `docs/24_eventbus/eventbus_03_dlq_operations.md`
