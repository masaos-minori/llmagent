## Goal
Reconcile parent `tasks` rows after recovery: a task whose last live attempt was failed by recovery moves from `running` to `failed` in the same transaction (REQ-001/REQ-002), with the reconciled count observable in the startup report (REQ-004).

## Scope
**Release unit**: wfaudit007-full

- Covers Plan `plans/20261108-084004_wfaudit007_task-status-never-reconciled.md` row 1 only: `scripts/agent/workflow/state_store.py`.

## Assumptions
- Sequencing: the `wfaudit001` procedures (`implementations/20261108-134201_01/02/03_*`) land first — this document builds on `recover_stale_attempts` already carrying `task_id`/`stage_id` in the classified dicts and the event-row prune inside the loop.
- `update_task_status` gains a no-commit transaction-safe variant in the sibling document `20261108-135741_02_scripts_agent_workflow_task_ops.py.md`; this document calls that variant.
- `failed` is the terminal value for crash-abandoned tasks (Plan Assumptions; vocabulary member, no new literal).

## Design decisions
- Reconciliation runs after the per-attempt loop, before the single `db.commit()`, so the whole recovery (prune → attempt fails → task reconcile) is one begin-immediate transaction (Plan Design "Ordering").
- Guarded compare-and-swap per task: the UPDATE carries `AND status='running'` and is issued only when `EXISTS (SELECT 1 FROM attempts WHERE task_id=? AND status='running')` is false after the loop updates — tasks with a live-leased attempt are never touched (REQ-002).

## Alternatives considered
- Calling the existing `update_task_status` per task: rejected — it commits at `task_ops.py:82`, which would fragment the recovery transaction (Plan row 2 exists for this reason).
- Removing `tasks.status` (issue alternative, Plan `UNK-01`): rejected — the halt guard reads it.

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`

### Procedure
1. In `recover_stale_attempts`, collect the distinct `task_id` of every claimed (rowcount==1) attempt during the loop.
2. After the loop and before the commit, reconcile each collected task.
3. Extend `RecoveryReport` (L36) with a reconciled-task count and log it alongside the existing recovery counts.

### Method
1. Accumulate `reconciled_candidates: set[str]` from `item["task_id"]` in the `cursor.rowcount == 1` branch.
2. After the loop (inside `if stale:` before `db.commit()`): for each candidate, skip if a live attempt remains (`SELECT 1 FROM attempts WHERE task_id=? AND status='running'` returns a row); otherwise call the sibling document's no-commit variant with the `TASK_STATUSES` member `failed` (REQ-003 — import from `agent.workflow.models`, no literal); count rows where the guarded UPDATE actually changed a row.
3. `RecoveryReport` gains field `tasks_reconciled` (new); `logger.info` reports it next to the recovery counts (REQ-004).

### Details
- Ordering inside the transaction: event prune (wfaudit001) → attempt fails (existing) → task reconciliation (this document) — matches Plan Design.
- Reconciliation queries run on the same connection/transaction; no new connection or commit call.

## Compatibility considerations
- `RecoveryReport` gains a defaulted field; existing readers (tests, orchestrator report use) keep working.
- Tasks that legitimately finished with `halted`/`completed` are never reconciled — halt-guard behavior at `workflow_engine_adapter.py:315` is unchanged.

## Security considerations
- No new inputs; all values come from the attempts/tasks tables; parameter-bound SQL only.

## Rollback considerations
- Single revert of the commit; no schema change involved.

## Validation plan
- Reconciliation tests in `tests/agent/workflow/test_state_store.py` (extend `TestRecoverStaleAttemptsOptimisticLocking` fixtures with parent task rows): task `running` + stale attempt → `failed`; live-lease task stays `running`; `halted`/`completed`/`failed` tasks untouched; multi-attempt task (one recovered + one live) stays `running` (Plan Tests).
- Constant-usage test: the written value is the imported `TASK_STATUSES` member; out-of-vocabulary writes raise (REQ-003/`wfaudit005` behavior).
- caplog assertion: reconciliation count distinct from attempt-recovery count (REQ-004).
- Halt-guard regression in `tests/agent/test_orchestrator.py` (`_init_workflow_task` resume/reuse class, L2159+): a `halted` task is still resumable-blocked as before; a reconciled `failed` task is not treated as resumable-halted (REQ-005).
- New tests fail on HEAD (task stays `running`); `uv run pytest tests/agent/workflow/ -q`, then full `uv run pytest tests/ -q`; lint/type gates per `rules/toolchain.md`.

## Completion criteria
- After recovery, no `running` task remains whose attempts are all terminal; live tasks keep `running`; counts are logged; halt-guard behavior regression-pinned.

## Out of Scope
- The no-commit task status variant (row 2 document).
- Event-row pruning (wfaudit001 documents).
- Diagnostics surfacing reconciled-vs-failed distinction (`UNK-02`, out of plan scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-064151 | 20261109-064151 | reconcile block inside if stale before commit; RecoveryReport.tasks_reconciled; summary log |
| 2 | Add or update tests per Validation plan | Completed | 20261109-064151 | 20261109-064151 | TestRecoveryReconcilesTaskStatus (5 tests) + halt-guard regression test in test_orchestrator.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-064151 | 20261109-064151 | gates exit 0; targeted suites 310 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-064151 | 20261109-064151 | docs rows 3-4 own the doc updates N/A: doc updates owned by procedure docs 03/04 |

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
- **Requirement ID**: `REQ-001` (reconcile to `failed` in-transaction), `REQ-002` (live/halted/completed untouched), `REQ-004` (reconciliation counts observable)
- **Source issue**: `issues/20261107-203220_wfaudit007_task-status-never-reconciled.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084004_wfaudit007_task-status-never-reconciled.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-135741
- **Related target files**: `scripts/agent/workflow/state_store.py`