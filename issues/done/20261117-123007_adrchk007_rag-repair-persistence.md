# Persist RAG maintenance repairs and fix recovery result mapping

## Priority
High

## Summary
`RagMaintenanceService.rebuild_vec()` and `reconcile_url()` write under `write_mode=True` but do not call `commit()`, and `recover()` reports VACUUM failures as integrity failures. Make repairs persist and report the integrity state correctly.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H07`; merged from ADRCHK-H08, L16 (review finding N35 and round 4 Low findings)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
In `scripts/agent/services/rag_maintenance_service.py`, `rebuild_vec` and `reconcile_url` contain no `commit()` call (`Explicit in code`, confirmed by `rg`). Whether `SQLiteHelper.open(write_mode=True)` commits on exit is `Needs confirmation`; if it does, the repairs persist and the commit tasks close.

Re-verified on 2026-11-18 against current source (adversarial pass; labels follow `skills/DESIGN.md` Evidence labels).
- Confirmed (`Explicit in code`): neither `rebuild_vec` nor `reconcile_url` calls `commit()`. `SQLiteHelper.open(write_mode=True)` opens a default `sqlite3` connection and `__exit__` calls `close()`, which does not commit, so an uncommitted write is discarded at exit. `rebuild_fts` commits explicitly and has no explicit rollback: a failure rolls back implicitly when the connection closes.
- Corrected (`Verified by test`, reproduced in a scratch database with the canonical table shapes): both repairs fail before they reach the missing commit. `rebuild_vec` selects `chunks.embedding`, a column the canonical `chunks` DDL (`scripts/db/schema_sql.py`) does not have; embeddings exist only in the `chunks_vec` vec0 table (`scripts/rag/ingestion/transaction_commit.py`), so the call raises `OperationalError: no such column: embedding` and the uncommitted `DELETE` is rolled back. `reconcile_url` reads rows by column name on a connection opened without `row_factory=True`, so it raises `TypeError` once the URL exists.
- Corrected: the existing tests in `tests/agent/services/test_rag_index_integrity.py` replace `SQLiteHelper` with a fake whose rows are `sqlite3.Row` and use a stand-in `chunks` table with an `embedding` column, so they pass and hide both defects. Acceptance Criteria 1 and 2 assume chunks carry embeddings; adding `commit()` alone cannot satisfy them.
- Corrected: `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` describes `rebuild_vec` for orphan vector rows as removing `chunks_vec` rows that have no matching `chunks` row, while ADR-005 Decision 9 and the ADR-008 `derived-data-rebuild` entry describe a rebuild from source. The vector rows cannot be regenerated from `chunks`.
- Corrected: "can lead to an unneeded restore" is overstated. `recover_corruption` decides on a restore from the integrity condition (corruption only) before the result is mapped; a VACUUM failure on a healthy database returns `success=False` with `action="vacuum_failed"`, so only the reported `integrity_ok` is wrong. `RagMaintenanceService.recover()` has no caller in `scripts/` and no test; the same mapping exists in `DbMaintenanceService.recover_session` (not a target file).
- Confirmed (`Explicit in code`): the `SQLiteHelper` class docstring says the pragmas apply to every connection, while a read-only connection gets only `busy_timeout`.
- Confirmed: `tests/agent/services/` has no `test_rag_maintenance_service.py`; `rebuild_vec` and `reconcile_url` are covered only in `test_rag_index_integrity.py`. `reconcile_url` has no caller in `scripts/`; `/session rag-rebuild-vec` calls `rebuild_vec`.

## Reason for Change
- Repair writes are discarded at close: `rebuild_fts()` commits, but the other two do not, and `SQLiteHelper.close()` closes without committing, so implicit transactions roll back (the two repairs also fail earlier on the canonical schema, see Problem).
- The adopted repair would not work: orphan-vector findings use `rebuild_vec` as the repair action, so operators would see a success count while the index stays inconsistent.
- The result mapping hides the real state: `recover()` maps `integrity_ok` to `result.success`, so a VACUUM failure on a healthy database is reported as an integrity failure.
- The `SQLiteHelper` class docstring says WAL pragmas apply to every connection, but read-only connections are excluded, and that exclusion is why an earlier deviation was resolved.

## Implementation Intent
- Every maintenance write is atomic and persists, or is rolled back completely.
- The recovery result reports the integrity state separately from secondary steps.
- The helper documentation describes the real pragma behavior.

## Target Files or Areas
- `scripts/agent/services/rag_maintenance_service.py`
- `scripts/db/helper.py`
- `tests/agent/services/`
- `tests/db/`

## Required Changes
- Confirm that `SQLiteHelper.open(write_mode=True)` does not commit on exit; if it does, close the commit tasks and attach the evidence.
- Write persistence tests that reopen the database after each call; they must fail first.
- Add `db.commit()` at the end of both methods, with a rollback on failure as in `rebuild_fts`.
- Set `integrity_ok` from the integrity check result only.
- Fix the `SQLiteHelper` docstring.

## Constraints
- Write the failing tests first, then fix the code.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- After `rebuild_vec()`, a new connection sees one `chunks_vec` row for each chunk with an embedding.
- After `reconcile_url(url)`, a new connection sees the rebuilt FTS and vec rows.
- A VACUUM failure on a healthy database gives `integrity_ok=True` (test).

## Testing Expectations
Persistence and recovery tests under `tests/agent/services/` and `tests/db/` that reopen the database; run the full validation sequence. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Not required beyond the `SQLiteHelper` docstring correction.

## Out of Scope
- Choosing the RAG failure policy.
- Changing repair actions in the consistency check messages.

## Dependencies
- `issues/20261117-123006_adrchk006_rag-failure-policy.md` relies on `rebuild_vec` persisting before its repair actions are corrected (soft dependency).

## Unresolved Questions
- Test location: persistence tests go in a new file under `tests/agent/services/`; the existing `test_rag_index_integrity.py` needs its fake aligned with the real helper.
- The `rebuild_vec` contract on the canonical schema (orphan removal versus a rebuild from source) is a maintainer decision; ADR-005 Decision 9 and the ADR-008 `derived-data-rebuild` wording say "rebuild", and an ADR wording change needs an approval record.
- `DbMaintenanceService.recover_session` maps `integrity_ok` the same way and is outside the Target Files.

## AI Implementation Instruction
- Write the failing tests first, then fix the code.
- Do not touch the rebuild_fts behavior.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123007
- **Related target files**: `scripts/agent/services/rag_maintenance_service.py`; `scripts/db/helper.py`; `tests/agent/services/`; `tests/db/`
