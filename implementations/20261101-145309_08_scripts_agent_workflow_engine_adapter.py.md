<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "scripts/agent/workflow_engine_adapter.py", "target_kind": "source", "seq": 8} -->

## Goal

Route `scripts/agent/workflow_engine_adapter.py` status writes through the transition API, keep the halted-resume guard behavior, and pass the persisted attempt number to `audit_stage_completed` (REQ-007, REQ-009 / AC-6, AC-8).

## Scope

- Resume guard (`workflow_engine_adapter.py:279-281`): replace the local `halted` check with the same claim contract (delegating to row 03 semantics); message keeps containing `halted` so `tests/agent/test_orchestrator.py:2116` still matches.
- Exit-status writes: `_status_for_exit` (`:49-59`) results are written via `transition_task_status` at the halted site (`:204`) and `_record_exit_status` (`:224-240`, write at `:235`), including the transitional `completed -> failed` edge.
- Audit call (`:375`): pass `attempt_number=engine.current_attempt_number`.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- Cancellation is recorded `halted` (docs `agent_03_03:83,88`); that vocabulary choice is unchanged by this Plan.

## Design decisions

- The adapter stops composing its own status SQL paths and only calls `task_ops` transitions exposed through `StateStore`.
- `attempt_id=turn_id` at `:353` (tool-loop audit correlation) is explicitly out of this Plan's scope (it belongs to the lease plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` territory).

## Alternatives considered

- Keeping the guard as a local `if status == "halted"`: rejected — two guards on one contract drift (REQ-007 names one contract).

## Implementation
### Target file
`scripts/agent/workflow_engine_adapter.py`

### Procedure
1. Replace `:279-281` with a call that raises `RuntimeError` (message names `halted`) for `halted`, `TaskTransitionError` for `running`/`completed`, and claims `pending`/`failed` via `claim_task_running`.
2. Convert the two status-write sites to `transition_task_status` calls.
3. Add the `attempt_number` argument to the `audit_stage_completed` call at `:375`.

### Method
Direct edit at four cited sites.

### Details
- Halted-then-cancelled repeat writes: the transition matrix makes a second `running -> halted` on a `halted` task raise — the adapter must not swallow it silently; row 19 pins the expected test outcome.

## Compatibility considerations

- Row 21 tests the audit payload change; row 19 keeps the orchestrator mock assertions consistent.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Adapter changes are independent of schema changes and revert cleanly with row 07.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py -v` and `uv run pytest tests/agent/test_tool_audit.py -v`.
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- Adapter status writes equal the transition matrix; halted-resume still raises a `RuntimeError` naming `halted`; `stage_completed` audit carries the persisted attempt number (AC-6, AC-8).

## Out of Scope

- `attempt_id=turn_id` tool-loop correlation (`:353`); lease/stale-attempt semantics (wflease001 plan).

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
- **Requirement ID**: `REQ-007`, `REQ-009`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/tool_audit.py`, `tests/agent/test_orchestrator.py`
