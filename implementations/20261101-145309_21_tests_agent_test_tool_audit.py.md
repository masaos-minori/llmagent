<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "tests/agent/test_tool_audit.py", "target_kind": "test", "seq": 21} -->

## Goal

Add the `stage_completed` attempt-number test to `tests/agent/test_tool_audit.py` (REQ-009 / AC-8).

## Scope

- New test class asserting `audit_stage_completed` writes `attempt_number` into the event payload (no `stage_completed` test exists at HEAD).

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- Fixture pattern follows `_make_ctx` (`test_tool_audit.py:63`) and the existing audit-event capture style.

## Design decisions

- Assert the exact payload key/value alongside the existing `workflow_id`/`task_id` keys.

## Alternatives considered

- Extending an approval-event test: rejected — separate event type, separate class keeps ADR INV-11 tests untouched.

## Implementation
### Target file
`tests/agent/test_tool_audit.py`

### Procedure
1. Add `TestAuditStageCompletedAttemptNumber` following the existing capture pattern.

### Method
Direct edit; additive test class.

### Details
- Payload source is row 09; this file tests only the emitted event.

## Compatibility considerations

- ADR test table already cites this file for INV-11 (unchanged).

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Delete the class.

## Validation plan

- `uv run pytest tests/agent/test_tool_audit.py -v`.

## Completion criteria

- The audit event contract for `stage_completed` is test-pinned with `attempt_number` (AC-8).

## Out of Scope

- Adapter-side propagation tests (row 19).

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
- **Requirement ID**: `REQ-009`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `tests/agent/test_tool_audit.py`, `scripts/agent/tool_audit.py`, `scripts/agent/workflow_engine_adapter.py`
