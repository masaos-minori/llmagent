## Goal
- Remove the EventBus DDL accessor from `scripts/db/` so that one rule holds: `scripts/db/` exposes no EventBus DDL (`REQ-005`: remove `build_eventbus_schema_sql` and `_EVENTBUS_SCHEMA_PATH`; `REQ-001`: re-run the searches before editing and keep their output as evidence).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `scripts/db/schema_sql.py` and its companion test file `tests/db/test_create_schema.py`.
- Plan step: Phase 1 of `plans/20261118-164413_adrchk009_plan-code-reconcile.md`.

## Assumptions
- No `scripts/`, `tools/`, `docs/`, `registry/`, `config/`, or `deploy/` file uses the removed symbols; falsifiable by the Phase-1 search below, which is run before the first edit.
- The EventBus-owned accessor `schema_sql()` in `scripts/eventbus/db_tools.py` stays the only EventBus DDL accessor; `tests/db/test_create_schema.py` already builds `_CANONICAL_EVENTBUS_DDL` from it.
- No Frozen Plan overlaps these files (`tools/check_plan_target_overlaps.py` reported none in Step 2 of this cycle).

## Design decisions
- `scripts/db/` exposes no EventBus DDL; the EventBus service and `eventbus.db_tools` own it (the user confirmed this rule on 2026-11-18, consistent with the adrrev002 owner decision of 2026-11-10).
- Delete the accessor, the constant, the module-docstring entry, and the `Path` import that only the constant uses; add no alias, shim, or history comment.

## Alternatives considered
- Keep the accessor and amend adrrev002 `AC-04`: rejected, because it keeps a second reader of `scripts/eventbus/schema.sql` with no production caller and contradicts `docs/41_db/db_08_active_databases.md`.

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. Before editing, run `rg -n "build_eventbus_schema_sql|_EVENTBUS_SCHEMA_PATH" scripts tools tests docs registry config deploy` and the adrrev002 `AC-04` search; keep the output as the `REQ-001` evidence. If a symbol is already gone, record that and skip that edit.
2. Edit `scripts/db/schema_sql.py` as described in Method.
3. Edit the companion test file, then run the tests.

### Method
- Delete the `build_eventbus_schema_sql()` entry from the `Functions:` list of the module docstring.
- Delete `from pathlib import Path` (its only use is `_EVENTBUS_SCHEMA_PATH`; confirm with `rg -n "\bPath\b" scripts/db/schema_sql.py` before and after).
- Delete the `_EVENTBUS_SCHEMA_PATH` assignment and the `build_eventbus_schema_sql` function at the end of the module; the file then ends with `build_workflow_schema_sql`, followed by one newline.

### Details
- Keep `import logging` and the module-level `logger`; they are untouched.
- Do not edit any other builder (`build_rag_schema_sql`, `build_session_schema_sql`, `build_workflow_schema_sql`).

### Companion test files
- `tests/db/test_create_schema.py`
  - Procedure: change the import to `from db.schema_sql import build_workflow_schema_sql`; delete `TestEventbusSchemaFingerprint::test_db_accessor_returns_eventbus_canonical_ddl`; leave `_CANONICAL_EVENTBUS_DDL` and every other test as they are.
  - Validation: `rg -n "build_eventbus_schema_sql" tests` returns no match; `uv run pytest tests/db/test_create_schema.py -v` passes.

## Compatibility considerations
N/A: no `scripts/` caller of the removed symbols exists; the only consumer is the one test removed here.

## Security considerations
N/A: a deletion with no input handling, secret, or approval path.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `rg -n "build_eventbus_schema_sql|_EVENTBUS_SCHEMA_PATH" scripts tools tests docs` returns no match (`AC-05`).
- `rg -n "DbTarget\.EVENTBUS|build_eventbus_schema_sql|create_eventbus_schema|rotate_eventbus_db|eventbus_db_path" scripts/db/ scripts/shared/ scripts/agent/` returns no match (adrrev002 `AC-04`).
- `uv run pytest tests/db -v`, `uv run python tools/check_db_separation.py`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run ruff format --check scripts/db/schema_sql.py tests/db/test_create_schema.py` and `uv run ruff check` on both files.

## Completion criteria
- The two symbols and the docstring entry are absent from `scripts/db/schema_sql.py`, and its `Path` import is gone.
- The companion test file has no reference to `build_eventbus_schema_sql`, and `tests/db` passes.
- The search outputs from step 1 and from the Validation plan are recorded for the adrrev002 and adrrev005 edits (`REQ-001`).

## Out of Scope
- Any change to `scripts/eventbus/`, DDL, or the other builders; edits to the two archived plans (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-run the searches, then remove the accessor, constant, docstring entry, and `Path` import from `scripts/db/schema_sql.py` | Pending | — | — | |
| 2 | Update the companion test file `tests/db/test_create_schema.py` (import and one test) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (re-run the searches and keep the evidence), `REQ-005` (remove the EventBus DDL accessor and its consumer test)
- **Source issue**: issues/20261117-123009_adrchk009_plan-code-reconcile.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-164413_adrchk009_plan-code-reconcile.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-165056
- **Related target files**: `scripts/db/schema_sql.py`, `tests/db/test_create_schema.py`
