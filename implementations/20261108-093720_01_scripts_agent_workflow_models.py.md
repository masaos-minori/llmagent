# Implementation procedure: `scripts/agent/workflow/models.py` — declare the status vocabularies

## Goal
Declare the three status vocabularies as module-level frozensets in `models.py` so the workflow state machine exists in exactly one place (`REQ-001`).

## Scope
**Release unit**: wfaudit005-full

- Add `TASK_STATUSES` (new), `ATTEMPT_STATUSES` (new), `TOOL_CALL_STATES` (new) frozensets to `scripts/agent/workflow/models.py`.

## Assumptions
- Vocabularies per `REQ-001`: `TASK_STATUSES` (new) `= frozenset({"pending", "running", "completed", "failed", "halted"})`, `ATTEMPT_STATUSES` (new) `= frozenset({"running", "completed", "failed"})`, `TOOL_CALL_STATES` (new) `= frozenset({"pending", "completed", "failed", "interrupted"})` — the last mirrors the existing `tool_call_state.state` SQL CHECK (`schema_sql.py` L237).
- Completeness of the observed sets was re-validated at HEAD `50b5ac2c6`: engine writes `running`/`halted`/`failed`/`completed` + DDL default `pending`; attempt writes `running` (DDL default, `begin_stage_if_new`), `completed`/`failed` (`finish_attempt`, recovery); tool-call writes are the CHECK set. No other status literal exists in `scripts/` writer call sites.

## Design decisions
- Module-level frozensets next to the existing dataclasses (Plan Design "Single declaration"): every ops module already lives in `agent/workflow/`, so no new module and no cross-layer import.
- The DDL builder does NOT import these constants — import-linter contract `db-only-uses-shared` forbids `db` importing `agent`; the drift guard is the `tests/db/` equality test in sibling document `20261108-093720_05_scripts_db_schema_sql.py.md` (`REQ-003`).

## Alternatives considered
- Declare in `scripts/shared/` so both layers import one source: rejected — workflow status vocabulary is agent-domain data; putting it in `shared` widens the leaf layer for one CHECK clause when a test already pins equality (Plan Design, contract-corrected).

## Implementation
### Target file
`scripts/agent/workflow/models.py`

### Procedure
1. Add the three frozenset constants (new) after the module imports, each with a one-line comment naming the table it constrains (`tasks.status`, `attempts.status`, `tool_call_state.state`).

### Method
- `TASK_STATUSES = frozenset({"pending", "running", "completed", "failed", "halted"})  # tasks.status` — one line per set, matching the `workflow_loader.py` `_RETRY_KINDS` frozenset style already in the package.

### Details
- Current state (verified at HEAD `50b5ac2c6`): `models.py` holds the workflow dataclasses only; no vocabulary declaration exists anywhere in `scripts/` (a substring grep for status-vocabulary names finds nothing).

## Compatibility considerations
- Pure addition; no existing symbol changes. No companion test file in this document: vocabulary tests are owned by sibling document `20261108-093720_06_tests_agent_workflow_.md` (the plan's tests target row).

## Security considerations
- N/A: constant declaration.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/workflow/models.py` | import check | `grep -n 'TASK_STATUSES\|ATTEMPT_STATUSES\|TOOL_CALL_STATES' scripts/agent/workflow/` | constants declared here and imported by the three ops modules (sibling docs 02-04) |
| gates | static | `rules/toolchain.md` sequence incl. `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria
- The three frozensets exist with exactly the `REQ-001` members and are imported by `task_ops.py`, `attempt_ops.py`, `tool_call_state_ops.py` (`Acceptance Criteria REQ-001`).

## Out of Scope
- Writer validation (sibling docs 02-04); DDL CHECKs (sibling doc 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocks wfaudit001 and wfaudit007: land this plan's batch first |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | No companion test file: tests owned by sibling seq 06 |

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
- **Requirement ID**: `REQ-001` (vocabulary declaration)
- **Source issue**: `issues/20261107-203218_wfaudit005_unvalidated-status-writes.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: `plans/20261108-084002_wfaudit005_unvalidated-status-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-093720
- **Related target files**: `scripts/agent/workflow/models.py`
