<!-- workitem: {"kind":"implementation-procedure","batch_id":"20261101-145309","seq":7,"source_plan":"plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md","source_issue":null,"source_review":null,"target_file":"scripts/agent/workflow/workflow_engine.py","generated_at":"2026-11-01T14:53:09Z","schema_version":"1.0","schema_hash":"488513b688446992"} -->

## Goal

Make `scripts/agent/workflow/workflow_engine.py` claim tasks through the transition API, run retries from the persisted attempt number with a budget that survives restarts, and expose the current attempt number for audit correlation (REQ-007, REQ-009 / AC-6, AC-8).

## Scope

- `run()` (`workflow_engine.py:162-186`): replace the unconditional status writes (`:175,181,184,186`) with `claim_task_running` + terminal transitions via `StateStore` delegates.
- Retry loop: replace the in-memory `attempt = 0` (`:202`) with the persisted current attempt number from the canonical start (row 05) and enforce `max_attempts` across process restarts.
- Expose `current_attempt_number` on the engine for the adapter (row 08).

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- `begin_stage_if_new` (`:264`) and `finish_attempt` sites (`:280,291,300`) keep their call shape through Phase 3; this row only wires claim/numbering.

## Design decisions

- Claim happens before any stage runs; `running`/`completed`/`halted` tasks raise (`StageAlreadyRunningError` semantics for a live task, `TaskTransitionError` otherwise) instead of silently re-entering (`:172-176` today reuses any existing task).
- Budget rule: attempts already persisted for the (task, stage) pair count against `max_attempts`, so a restarted turn cannot restart a stage indefinitely.

## Alternatives considered

- Resetting numbering per process (current behavior): rejected — REQ-007 requires the budget to span restarts, which in-memory counters cannot provide.

## Implementation
### Target file
`scripts/agent/workflow/workflow_engine.py`

### Procedure
1. Insert the claim call at the top of `run()`; remove the existing-task status-agnostic reuse.
2. Read the persisted attempt number from the row-05 start result instead of `attempt = 0` (`:202`).
3. Store the current attempt number on the engine instance after each stage start.
4. Route terminal writes through `transition_task_status`.

### Method
Direct edit; control-flow rewrite of `run()` and `_execute_stage_with_retry`.

### Details
- `event_id` composition (`:262`) is unchanged; ledger semantics come from row 05.
- `WorkflowHaltError`/`WorkflowTimeoutError` (`:77,81`) stay engine-local.

## Compatibility considerations

- Row 14 rewrites the engine tests that assume in-memory numbering (`test_workflow_engine.py:111-161,186-206`); row 19 updates orchestrator-level assertions.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.

## Rollback considerations

- Engine revert alone is safe if rows 05/06 are reverted with it (the claim and numbering APIs they call are the changed surface).

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py -v` (row 14).
- `uv run pytest tests/agent/workflow/test_workflow_recovery.py -v` (row 17: resume after failed attempts continues numbering).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- A task can only enter `running` via claim; stage attempts continue across restarts and respect `max_attempts`; `current_attempt_number` is readable after each stage (AC-6, AC-8).

## Out of Scope

- Adapter resume guard (row 08); audit payload (row 09).

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
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`
