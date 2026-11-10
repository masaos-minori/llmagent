## Goal
- Remove EventBus schema creation from `create_schema` (REQ-004).

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
`scripts/db/create_schema.py`

### Procedure
1. Delete `create_eventbus_schema()` (`create_schema.py:84-131`) and the `create_eventbus_schema()` call in `create_schema()` (`:134-140`).
2. Remove the imports it alone used (`build_eventbus_schema_sql`, `eventbus_schema_version`, `validate_canonical` if unused elsewhere) and update the module docstring (lines 10-18) and `create_schema` docstring to three databases.
3. Do not touch the rag, session, workflow creation functions.

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- Production reach of the removed function was confirmed: `deploy/init_db.sh` ran it (Plan Background); Phase 2 (document 05) moves that to `eventbus.db_tools.ensure`, so this removal must follow Phase 2.

## Compatibility considerations
- `uv run python scripts/db/create_schema.py` no longer creates eventbus.sqlite; `deploy/init_db.sh` creates it through `eventbus.db_tools` (Phase 2).

## Security considerations
- No authentication or authorization behavior changes; the EventBus path and schema checks stay fail-closed.

## Rollback considerations
- Revert the phase's commit; Phases 1-2 keep the Agent-side path available until Phase 3 lands, so a revert of Phase 3 restores the old behavior.

## Validation plan
- `uv run pytest tests/db/test_create_schema.py -v`; `rg -n "create_eventbus_schema|eventbus" scripts/db/create_schema.py` is empty.
- `uv run ruff check scripts/ tests/ tools/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- `create_schema()` creates rag, session, workflow only.

## Out of Scope
- Editing any other file.
- Redesigning the EventBus, its schema, or its authorization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change in `scripts/db/create_schema.py` | Pending | — | — | |
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
- **Related target files**: `scripts/db/create_schema.py`
