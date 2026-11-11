## Goal

Move `scripts/eventbus/db_tools.py` off the deleted module: import `assert_matches` from
the generalized `scripts/shared/schema_fingerprint` module (`REQ-003`, fallout 2026-11-10).

## Scope
**Release unit**: fingerprint-cutover (Phase 2; batched with rows 02,03,04,16,23,24,26 because the suite cannot validate green with the stamp removed until this row lands)

## Assumptions
- `scripts/shared/eventbus_schema_fingerprint.py` is deleted in Phase 2 (row 2), so the
  current import at line 25 breaks on deletion.
- `scripts/eventbus/schema.py` removes `_expected_schema_version` (row 3), so the import
  at line 29 must be trimmed.

## Design decisions
- Swap only the import source and resolve the now-orphaned version helper; keep the
  create-or-validate control flow.

## Alternatives considered
N/A: fallout code row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`scripts/eventbus/db_tools.py`

### Procedure
1. Line 25: change `from shared.eventbus_schema_fingerprint import assert_matches` to
   `from shared.schema_fingerprint import assert_matches (new)`.
2. Line 29: drop `_expected_schema_version` from
   `from eventbus.schema import _SCHEMA_PATH, _expected_schema_version`, keeping
   `_SCHEMA_PATH` (used at line 55).
3. Reconcile `schema_version()` (lines 58-60): it currently returns
   `int(_expected_schema_version(schema_sql()))`, which no longer exists. Because the
   canonical DDL no longer stamps `PRAGMA user_version`, the fresh database defaults to
   `user_version 0`; make `schema_version()` return the current version consistently with
   the create path so the kept test's `_state` comparison (`version == db_tools.schema_version()`)
   still holds. Confirm the expected value against `scripts/eventbus/schema.py` (row 3)
   and `tests/eventbus/test_eventbus_db_tools.py`.

### Method
- Locate the references with
  `rg -n 'assert_matches|_expected_schema_version|schema_version|_SCHEMA_PATH' scripts/eventbus/db_tools.py`
  before editing.

### Details
- The `ensure()` refusal path already calls `assert_matches`; after the swap it uses the
  generalized module. The `_check_database` call needed the new ddl argument:
  `assert_matches(conn, schema_sql(), label=str(path))` (found during the row-27 integration
  test: the generalized signature requires canonical_ddl).

## Compatibility considerations
The CLI `schema_version` subcommand (line 148) and the EventBus test import stay; their
values must stay consistent after step 3.

## Security considerations
None beyond the existing read-only fingerprint.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_db_tools.py -v` passes (the stale-version and
unstamped cases are removed by its row); the shape-drift case still refuses.

## Completion criteria
`db_tools.py` imports `assert_matches` from `scripts/shared/schema_fingerprint`, has no reference to the
deleted module or `_expected_schema_version`, and `schema_version()` stays consistent with
the create path.

## Out of Scope
Deleting `eventbus_schema_fingerprint.py` (row 2) and the schema.py changes (row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Swap the assert_matches import; drop the removed version helper | Completed | — | 20261111-083915 | Pre-execution evidence (20261111, read-only assert_matches): deployed /opt/llm/db/eventbus.sqlite carries an extra 'schema_migrations' table and will refuse startup with the new assert until the operator archives and recreates it (UNK-03). rag.sqlite and session.sqlite match; workflow.sqlite carries extra 'execution_snapshots'. import swapped to shared.schema_fingerprint; _expected_schema_version dropped; schema_version() derived from in-memory DDL apply (returns 0); ran early after rows 03/04 to restore importability |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261111-102849 | 20261111-102849 | adrrev005 batch cutover: full suite 12056 passed, 9 skipped; diff-cover 100%; pre-commit all pass |

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
- **Requirement ID**: `REQ-003` — import assert_matches from the generalized module (fallout)
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/eventbus/db_tools.py`
