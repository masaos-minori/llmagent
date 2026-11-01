<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md", "target_kind": "documentation", "seq": 24} -->

## Goal

Rewrite the state-semantics, resume, and startup-recovery sections of `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` to the implemented contract (REQ-010 / AC-11).

## Scope

- `### Workflow State Semantics` (`:31`) gains the five-status vocabulary and the transition matrix summary.
- `### Resuming Existing Tasks` (`:35-40`): claim contract — `pending`/`failed` claimable, `running`/`completed` rejected, `halted` still raises the `RuntimeError` naming `halted` (`:40` wording stays compatible).
- `### Startup Recovery` (`:143-145`): replace "it never changes the persisted task status" with the atomic attempt+task failure semantics (Plan UNK-03 owner decision).
- Task Status Transitions table (`:74-90`) and Operational Notes (`:149-150`) reconciled with the matrix (cancellation-stays-`halted` policy unchanged).

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- Docs are written in English (`skills/DESIGN.md` Output language); the frozen cite's `started (not completed)` phrase no longer exists in this file at HEAD — the rewrite targets the actual HEAD text, cite drift noted.

## Design decisions

- Section-level edits only; the doc's structure and checker-relevant headings stay intact.

## Alternatives considered

- Regenerating the whole doc: rejected — unnecessary churn and churn-risk (23 edits/30d).

## Implementation
### Target file
`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Procedure
1. Apply the three section rewrites plus the table reconciliation.
2. Re-run the docs checkers and record any Japanese/content-policy findings.

### Method
Direct edit of four cited regions.

### Details
- `agent_04_03` (row 25) states the StateStore side of the same contract; the two docs must use identical wording for the claim matrix.

## Compatibility considerations

- Row 23 ADR amendment lands in the same phase so invariants and flow doc agree.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Docs revert is data-free; pair with rows 23/25.

## Validation plan

- Full docs checker set (as row 23 lists).

## Completion criteria

- AC-11: the flow doc describes claim, ledger, and recovery exactly as implemented.

## Out of Scope

- Approval-policy sections; retry-config reference tables.

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
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`
