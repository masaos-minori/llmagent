## Goal
Make `tasks.status` reflect reality after recovery: when `recover_stale_attempts` fails a task's last live attempt, write a terminal task status from the declared vocabulary in the same transaction — and keep the halt-guard behavior intact.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/agent/workflow/state_store.py` — after the recovery loop, reconcile owning `tasks` rows whose attempts are all terminal: write `failed` (vocabulary value from `wfaudit005`) for tasks left `running` by a crash.
  - `scripts/agent/workflow/task_ops.py` — reconciliation helper (or reuse `update_task_status`, already vocabulary-validated after `wfaudit005`).
  - Tests: crash-residual `running` task becomes `failed` after recovery; halted and completed tasks untouched; a task with a live lease untouched.
- **Out-of-Scope**:
  - Removing the `tasks.status` column (the issue offers this alternative — rejected in Design: the halt guard reads it).
  - New consumers/reports by status (session diagnostics changes) — observable only after consumers exist; recorded as `UNK-02`.
  - The event-row prune in the same transaction (planned as `wfaudit001`, landed first).
- **Dependencies**: After `wfaudit005` (must write a declared `TASK_STATUSES` value) and after `wfaudit001` (shares the `recover_stale_attempts` transaction; 001's structure is extended, not rewritten).

## Background
`recover_stale_attempts` (`scripts/agent/workflow/state_store.py:190-248`) updates only `attempts`; the only `UPDATE tasks` writer is `task_ops.update_task_status` (L68-74). The engine writes terminal statuses normally (`workflow_engine.py:213-224`), but a process that dies mid-run never reaches those writes, so crash-residual tasks stay `running` forever and are indistinguishable from live tasks in every report (`scripts/agent/diagnostic_store.py` never reads the tasks table; task counts in `task_ops.py:111,121` filter by `session_id` only). The only `tasks.status` reader today is the resume halt guard `if _fetched.status == "halted"` (`workflow_engine_adapter.py:315`). The issue's "completed never written" claim was corrected during validation — the surviving gap is exactly the recovery path. Evidence: issue `## Adversarial Validation`.

## Problem
A crashed task's row permanently reads `running`: reports cannot distinguish crashed from live tasks, and any future resume guard or reconciliation built on status starts from wrong data.

## Reason for Change
Recovery already knows the truth (it just failed the task's last attempt); leaving the parent row stale contradicts the status vocabulary declared in `wfaudit005` and blocks any status-based reporting.

## Implementation Intent
Extend the recovery transaction with a parent-row reconciliation step: for each task that had at least one recovered attempt, check whether any non-terminal attempt remains live; if none and the task is still `running`, write `failed` via the vocabulary-validated `update_task_status`. Do not introduce new status values and do not touch halted/completed tasks.

## Requirements
- `REQ-001`: After recovery marks an attempt `failed`, every owning task with status `running` and no remaining live (non-terminal) attempts is updated to `failed` in the same transaction.
- `REQ-002`: Tasks with a live-leased running attempt, and tasks already `halted`/`completed`/`failed`, are never changed by reconciliation.
- `REQ-003`: The written value comes from `TASK_STATUSES` (`wfaudit005` constants) — no new literal.
- `REQ-004`: Reconciliation counts are logged alongside recovery counts (observable in the startup report).
- `REQ-005`: New tests pin `REQ-001`/`REQ-002`/`REQ-004`; the halt-guard behavior (`workflow_engine_adapter.py:315`) is regression-tested against a reconciled task (a `failed` task must not be resumable as `halted`).

## Implementation Target Files
**Freeze status**: Draft

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/state_store.py` | Modify | Add post-loop reconciliation to `recover_stale_attempts`: set of recovered task_ids -> conditional `UPDATE tasks SET status='failed' WHERE task_id=? AND status='running'` after live-attempt check | `REQ-001`/`REQ-002`/`REQ-004` | Recovery touches only attempts (grep `UPDATE tasks`) | `tests/agent/workflow/test_state_store.py`, `test_workflow_state_store.py` | `Verified` |
| `scripts/agent/workflow/task_ops.py` | Reference/possible Modify | Reuse `update_task_status` (validated in `wfaudit005`) or add a guarded variant used in-transaction | `REQ-001`/`REQ-003` | `task_ops.py:68-74` | `tests/agent/workflow/` | `Verified` |
| `scripts/agent/workflow/workflow_engine.py` | Reference | Confirmed no-change: normal-run writes already terminal (L213-224) | Regression context | Step 2 validation | existing engine tests | `Verified` |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Modify | State the recovery reconciliation behavior for `tasks.status` | `REQ-001` | Turn/task status descriptions exist (wfreview007 precedent) | docs checkers | `Verified` |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | Recovery section: attempt fail + task reconciliation | `REQ-001`/`REQ-004` | Recovery doc describes attempts only | docs checkers | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/models.py` | `TASK_STATUSES` / `ATTEMPT_STATUSES` constants from `wfaudit005` | `REQ-003` |
| `scripts/agent/workflow_engine_adapter.py` | Halt guard (L315) semantics — reconciled `failed` tasks and resume behavior | `REQ-005` |
| `plans/20261108-084003_wfaudit001_processed-events-never-pruned.md` | The shared recovery transaction shape this plan extends | `REQ-001` |

## Acceptance Criteria
- `REQ-001`: Test: task `running` + one stale attempt -> after recovery, task `failed`.
- `REQ-002`: Tests: live-lease task stays `running`; `halted` task untouched; `completed` task untouched.
- `REQ-003`: The reconciliation SQL status value is the imported `TASK_STATUSES` member (test asserts the constant is used, and out-of-vocabulary writes raise per `wfaudit005`).
- `REQ-004`: Startup log contains reconciliation count distinct from attempt-recovery count.
- `REQ-005`: New tests fail on HEAD (stays `running`) and pass after; halt-guard test confirms a `halted` task is still resumable and a reconciled `failed` task is not treated as resumable-halted.

## Tests
- Recovery reconciliation unit tests in `tests/agent/workflow/test_state_store.py` (extend recovery fixtures with parent task rows).
- Multi-attempt case: task with one recovered + one live-leased attempt stays `running`.
- Halt-guard regression test in `tests/agent/` adapter tests.
- Log-observability assertion (caplog) for the reconciliation count.

## Documentation Impact
- `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` — task-status lifecycle description gains the recovery path.
- `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` — recovery behavior list extended.
- Run docs checkers for domains agent/db per `routing.md`.

## Assumptions
- `failed` is the correct terminal value for a crash-abandoned task (vocabulary member; no separate `abandoned` value is introduced). Owner can veto in favor of a distinct value — `wfaudit005` vocabulary review point.
- "No remaining live attempts" is determined by `EXISTS (SELECT 1 FROM attempts WHERE task_id=? AND status='running')` evaluated after the recovery updates, inside the same transaction.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | whether the owner prefers removing `tasks.status` instead (issue's alternative) | consumer demand unclear | rejected in Design for now (halt guard reads status); revisit when status consumers appear | `False` |
| `UNK-02` | whether diagnostics/reporting should surface reconciled-vs-failed distinction | product decision | follow-up issue if desired; out of scope here | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/state_store.py` | Modify | startup recovery for every service boot | 6 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/task_ops.py` | Modify (possible) | task status writers | 3 | N/A | not applicable (rsynced) |
| docs (2 files) | Modify | docs only | N/A | N/A | not applicable |

## Design
**Conditional, idempotent reconciliation.** The write is `UPDATE tasks SET status=?, updated_at=? WHERE task_id=? AND status='running'` guarded by the no-live-attempt EXISTS check — a compare-and-swap mirroring the attempt-level discipline already in `recover_stale_attempts` (L216-224). Because it runs only for tasks that had a recovered attempt, its cost is bounded by the recovery set.

**Why not delete the column:** the resume halt guard (`workflow_engine_adapter.py:315`) reads `tasks.status`; reports and future resume semantics need the column. Keeping the column honest is cheaper than removing a working reader.

**Ordering within the shared transaction:** event prune (`wfaudit001`) → attempt fails (existing) → task reconciliation (this plan). All in the same begin-immediate transaction so a crash mid-recovery never leaves a `failed` attempt under a `running` task.

## Implementation steps
1. **Phase 1: Reconciliation (`REQ-001`-`REQ-004`).** Extend `recover_stale_attempts` with the guarded parent-row update and count logging; add tests.
2. **Phase 2: Regression + docs (`REQ-005`).** Halt-guard regression test; docs updates; docs checkers.

### Release units
**Unit**: wfaudit007-full | **Phases**: 1, 2 | **Reason**: one behavior change to the recovery transaction plus its regression/doc wrap.

## Validation plan
- `uv run pytest tests/agent/workflow/ -q` after Phase 1; full `uv run pytest tests/ -q` before completion.
- New tests fail on HEAD (task stays `running`).
- Production check after deploy: `SELECT status, COUNT(*) FROM tasks GROUP BY status;` — `running` count should drop to live tasks only after the first restart.
- Lint/type gates per `rules/toolchain.md`; docs checkers after Phase 2.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Reconciling a task whose attempt was recovered but whose other process is mid-write | Low | Medium | EXISTS live-attempt check runs after the compare-and-swap; same transaction prevents interleaving |
| A reconciled `failed` task breaks a future resume expectation | Low | Low | Halt guard only special-cases `halted`; regression test pins both behaviors |
| Recovery transaction grows (prune + fails + reconcile) and holds the write lock longer | Low | Low | Recovery set is bounded by stale attempts; all statements are indexed by PK |

## Execution Status
### Execution Status
| Work Item | Status | Owner | Started | Completed | Notes |
|---|---|---|---|---|---|
| Phase 1: reconciliation | Planned | engineer | | | |
| Phase 2: regression + docs | Planned | engineer | | | |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Work Item | Type | Link | Created |
|---|---|---|---|

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203220_wfaudit007_task-status-never-reconciled.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084004
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Problem (permanently running) | `scripts/agent/workflow/state_store.py` | Running task with no live attempts -> `failed` | reconciliation tests |
| `REQ-002` | Plan Design (safety) | same | live/halted/completed untouched | guard tests |
| `REQ-003` | Dependency on `wfaudit005` | `models.py` constants | vocabulary value only | constant-usage test |
| `REQ-004` | Issue Validation Expectations | logging | count observable | caplog test |
| `REQ-005` | Issue Testing Expectations | tests | fail on HEAD | pytest |

## Notes
- Source verified against HEAD `926dbc109`; the issue's central "completed never written" claim was corrected in the issue's `## Adversarial Validation` — the surviving gap is recovery-only.
- Sequence: `wfaudit005` -> `wfaudit001` -> this plan (shared recovery transaction).
