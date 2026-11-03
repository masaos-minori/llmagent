<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "tests/agent/test_orchestrator.py", "target_kind": "test", "seq": 19} -->

## Goal

Update `tests/agent/test_orchestrator.py` status-write assertions for the transition API and pin the halted-resume message and audit attempt number (REQ-007, REQ-009, REQ-011 / AC-6, AC-8).

## Scope

- Mocked `update_task_status` assertions (`test_orchestrator.py:2758-2896`) — expect transition-API calls instead of raw status writes.
- Halted-resume test (`:2226-2249`) and the `match="halted"` assertion (`:2116`): behavior must still pass after row 08's guard rewrite.
- Add an audit-argument assertion that `audit_stage_completed` receives `attempt_number`.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- This suite mocks `StateStore` at the boundary; the adapter (row 08) is the object under test.

## Design decisions

- Keep the existing halted-resume tests untouched in intent — they are the acceptance anchor for the `TaskTransitionError` message contract (row 02).

## Alternatives considered

- Rewriting the mocks against `task_ops` directly: rejected — the existing store-boundary mocks are this suite's stable seam.

## Implementation
### Target file
`tests/agent/test_orchestrator.py`

### Procedure
1. Update mock surfaces to the renamed/delegated methods the adapter now calls.
2. Extend the exit-status assertions with the `completed -> failed` transitional case.
3. Add the audit `attempt_number` assertion to the stage-completion orchestration test.

### Method
Direct edit of mock expectations plus one new assertion block.

### Details
- The suite is 3211 lines and high-churn (14 edits/30d); limit changes to the cited regions.

## Compatibility considerations

- Depends on rows 06/08 method names landing first.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Revert with rows 06/08.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py -v`.

## Completion criteria

- Orchestrator-level tests prove claim semantics, halted guard, and attempt-number propagation (AC-6, AC-8).

## Out of Scope

- Engine-internal numbering (row 14).

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
- **Workflow phase**: Phase 4 (Engine, adapter, and audit correlation)
- **Requirement ID**: `REQ-007`, `REQ-009`, `REQ-011`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `tests/agent/test_orchestrator.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/tool_audit.py`, `tests/agent/test_tool_audit.py`

## Implementation Result (2026-11-03: superseded by upstream)

This wfrecovery001 procedure implemented an attempt-number-based recovery state
machine. Upstream (`origin/master`) superseded this design with a lease-based
stale-attempt recovery (wflease001, AC-2/AC-4/AC-5/AC-7). The batch was
therefore NOT merged into `origin/master`.

- **Decision (2026-11-03):** full supersession. Every one of the ~32 code files
  the batch touched was rewritten or replaced by upstream (lease columns on
  `attempts`, a `disable_foreign_keys` migration-runner rebuild, fail-closed
  tool audit, schema manifest bumped to workflow version 1.4.0). No substantive
  delta survives.
- **Action:** the 3-way merge (`git merge --no-commit backup-batch` onto branch
  `rederive` from `origin/master`) was aborted (`git merge --abort`), returning
  to a clean `origin/master` at `7d6744fd`.
- **Residual:** `attempt_number` / `CHECK` are entangled with upstream's
  lease/local-retry design and cannot be integrated as a clean, bounded
  addition; reintroducing them would fight the lease architecture.
- **Outcome:** divergent code is not integrated. The batch remains on
  `backup-batch` as a superseded historical record. All 26 procedures were
  executed and marked Completed on `backup-batch`; this note records the
  supersession.

