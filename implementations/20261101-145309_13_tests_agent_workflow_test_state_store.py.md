<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "tests/agent/workflow/test_state_store.py", "target_kind": "test", "seq": 13} -->

## Goal

Update `tests/agent/workflow/test_state_store.py` recovery mocks/assertions for the atomic attempt+task recovery (REQ-006, REQ-011 / AC-7).

## Scope

- The mocked recovery suite (`test_state_store.py:13-233`: mocks `find_stale_running_attempts`, asserts recovery counts) gains task-status assertions: each recovered attempt's owning `running` task becomes `failed`; an already-terminal owner is untouched.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- The suite mocks `SQLiteHelper` calls; assertions pin the per-attempt transaction shape (attempt UPDATE then task UPDATE before commit).

## Design decisions

- Count semantics: `recover_stale_attempts` return value keeps counting transitioned attempts; task-side transitions are asserted separately.

## Alternatives considered

- Porting all recovery coverage to raw-SQL integration tests (row 17): rejected — this file's mock style is the existing pattern the ADR test table cites.

## Implementation
### Target file
`tests/agent/workflow/test_state_store.py`

### Procedure
1. Extend the existing recovery test cases with `tasks` status assertions.
2. Add a repeated-recovery case (second call returns 0 and changes nothing).

### Method
Direct edit; additive assertions plus one new case.

### Details
- Mock call recording must expect the added conditional task UPDATE (`AND status='running'`).

## Compatibility considerations

- ADR citation row is updated by row 23.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Revert with row 06.

## Validation plan

- `uv run pytest tests/agent/workflow/test_state_store.py -v`; fails pre-change (REQ-011).

## Completion criteria

- Recovery tests prove atomicity, owner-conditionality, and idempotent repeats (AC-7).

## Out of Scope

- Concurrency or crash scenarios.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 3 (Attempt lifecycle, ledger, and recovery)
- **Requirement ID**: `REQ-006`, `REQ-011`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `tests/agent/workflow/test_state_store.py`, `scripts/agent/workflow/state_store.py`, `tests/agent/workflow/test_workflow_recovery.py`
