<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "tests/agent/workflow/test_workflow_recovery.py", "target_kind": "test", "seq": 17} -->

## Goal

Create `tests/agent/workflow/test_workflow_recovery.py` with the crash, resume, and repeated-recovery regression scenarios (REQ-006, REQ-007, REQ-011 / AC-6, AC-7).

## Scope

- New file in the existing `tests/agent/workflow/` directory (no recovery-scenario test file exists at HEAD).
- Scenarios (each fails against HEAD first, REQ-011): crash after the attempt row is written (no ledger row -> stage restartable with next number); crash after a side effect before the attempt is finished (stale `running` attempt -> recovery fails attempt + owning `running` task); repeated restart and recovery (idempotent); resume of a `failed` task after one or more attempts (numbering continues via row 14's engine path); resume of `completed`, `halted`, and `running` tasks is rejected.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- Scenario harness: build a workflow database via `schema_sql._WORKFLOW_SCHEMA`, simulate a crash by leaving rows in their written state, then run `recover_stale_attempts` and/or `WorkflowEngine.run` against the same file.

## Design decisions

- One test class per scenario with names mirroring the REQ-011 list, so the traceability table maps 1:1.

## Alternatives considered

- Extending `test_workflow_state_store.py` instead: rejected — the frozen table names this new file for the crash/resume family.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_recovery.py` (new)

### Procedure
1. Create the module with a shared `workflow_db`-style fixture.
2. Implement the five scenario groups.

### Method
New file creation.

### Details
- Existing recovery-adjacent tests (`test_workflow_state_store.py:449-542`) stay in place; this file covers the engine-visible crash/resume contract.

## Compatibility considerations

- Row 23 cites this file in the ADR test table.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Delete the file.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_recovery.py -v` — red on HEAD, green after Phase 3/4.

## Completion criteria

- All REQ-011 recovery scenarios have named tests (AC-6, AC-7).

## Out of Scope

- Concurrency (row 18); migration fixtures (row 22).

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
- **Requirement ID**: `REQ-006`, `REQ-007`, `REQ-011`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `tests/agent/workflow/test_workflow_recovery.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/workflow_engine.py`, `tests/agent/workflow/test_workflow_concurrency.py`
