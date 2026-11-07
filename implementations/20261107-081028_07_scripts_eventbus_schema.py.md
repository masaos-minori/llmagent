## Goal

- Remove `MigrationRunner`/`REGISTRY`/`read_ledger` wiring and the auto-migration and auto-stamp branches from `scripts/eventbus/schema.py`, keeping `user_version == 6` plus fingerprint acceptance and rejecting `user_version = 0` without stamping (REQ-003: current-schema-only startup validation; REQ-004: refusal writes nothing).

## Scope
**Release unit**: current-schema-only-cutover

- Single-function rework of `_init_schema` plus import cleanup in this file; companion test rows 20-21 (`tests/eventbus/test_eventbus_schema_version.py`, `tests/eventbus/test_eventbus_startup.py`) are covered here as companions.

## Assumptions

- After REQ-001, refusals consolidate onto the plain `RuntimeError` raised by `shared.eventbus_schema_fingerprint` — that module defines no `MigrationRefusalError` (Plan Design, re-verified 2026-11-07).
- New databases get the `PRAGMA user_version = 6` stamp only from canonical `schema.sql` via `create_eventbus_schema` (sibling document 09).
- `scripts/eventbus/db_conn.py` calls `_init_schema` on connection (lines 21/95 region); its behavior changes only through this function — `db_conn.py` is a read-only Reference File.

## Design decisions

- Accept iff `found == expected` (fingerprint `assert_matches`) — everything else raises the fixed REQ-004 refusal text (database path, expected/detected versions, archive-and-recreate guidance) before any mutation; the `found == 0 && shape matches → stamp` branch and the registered-migration branch are both deleted, not replaced.
- Refusal type stays `RuntimeError` (no new exception class): the gate already raised `RuntimeError` for unregistered/downgrade cases.

## Alternatives considered

- Keeping the `user_version = 0` auto-stamp for marker-free current-shape databases: rejected by REQ-003 ("unversioned databases are rejected and left unstamped").

## Implementation
### Target file
`scripts/eventbus/schema.py`

### Procedure
1. Phase 1 (companion test file below) rewrites the version tests into a rejection matrix; confirm RED.
2. In the Phase 2 commit, apply the import and branch removals below; confirm the companion tests green.

### Method
- Delete the imports `from shared.db_migrations import MigrationRefusalError, MigrationRunner, read_ledger` (line 8) and `from eventbus.migrations import REGISTRY, verify_backup` (line 11), and the `_MIGRATIONS = MigrationRunner()` module-level assignment (line 16 region, with its dbmig001 comment line).
- In `_init_schema`: keep the `found == expected → assert_matches(conn); return` branch. Delete the `found == 0 and _matches_current_schema(conn, sql)` stamp branch and the whole registered-forward-migration `try/except` block (currently the lines 101-121 region: `_MIGRATIONS.plan(...)`, `_MIGRATIONS.apply(conn, path, verify_backup)`, the `except (MigrationRefusalError, sqlite3.Error)` re-raise, and the post-migration `assert_matches`/log lines).
- Replace both deleted branches with a single refusal that raises the fixed REQ-004 message text (Plan Design "Refusal message") carrying the database path, `found`, and `expected` — before any write, archive, or delete (AC-005).

### Details
- Keep `_matches_current_schema` if it is still referenced (shape checks); verify remaining callers before removing it.
- `_SCHEMA_PATH` (line 18 region) and the `expected` derivation from `schema.sql` stay unchanged.

### Companion test files
- `tests/eventbus/test_eventbus_schema_version.py`
  - Procedure: delete `test_unstamped_current_database_is_stamped` (line 56) and `test_registered_v3_database_migrates_at_startup` (line 121); keep `test_schema_version_is_pinned_to_six` (line 76), `test_mismatched_version_is_refused` (line 46), `test_unstamped_old_shape_is_refused_and_left_unstamped` (line 66), `test_database_stamped_one_is_refused` (line 105), `test_future_version_is_refused` (line 160); add `test_unstamped_current_shape_is_refused_and_left_unstamped` (new) and file-hash-unchanged assertions on every rejection case (new), covering the version 0/5/6/7 + altered-shape matrix (Plan Validation plan row).
  - Validation: `uv run pytest tests/eventbus/test_eventbus_schema_version.py` — RED in Phase 1, green after this document's Method; hashes unchanged on rejection.
- `tests/eventbus/test_eventbus_startup.py`
  - Procedure: replace manual fixture stamping (`conn.execute(f"PRAGMA user_version = {eventbus_schema_version()}")` at lines 265-269 region) with creation through the canonical `create_eventbus_schema` path; add a case (new) asserting an unstamped DDL-only database is refused by `open_db` and stays at `user_version = 0`.
  - Validation: `uv run pytest tests/eventbus/test_eventbus_startup.py` green after Method; fresh DB marker-free.

## Compatibility considerations

- `scripts/eventbus/db_conn.py` needs no edit: it inherits the new gate behavior (Reference File).
- Existing stamped, current-shape databases open normally (AC-006).

## Security considerations

- Refusal message names paths and versions but no credentials (REQ-004 / AC-005).

## Rollback considerations

- Revert the commit restores the migration wiring (single-commit change within the release unit).

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_schema_version.py tests/eventbus/test_eventbus_startup.py` — full rejection matrix passes; hashes unchanged; fresh DB marker-free (Plan Validation plan row).
- `uv run python tools/check_db_separation.py` and fingerprint tests — clean against the regenerated DDL (REQ-008).
- Whole-unit gates run in Plan Phase 5 per `rules/toolchain.md`.

## Completion criteria

- Only `user_version == 6` + fingerprint match opens an eventbus database; every other state raises the fixed refusal with the file byte-identical before/after (AC-004, AC-005); a missing database is created stamped via canonical DDL (AC-006).

## Out of Scope

- Deleting `scripts/eventbus/migrations.py` — sibling document 03.
- Removing the ledger CREATE from `scripts/eventbus/schema.sql` — sibling document 09.
- Workflow domain gate — sibling document 10.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite companion version/startup tests into the rejection matrix; confirm RED (Plan Phase 1) | Pending | — | — | Release unit "current-schema-only-cutover": intentionally RED until Phase 2 |
| 2 | Remove framework imports, `_MIGRATIONS`, stamp branch, and migration branch; add fixed refusal (Plan Phase 2) | Pending | — | — | |
| 3 | Run `uv run pytest tests/eventbus/test_eventbus_schema_version.py tests/eventbus/test_eventbus_startup.py` green | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (current-schema-only startup validation), REQ-004 (refusal performs no write)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-081028
- **Related target files**: `scripts/eventbus/schema.py`, `tests/eventbus/test_eventbus_schema_version.py`, `tests/eventbus/test_eventbus_startup.py`
