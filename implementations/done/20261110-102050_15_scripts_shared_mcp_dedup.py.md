## Goal
- Reword the comment at `mcp_dedup.py:31` that names `eventbus_db_path` (REQ-005).

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
`scripts/shared/mcp_dedup.py`

### Procedure
1. Reword the comment so it cites only `workflow_db_path` (or no key) as the fallback-literal precedent; no code change.

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- Lightweight row; the field-name filter in `tests/shared/test_mcp_dedup.py:338` is the companion edit.

### Companion test files
- `tests/shared/test_mcp_dedup.py`
  - Procedure: Remove `"eventbus_db_path"` from the field-name filter (`:338`).
  - Validation: `uv run pytest tests/shared/test_mcp_dedup.py -v`

## Compatibility considerations
- See Details; the removal is intentional and has no shim (`tools/check_compat_shims.py`).

## Security considerations
- No authentication or authorization behavior changes; the EventBus path and schema checks stay fail-closed.

## Rollback considerations
- Revert the phase's commit; Phases 1-2 keep the Agent-side path available until Phase 3 lands, so a revert of Phase 3 restores the old behavior.

## Validation plan
- `uv run pytest tests/shared/test_mcp_dedup.py -v`; `rg -n eventbus_db_path scripts/shared` is empty.

## Completion criteria
- Comment updated; behavior unchanged.

## Out of Scope
- Editing any other file.
- Redesigning the EventBus, its schema, or its authorization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change in `scripts/shared/mcp_dedup.py` | Completed | 20261110-122422 | 20261110-122422 |  |
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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261109-112538_adrrev002_agent-eventbus-coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-091327_adrrev002_agent-eventbus-coupling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-102050
- **Related target files**: `scripts/shared/mcp_dedup.py`, `tests/shared/test_mcp_dedup.py`