## Goal
Delete `_migrate()` and simplify `_init_schema()` so the service creates the schema from `schema.sql` when `events` is absent and does nothing otherwise (REQ-003).

## Scope
- Remove `_migrate()`, its call, the `_COL_*` imports used only by it, and the stale docstring/comment text in `scripts/eventbus/schema.py`.
- The `eventbus-is-isolated` import contract must keep holding.

## Assumptions
- `open_db()` in `scripts/eventbus/db_conn.py` is the only caller of `_init_schema()` and imports only `_apply_eventbus_pragmas` and `_init_schema` from this module (verified).
- Every `_COL_*` name imported here is used only inside `_migrate()` (verified); the constants themselves stay in `scripts/eventbus/_constants.py` because other modules use them.
- Decision recorded in the Plan (UNK-01): an existing `events` database is left untouched; running `schema.sql` on every start is an alternative the owner may choose instead.

## Design decisions
- `_init_schema()` keeps its table-exists probe and returns early when `events` exists; otherwise it executes `schema.sql`.
- Update the module docstring from "schema definition, migration logic" to schema definition and creation only.

## Alternatives considered
- Always executing `schema.sql` (idempotent) so missing indexes/tables are repaired: rejected for now because the Issue's stated simplest behavior is "do nothing" and the baseline guarantees the current schema; recorded as UNK-01.

## Implementation
### Target file
`scripts/eventbus/schema.py`

### Procedure
1. Delete `_migrate()` entirely.
2. In `_init_schema()` replace the `_migrate(conn)` branch with a plain early `return`; update the docstring ("Create the events schema when the table is absent").
3. Delete the import block of `_COL_*` names; keep `Path`, `Connection`, `_SCHEMA_PATH`, `_DEFAULT_BUSY_TIMEOUT_MS`, and `_apply_eventbus_pragmas`.
4. Update the module docstring; leave the `logger` declaration (accepted unused-logger boilerplate).

### Method
- Delete by symbol; run `ruff` to confirm no unused import remains.
- Verify `PYTHONPATH=scripts uv run lint-imports` still passes (`eventbus-is-isolated`).

### Details
- Do not touch `_apply_eventbus_pragmas`, `_SCHEMA_PATH`, or `schema.sql`.

## Compatibility considerations
A database at the current schema starts exactly as before. A database older than the baseline is no longer repaired at startup (recreate instead).

## Security considerations
N/A: removes in-place DDL/DML on the live database at every start.

## Rollback considerations
Revert the commit; no data changes by this edit.

## Validation plan
- `uv run pytest tests/db/test_eventbus_schema_equivalence.py tests/eventbus -q`, then the full suite once.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`.

## Completion criteria
- `_migrate` no longer exists; `_init_schema()` creates the schema on an empty path and leaves an existing database unchanged.
- No unused imports; import contracts pass.

## Out of Scope
- `schema.sql`, the DB bootstrap in `scripts/db/`, and the `_constants.py` module.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `_migrate()`, simplify `_init_schema()`, drop unused imports | Pending | — | — | |
| 2 | Tests are covered by the test-file procedures | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Deploy step: run the read-only column check on `/opt/llm` `eventbus.sqlite`, deploy, verify startup | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (remove `_migrate()` and simplify `_init_schema()`)
- **Source issue**: `issues/20261021-102130_rmebmig_remove-the-eventbus.sqlite-schema-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093935_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101015
- **Related target files**: scripts/eventbus/schema.py
