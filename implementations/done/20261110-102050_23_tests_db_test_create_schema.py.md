## Goal
- Remove the Agent-side eventbus creation cases (REQ-007); their behavior is covered by `tests/eventbus/test_eventbus_db_tools.py`.

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
`tests/db/test_create_schema.py`

### Procedure
1. Remove the `build_eventbus_schema_sql`/`eventbus_schema_version` imports (`:24, 26`), the eventbus branch of the config helper (`:194-198`), and every test class or case that exercises `create_eventbus_schema` (around `:827-1574`, including the `PRAGMA user_version` cases).
2. Keep the rag, session, workflow cases; re-run to confirm no helper became unused.

### Method
- Targeted edits; remove imports left unused as `ruff` reports them.

### Details
- 50 hits for the removed names (rg count); the removed cases map to the document 04 tests (fresh, current, stale, unstamped, malformed).

## Compatibility considerations
N/A: test code only.

## Security considerations
N/A: test code only; no credentials involved.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_create_schema.py -v`; `rg -n "eventbus" tests/db/test_create_schema.py` is empty.

## Completion criteria
- The module has no eventbus case and passes.

## Out of Scope
- Editing any other file.
- Redesigning the EventBus, its schema, or its authorization.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change in `tests/db/test_create_schema.py` | Completed | 20261110-122422 | 20261110-122422 | Kept TestEventbusSchemaFingerprint (the only tests of the shared fingerprint validator) with the DDL taken from eventbus.db_tools; creation, validate-first, timestamp and table/column tests removed (moved to document 04). |
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
- **Related target files**: `tests/db/test_create_schema.py`