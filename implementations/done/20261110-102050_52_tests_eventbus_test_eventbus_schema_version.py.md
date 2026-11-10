## Goal
- Import the schema version helper from the EventBus-side tool (REQ-007; fallout row added in Step 3a).

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
`tests/eventbus/test_eventbus_schema_version.py`

### Procedure
1. Replace `from db.schema_sql import eventbus_schema_version` (`:28`) with `from eventbus.db_tools import schema_version` and update the uses (`:75, 81, 130, 199`); keep the assertions.

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- Plan 005 later deletes the `user_version` cases of this file; do not remove them here.

## Compatibility considerations
N/A: test code only.

## Security considerations
N/A: test code only; no credentials involved.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_schema_version.py -v`.

## Completion criteria
- The module no longer imports `db.schema_sql`.

## Out of Scope
- Editing any other file.
- Redesigning the EventBus, its schema, or its authorization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change in `tests/eventbus/test_eventbus_schema_version.py` | Completed | 20261110-122422 | 20261110-122422 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261110-122422 | 20261110-122422 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261110-122422 | 20261110-122422 |  |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20261109-112538_adrrev002_agent-eventbus-coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-091327_adrrev002_agent-eventbus-coupling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-102050
- **Related target files**: `tests/eventbus/test_eventbus_schema_version.py`