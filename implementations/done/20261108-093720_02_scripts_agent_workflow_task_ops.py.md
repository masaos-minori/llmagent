# Implementation procedure: `scripts/agent/workflow/task_ops.py` — validate `status` in `update_task_status`

## Goal
Reject out-of-vocabulary task statuses with a typed `ValueError` before any SQL runs, so a typo can no longer create an invisible status row (`REQ-002`).

## Scope
**Release unit**: wfaudit005-full

- One validation guard at the top of `update_task_status` (L68-74) plus the `models.py` import.

## Assumptions
- All production writers already pass vocabulary-valid values (verified: `workflow_engine.py` L213-224 writes `running`/`halted`/`failed`/`completed`; adapter L230/L273 writes `halted` only) — the guard is a no-op for current behavior (`REQ-005`).
- Task creation (`create_task`) keeps the DDL default `'pending'` unchanged; only status updates are validated (Plan target row: "creation default stays `pending`").

## Design decisions
- Validate at the writer helper, not at each caller (Plan Design "Validate at the writer"): engine, adapter, facade, and future `wfaudit001`/`wfaudit007` reconciliation all flow through this function.
- Error message names the table and the offending value (`REQ-002`): `raise ValueError(f"invalid tasks.status {status!r}")` — consistent with the project typed-error convention.

## Alternatives considered
- Rely on a DDL CHECK only: rejected for existing databases (no ALTER path; Plan Out-of-Scope) — code-side validation is the enforcement that works on legacy databases too (Plan Assumptions).

## Implementation
### Target file
`scripts/agent/workflow/task_ops.py`

### Procedure
1. Import `TASK_STATUSES` from `agent.workflow.models` (new import).
2. At the top of `update_task_status`, before `db.execute`, add: `if status not in TASK_STATUSES: raise ValueError(f"invalid tasks.status {status!r} (allowed: {sorted(TASK_STATUSES)})")`.
3. Extend the docstring with a `Raises ValueError` line.

### Method
- Guard-first pattern; no other statement in the function changes.

### Details
- Current state (verified at HEAD `50b5ac2c6`): `update_task_status` writes any caller-supplied string with no check; the halted-task guard (`workflow_engine_adapter.py` L315) is the reader a bad status would silently miss (Plan Problem).

## Compatibility considerations
- `ValueError` propagates to every caller except `_record_exit_status`, whose own try already swallows status-write failures observably (adapter L262-278) — a vocabulary bug there degrades instead of aborting a turn (Plan Design).
- Blast radius before landing (rules/toolchain.md): `rg -l '\bupdate_task_status\b' tests/ | wc -l` = 2 — known test writers are `tests/agent/test_orchestrator.py` (15) and `tests/agent/workflow/test_workflow_state_store.py` (2) at HEAD `11c20696a`; they pass only vocabulary-valid statuses (`halted`, `running`) or subclass overrides, so expect green (`REQ-005`).
- Rejection tests are owned by sibling document `20261108-093720_06_tests_agent_workflow_.md` (the plan's tests target row); this document has no companion of its own.

## Security considerations
- N/A: input validation on an existing helper; no new surface.

## Rollback considerations
- N/A: revert the commit; no persistence change.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/workflow/task_ops.py` | rejection tests (sibling seq 06 owns them) | `uv run pytest tests/agent/workflow/ -q` | `update_task_status(task, "done")` raises `ValueError`, row unchanged (`REQ-002`) |
| blast radius | static | `rg -l '\bupdate_task_status\b' tests/ \| wc -l` | measured before landing; known writers pass valid statuses |
| gates | static | `rules/toolchain.md` sequence incl. lint-imports | clean |

## Completion criteria
- Out-of-vocabulary status raises `ValueError` naming table and value and writes nothing (`Acceptance Criteria REQ-002`); valid-status behavior unchanged (`REQ-005`).

## Out of Scope
- `create_task` and the `tasks` DDL default.
- Reconciliation call sites of `wfaudit001`/`wfaudit007` (sequenced after this plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261108-125308 | 20261108-125308 | Blocks wfaudit001 and wfaudit007: land this plan's batch first memo3 adversarial verification pass at HEAD 11c20696a: stale check clean; blast-radius counts updated 15/2 at HEAD 11c20696a; adapter halted-only + guard behavior confirmed guard-first ValueError added at update_task_status; TASK_STATUSES import; ruff format applied |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261108-125308 | 20261108-125308 | No companion test file: rejection tests owned by sibling seq 06 ruff+format+mypy pass; lint-imports 6 kept; pytest tests/agent/workflow+test_orchestrator 285 passed; stale_detector clean |

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
- **Requirement ID**: `REQ-002` (task-status writer validation)
- **Source issue**: `issues/20261107-203218_wfaudit005_unvalidated-status-writes.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: `plans/20261108-084002_wfaudit005_unvalidated-status-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-093720
- **Related target files**: `scripts/agent/workflow/task_ops.py`