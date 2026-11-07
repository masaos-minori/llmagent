## Goal

- Replace the ledger-state audit in `scripts/db/recovery_drill.py` with a current-shape audit that flags legacy marker tables as audited findings (REQ-006: preserve rotation, archive validation, and supported recovery while dropping ledger assumptions).

## Scope
**Release unit**: current-schema-only-cutover

- Audit-logic change in this file only; its test coverage (`tests/db/test_recovery_drill.py`) is carried as a companion (row 24 is named exactly by this row's Related Tests).

## Assumptions

- Rotation (`scripts/db/rotation.py`) and backup/recovery validation (`scripts/db/recovery.py`) are verified ledger-free and stay untouched (Plan Reference Files).
- `scripts/shared/eventbus_schema_fingerprint.assert_matches` (import at line 30 region) stays in use — only the `shared.db_migrations` import (line 29) is removed with sibling document 01.

## Design decisions

- Legacy-marker audit: presence of `schema_migrations` or `workflow_schema_version` in a domain database → audited finding (drill fails, artifact still written, live DB untouched — same drill contract as the current ledger-missing finding); current-shape integrity checks are unchanged (Plan row + Design).

## Alternatives considered

- Dropping the marker audit entirely: rejected — REQ-006 requires the drill to flag legacy databases so operators find them before deploy.

## Implementation
### Target file
`scripts/db/recovery_drill.py`

### Procedure
1. In the Phase 3 commit, swap the audit function bodies and remove the framework import; update the companion test (row 24) in the same commit (Plan Phase 3).

### Method
- Remove `from shared.db_migrations import read_ledger` (line 29) and the `_LEDGER_TABLE = "schema_migrations"` constant plus `_has_ledger_table` / `_read_ledger_state` helpers (currently lines 58-62 region onward) — the ledger-state audit they feed.
- Add a legacy-marker audit (new): for each audited domain database, check `sqlite_master` for `schema_migrations` and `workflow_schema_version`; presence produces an audited finding in the same finding structure the ledger audit used, with the archive-and-recreate guidance in the finding text (REQ-004 message wording).
- Keep every other audit step (shape/integrity checks, artifact writing, live-DB read-only guarantee) byte-identical where possible.

### Details
- If `read_ledger` was used for ledger content reporting in drill artifacts, drop that artifact field together with the audit swap.

### Companion test files
- `tests/db/test_recovery_drill.py`
  - Procedure: replace `test_missing_ledger_is_an_audited_finding` (line 652) with `test_legacy_marker_is_an_audited_finding` (new) — seed a marker table in a scratch domain DB, assert the drill fails, an artifact is written for every domain, and the live DB file hash is unchanged — plus a marker-free case asserting the current-shape audit passes (new).
  - Validation: `uv run pytest tests/db/test_recovery_drill.py` green after Method (Plan Validation plan row).

## Compatibility considerations

- Drill artifact consumers (operator-facing report) see a new finding label; no machine contract depends on the old ledger finding string (Plan row evidence cites only the test).

## Security considerations

- Findings name paths only, no credentials (REQ-004 style).

## Rollback considerations

- Revert the commit restores the ledger audit (single-commit change within the release unit).

## Validation plan

- `uv run pytest tests/db/test_recovery_drill.py` — marker audit finding replaces the ledger finding (Plan Validation plan row).
- `uv run pytest tests/` — rotation/backup/recovery tests continue to pass (AC-008).
- Whole-unit gates run in Plan Phase 5 per `rules/toolchain.md`.

## Completion criteria

- A drill against a legacy (marker-carrying) scratch database fails with the marker finding and leaves the file byte-identical; a marker-free current-shape drill passes (AC-008).

## Out of Scope

- `scripts/db/rotation.py` and `scripts/db/recovery.py` — verified untouched (Reference Files).
- Deleting `shared/db_migrations.py` — sibling document 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace ledger audit with legacy-marker audit; remove framework import (Plan Phase 3) | Pending | — | — | Release unit "current-schema-only-cutover" |
| 2 | Replace companion test `test_missing_ledger_is_an_audited_finding` with marker audit cases and run green | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006 (replace ledger audit with current-shape audit, flag legacy markers)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-081028
- **Related target files**: `scripts/db/recovery_drill.py`, `tests/db/test_recovery_drill.py`
