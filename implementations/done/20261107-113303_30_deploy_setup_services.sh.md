## Goal

- Remove the Workflow schema-version gate from `deploy/setup_services.sh`: the block imports the deleted `WORKFLOW_SCHEMA_VERSION` constant and queries the deleted `workflow_schema_version` table, so it FATAL-exits on every marker-free post-cutover database (amended plan row: REQ-002 / AC-002 fallout).

## Scope
**Release unit**: current-schema-only-cutover

- Shell block deletion in this file only; the fixture alignment of the deploy test that seeds the version row is own-document seq 23 (`tests/deploy/test_setup_services_eventbus.py`, landed in the same Phase 3 commit).

## Assumptions

- The table-presence pre-flight above the gate (`REQUIRED_WORKFLOW_TABLES="tasks attempts processed_events artifacts"`, line 55) already excludes marker tables and stays unchanged (verified 2026-11-07).
- No test asserts the removed gate's stdout/stderr strings (`grep -rn "Workflow schema version" tests/deploy/` returns nothing), so removing the block breaks no assertion (verified 2026-11-07).

## Design decisions

- Delete the version block outright rather than replace it with a marker-absence check: the workflow shape gate owns marker rejection (`scripts/agent/services/workflow_schema.py`, sibling document 10) and the startup pre-flight in `start_agent.sh` already runs the shape check; duplicating marker detection in `setup_services.sh` would create a third gate with no owner (Plan Design: one gate per domain).

## Alternatives considered

- Keeping an echo-only informational line: rejected — both values it would print come from removed symbols, and the Plan removes workflow version reporting entirely.

## Implementation
### Target file
`deploy/setup_services.sh`

### Procedure
1. In the Phase 3 commit (Plan Phase 3), land this block deletion together with document 23's fixture alignment (the fixture stops seeding `workflow_schema_version` in the same commit so the sandbox tests never run against a half-migrated state).

### Method
- Delete the whole version gate block (lines 71-80): the `EXPECTED_SCHEMA_VERSION=$(... "from db.schema_sql import WORKFLOW_SCHEMA_VERSION; print(WORKFLOW_SCHEMA_VERSION)")` assignment, the `ACTUAL_SCHEMA_VERSION=$(sqlite3 ... "SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1;")` query, the `echo "Workflow schema version: ..."` line, and the mismatch `if` block with its `[FATAL]` message and `exit 1`.
- Keep the `MISSING_TABLES` loop (lines 55-69) and the trailing `echo "OK: workflow definition and schema pre-flight checks passed"` byte-identical.

### Details
- No new gate text is added here; the archive-and-recreate guidance for legacy workflow databases is owned by `init_db.sh` (document 12) and `check_workflow_schema` (document 10).

## Compatibility considerations

- Operators see one fewer stdout line; a legacy marker-carrying database now starts past this script's pre-flight and is refused by the agent's own `check_workflow_schema` gate (document 10) or by `init_db.sh` (document 12).

## Security considerations

- N/A: gate deletion removes a subprocess import of a deleted module; no new input handling.

## Rollback considerations

- Revert the commit restores the version gate (single-commit change within the release unit).

## Validation plan

- `uv run pytest tests/deploy/test_setup_services_eventbus.py` — green with document 23's aligned fixtures (sandbox `setup_services.sh` run reaches the health-check stage without a version gate).
- `bash -n deploy/setup_services.sh` — syntax check.
- Whole-unit gates run in Plan Phase 5 per `rules/toolchain.md`.

## Completion criteria

- `setup_services.sh` references neither `WORKFLOW_SCHEMA_VERSION` nor `workflow_schema_version` (`grep` in the file returns nothing) and its sandbox tests pass with marker-free fixtures (AC-002, AC-003).

## Out of Scope

- Fixture alignment in `tests/deploy/test_setup_services_eventbus.py` — own document (seq 23).
- `init_db.sh` gate inversion — sibling document 12.
- Workflow shape gate rework — sibling document 10.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the version gate block lines 71-80 with document 23 in the same commit (Plan Phase 3) | Completed | — | 20261107-130238 | Release unit "current-schema-only-cutover" Version gate block deleted (EXPECTED/ACTUAL_SCHEMA_VERSION + mismatch FATAL); MISSING_TABLES loop and OK echo byte-identical; bash -n clean; grep shows no WORKFLOW_SCHEMA_VERSION/workflow_schema_version in the file; tests/deploy 29 passed. Landed with doc 23 fixture alignment in the same change. |
| 2 | Run `uv run pytest tests/deploy/test_setup_services_eventbus.py` green; `bash -n` clean | Completed | — | 20261107-130238 | Version gate block deleted (EXPECTED/ACTUAL_SCHEMA_VERSION + mismatch FATAL); MISSING_TABLES loop and OK echo byte-identical; bash -n clean; grep shows no WORKFLOW_SCHEMA_VERSION/workflow_schema_version in the file; tests/deploy 29 passed. Landed with doc 23 fixture alignment in the same change. |
| 3 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Completed | — | 20261107-134719 | end-of-unit: check_compat_shims and check_db_separation passed, full suite green, coverage and diff-cover green; production agent-API restart deferred to ops startup-guard enabling (Plan UNK-01) |

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
- **Requirement ID**: REQ-002 (removed constant/table must not remain referenced), AC-002 (marker-free databases start normally)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md (amended 2026-11-07, fallout row)
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-113303
- **Related target files**: `deploy/setup_services.sh`