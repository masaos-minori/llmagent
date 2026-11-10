## Goal
- Remove the EventBus DDL accessors from `scripts/db/schema_sql.py` (REQ-004).

## Scope
**Release unit**: db-eventbus-removal

- In scope: this one file, Phase 3 of the Plan.
- Not in scope: any other file; a second file needed here is an additional-target discovery.
- Execution order follows the Plan's phases, not `seq`: Phase 1 (documents 03, 04), Phase 2 (05, 18), Phase 3 (the `scripts/db`, `scripts/shared`, validator, config, and test documents, one release unit), Phase 4 (01, 38, 39), Phase 5 (the document rows), Phase 6 verification.

## Assumptions
- Overlap with plans 003, 004, 005, 006 (judged in the Plan's Assumptions): sequencing or different keys; no contradiction on this file.
- The Plan's Step 3a corrections apply (EventBus tool reads `db_path` with its own reader; `eventbus_schema_version` and the DDL text accessor move to `scripts/eventbus/db_tools.py`).

## Design decisions
- Remove only what the Plan names for this file; keep every other behavior unchanged.

## Alternatives considered
N/A: the ownership decision (EventBus-side tooling, maintainer 2026-11-10) is fixed in the Plan's Design section.

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. Delete `EVENTBUS_SCHEMA_SQL_PATH`, `eventbus_schema_version()`, and `build_eventbus_schema_sql()` (`schema_sql.py:245-264`) and the docstring entry at line 14.
2. Remove imports left unused (for example `re`) as `ruff` reports them.
3. The version and DDL text are available to tests and tools from `eventbus.db_tools` (`schema_version`, `schema_sql`; document 03).

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- Users of the removed names: `create_schema.py` (07), `tools/check_db_separation.py` (18), and tests (23, 28, 29, 30, 31, 52); all are Plan rows.

### Companion test files
- `tests/eventbus/test_eventbus_startup.py`
  - Procedure: Replace `build_eventbus_schema_sql`/`eventbus_schema_version` imports (`:18`) and uses (`:267, 287, 298, 313, 325`) with `eventbus.db_tools.schema_sql()` and `schema_version()`.
  - Validation: `uv run pytest tests/eventbus/test_eventbus_startup.py -v`

## Compatibility considerations
- See Details; the removal is intentional and has no shim (`tools/check_compat_shims.py`).

## Security considerations
- No authentication or authorization behavior changes; the EventBus path and schema checks stay fail-closed.

## Rollback considerations
- Revert the phase's commit; Phases 1-2 keep the Agent-side path available until Phase 3 lands, so a revert of Phase 3 restores the old behavior.

## Validation plan
- `rg -n "build_eventbus_schema_sql|eventbus_schema_version|EVENTBUS_SCHEMA_SQL_PATH" scripts tests tools` returns no match.
- `uv run ruff check scripts/ tests/ tools/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- The module exposes DDL for rag, session, workflow only.

## Out of Scope
- Editing any other file.
- Redesigning the EventBus, its schema, or its authorization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change in `scripts/db/schema_sql.py` | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261109-112538_adrrev002_agent-eventbus-coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-091327_adrrev002_agent-eventbus-coupling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-102050
- **Related target files**: `scripts/db/schema_sql.py`, `tests/eventbus/test_eventbus_startup.py`
