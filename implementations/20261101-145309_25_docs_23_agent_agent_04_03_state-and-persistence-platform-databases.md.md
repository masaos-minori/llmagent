<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md", "target_kind": "documentation", "seq": 25} -->

## Goal

Update the StateStore responsibility-scope paragraph and the `begin_stage_if_new` bullet in `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` (REQ-010 / AC-11).

## Scope

- `### StateStore Responsibility Scope` (`:70-72`): reword "stage-level idempotency (duplicate-event detection and atomic attempt initiation)" to the completed-stage-ledger contract.
- `begin_stage_if_new` bullet (`:100`): state the single canonical start (ledger check, running-attempt check, `attempt_number = MAX + 1` insert in one transaction) and the `StageAlreadyRunningError` rejection.
- Keep the `idempotency_key` vs `tool_call_state.idempotency_key` clarification (`:72`) — it is the wftaskapi001 rename's context paragraph and is not re-touched here (sequencing note in that plan's row 11).

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- Frozen cite lines `234-242` are stale against HEAD (file is 106 lines); the rewrite targets the verified HEAD regions `:46,70-72,100`.

## Design decisions

- Bullet-level edits; no section restructuring.

## Alternatives considered

- Moving the contract text into `agent_03_03` only: rejected — the frozen table requires both docs updated.

## Implementation
### Target file
`docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`

### Procedure
1. Rewrite the two cited regions.
2. Re-run the docs checkers.

### Method
Direct edit of two cited regions.

### Details
- DB-ownership paragraph (`:46`) stays unchanged.

## Compatibility considerations

- Coordinate wording with rows 23/24 for identical claim-matrix phrasing.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Docs revert is data-free.

## Validation plan

- Full docs checker set.

## Completion criteria

- AC-11: the platform doc's StateStore scope matches the implemented ledger contract.

## Out of Scope

- Session/rag database sections; `tool_call_state` table description.

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
- **Workflow phase**: Phase 5 (Documentation and ADR)
- **Requirement ID**: `REQ-010`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
