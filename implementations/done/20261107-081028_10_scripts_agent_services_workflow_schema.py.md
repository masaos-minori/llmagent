## Goal

- Rework the Workflow startup/health gate in `scripts/agent/services/workflow_schema.py` to shape-only acceptance: drop the `workflow_schema_version` table requirement and version-row comparison, and reject databases carrying either legacy marker table (REQ-003: current-schema-only validation; REQ-004: refusal performs no write).

## Scope
**Release unit**: current-schema-only-cutover

- Gate logic change in this file only; its test coverage (`tests/agent/test_repl_health.py`) is carried as a companion (row 22 is named exactly by this row's Related Tests).

## Assumptions

- `workflow_schema_version` is migration history, so shape-only acceptance is the end state; no new workflow version mechanism is introduced (Plan Design).
- The companion test file is edited in both Phase 1 (add rejection cases, Plan Phase 1) and Phase 3 (fixture alignment, Plan Phase 3).

## Design decisions

- Required shape = current `REQUIRED_WORKFLOW_TABLES` entries minus the `"workflow_schema_version": ["version", "applied_at"]` entry (line 58 region); presence of `schema_migrations` or `workflow_schema_version` in `sqlite_master` → `SchemaCheckResult(valid=False)` with the fixed legacy-marker message (new) naming the archive-and-recreate procedure (REQ-004).
- Exact-shape pinning (required tables/columns) stays: marker-free current-shape databases pass unchanged (AC-006).

## Alternatives considered

- Keeping the version-row comparison but tolerating a missing table: rejected — REQ-003 treats any marker presence as legacy rejection.

## Implementation
### Target file
`scripts/agent/services/workflow_schema.py`

### Procedure
1. Phase 1 (companion test file below) adds legacy-marker rejection cases; confirm RED.
2. In the Phase 3 commit, apply the gate rework below; confirm the companion tests green.

### Method
- Remove the `"workflow_schema_version": ["version", "applied_at"],` entry (line 58) from `REQUIRED_WORKFLOW_TABLES`.
- Remove the `from db.schema_sql import WORKFLOW_SCHEMA_VERSION` import (line 78 region) and the version-check block (currently lines 118-129 region): the `SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1` fetch, the `actual_version != WORKFLOW_SCHEMA_VERSION` comparison, and its `SchemaCheckResult(valid=False, ...)` return.
- Add a marker-absence check before returning `SchemaCheckResult(valid=True)`: query `sqlite_master` for `schema_migrations` and `workflow_schema_version` (new helper or inline fetch), and on presence return `valid=False` with the fixed legacy-marker guidance text (REQ-004).

### Details
- The check is read-only: no write, archive, or delete on rejection (AC-005).

### Companion test files
- `tests/agent/test_repl_health.py`
  - Procedure: remove `from db.schema_sql import WORKFLOW_SCHEMA_VERSION` (line 27); delete the version-gate tests `test_matching_schema_version_passes` (line 614), `test_missing_schema_version_row_fails` (line 619), `test_mismatched_schema_version_fails` (line 625), and invert `test_missing_workflow_schema_version_table_fails` (line 631) into a passes-without-marker case; update the fixture signature `schema_version: str | None = WORKFLOW_SCHEMA_VERSION` (line 525, plus its `workflow_schema_version` CREATE in the body) and the call `db_path = _create_workflow_db(tmp_path, schema_version=WORKFLOW_SCHEMA_VERSION)` (line 615, deleted with its test) to drop the version parameter; keep the lease-columns case (line 606); add legacy-marker rejection cases: seeds `schema_migrations` or `workflow_schema_version` into a scratch workflow DB and asserts invalid result plus unchanged file hash (new).
  - Validation: `uv run pytest tests/agent/test_repl_health.py` — RED on the new cases in Phase 1, green after Method (Plan Validation plan row).

## Compatibility considerations

- Agent startup and REPL health paths consume `SchemaCheckResult` unchanged in shape; only the message on marker-present databases differs.

## Security considerations

- Failure message names paths and the manual recreate procedure, no credentials (REQ-004).

## Rollback considerations

- Revert the commit restores the version comparison (single-commit change within the release unit).

## Validation plan

- `uv run pytest tests/agent/test_repl_health.py` — marker present → invalid; marker-free current shape → valid (Plan Validation plan row).
- Whole-unit gates run in Plan Phase 5 per `rules/toolchain.md`.

## Completion criteria

- A workflow database with either marker table fails `check_workflow_schema` with the fixed message and byte-identical file; a marker-free current-shape database passes (AC-004, AC-006).

## Out of Scope

- `schema_sql.py` DDL removal — sibling document 08.
- `deploy/init_db.sh` gate — sibling document 12.
- `tests/deploy/test_setup_services_eventbus.py` fixture alignment — own document (seq 23).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add companion legacy-marker rejection cases; confirm RED (Plan Phase 1) | Completed | — | — | Release unit "current-schema-only-cutover" Companion rejection cases RED then green. Gate: marker entry removed from REQUIRED_WORKFLOW_TABLES, WORKFLOW_SCHEMA_VERSION import and version-row comparison removed, marker-absence check added before valid=True (marker check runs before required-table loop so legacy DBs are refused as legacy). Fixed refusal wording used. Fixture deviation: workflow fixture seeds PRAGMA journal_mode=WAL (SQLiteHelper applies the pragma on read opens; without seeding, the gate's open mutates the plain-mode DB header and the no-write hash assertion cannot hold). test_repl_health.py 43 passed, test_startup_rollback.py 14 passed, ruff clean. |
| 2 | Remove marker entry, version import/comparison; add marker-absence check (Plan Phase 3) | Completed | — | — | Companion rejection cases RED then green. Gate: marker entry removed from REQUIRED_WORKFLOW_TABLES, WORKFLOW_SCHEMA_VERSION import and version-row comparison removed, marker-absence check added before valid=True (marker check runs before required-table loop so legacy DBs are refused as legacy). Fixed refusal wording used. Fixture deviation: workflow fixture seeds PRAGMA journal_mode=WAL (SQLiteHelper applies the pragma on read opens; without seeding, the gate's open mutates the plain-mode DB header and the no-write hash assertion cannot hold). test_repl_health.py 43 passed, test_startup_rollback.py 14 passed, ruff clean. |
| 3 | Align companion fixtures and run `uv run pytest tests/agent/test_repl_health.py` green (Plan Phase 3) | Completed | — | — | Companion rejection cases RED then green. Gate: marker entry removed from REQUIRED_WORKFLOW_TABLES, WORKFLOW_SCHEMA_VERSION import and version-row comparison removed, marker-absence check added before valid=True (marker check runs before required-table loop so legacy DBs are refused as legacy). Fixed refusal wording used. Fixture deviation: workflow fixture seeds PRAGMA journal_mode=WAL (SQLiteHelper applies the pragma on read opens; without seeding, the gate's open mutates the plain-mode DB header and the no-write hash assertion cannot hold). test_repl_health.py 43 passed, test_startup_rollback.py 14 passed, ruff clean. |
| 4 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Completed | — | 20261107-134741 | end-of-unit run: ruff, mypy 558 files, lint-imports 6 kept, bandit -ll rc 0, full-suite coverage 11780 passed, diff-cover 100 pct |

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
- **Requirement ID**: REQ-003 (shape-only acceptance, legacy markers rejected), REQ-004 (refusal performs no write)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-081028
- **Related target files**: `scripts/agent/services/workflow_schema.py`, `tests/agent/test_repl_health.py`