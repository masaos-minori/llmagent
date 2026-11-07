## Goal
Make recovery reconcile `processed_events` so a recovered stage is not permanently skipped: delete the event rows belonging to recovered attempts, add a retention purge for the workflow tables, and remove the false recovery claims from the code comments.

## Priority
High

## Scope
- **In-Scope**:
  - `scripts/agent/workflow/state_store.py` — `recover_stale_attempts`: delete `processed_events` rows for each recovered attempt inside the same transaction; add a `purge_finished_events(retention_days)`-style purge for `processed_events` (and the finished-task rows it references) called at startup.
  - `scripts/agent/workflow/idempotency_ops.py` — correct the misleading comment block (L43-46) claiming recovery "removes their event IDs".
  - Retention horizon constant (named constant, config-free, mirroring the wflease001 precedent) documented in code.
  - Tests: recovery-then-resume re-execution test; purge test; comment-claim removal verified.
  - Docs: `docs/41_db` workflow-table retention story.
- **Out-of-Scope**:
  - The adapter "crashed tasks will not produce duplicate stage executions" comment — verified no longer present at HEAD; nothing to correct there.
  - `tasks` status reconciliation after recovery (separately planned as `wfaudit007`, same transaction, sequenced after this plan).
  - Changing the event-key format (`task_id:stage_id:attempt`) itself.
- **Dependencies**: After `wfaudit005` (the reconciliation/purge touches status-guarded writes using the declared vocabulary). Shares the `recover_stale_attempts` transaction with `wfaudit007` — land 001 before 007. Touches the same `begin_stage_if_new` call path as `wfaudit015` (facade routing) — keep this plan's edits at the ops level so 015's facade migration can wrap them.

## Background
The engine keys each stage attempt with `event_id = f"{task_id}:{stage_id}:{attempt}"` (`scripts/agent/workflow/workflow_engine.py:311`) and skips the stage when `begin_stage_if_new` returns None ("skipped (already processed)", L321-325). `recover_stale_attempts` (`scripts/agent/workflow/state_store.py:190-248`) marks orphaned running attempts `failed` but never touches `processed_events`; no `DELETE FROM processed_events` exists anywhere in `scripts/` (grep-verified at HEAD). The comment block in `begin_stage_if_new` (`scripts/agent/workflow/idempotency_ops.py:43-46`) claims recovery detects stale attempts and "removes their event IDs" so they run again — false. Consequence: a resumed task re-running attempt N collides with the surviving event row and the stage is permanently skipped. The dedup domain shows the retention precedent (`DedupStore.purge_expired`, `scripts/shared/mcp_dedup.py:313`). All verified in the issue's `## Adversarial Validation`.

## Problem
Crash recovery currently cannot re-execute a recovered stage: the event row survives, so every later resume skips it. Meanwhile rows accumulate forever in `processed_events` (and their task parents), with no retention story for the workflow tables.

## Reason for Change
The recovery feature's stated purpose ("so they run again") is documented but not implemented — a semantic bug with user-visible effect (resumed tasks silently missing stages), and unbounded table growth on a long-lived production database.

## Implementation Intent
Keep recovery's compare-and-swap structure intact and extend its transaction: when an attempt is marked failed by recovery, delete the matching `processed_events` row by deterministic key (`task_id:stage_id:attempt` derived from the attempt row). Add a startup purge that deletes event rows whose task has a terminal status older than a named retention constant. Correct the comment to describe the real behavior after the change.

## Requirements
- `REQ-001`: On successful recovery of an attempt (the rowcount==1 compare-and-swap branch), the matching `processed_events` row (`event_id = {task_id}:{stage_id}:{attempt}`) is deleted in the same transaction.
- `REQ-002`: A resumed run after recovery executes the recovered stage again (no "skipped (already processed)" for that attempt).
- `REQ-003`: A startup purge deletes `processed_events` rows whose owning task is in a terminal status (`completed`/`failed`/`halted` from `wfaudit005`'s vocabulary) with `updated_at` older than a named retention constant; it runs once at process initialization next to `recover_stale_attempts` (`scripts/agent/orchestrator.py:92` call site region).
- `REQ-004`: The misleading comment block in `begin_stage_if_new` (`idempotency_ops.py:43-46`) is replaced with an accurate description of the recovery/prune behavior.
- `REQ-005`: New tests pin REQ-001-REQ-004; purge counts are logged observably (count deleted, mirroring recovery's report).

## Implementation Target Files
**Freeze status**: Draft

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/state_store.py` | Modify | Recovery loop (L206-240): after the compare-and-swap UPDATE succeeds, `DELETE FROM processed_events WHERE event_id=?` built from the attempt's task/stage/attempt identity; add `purge_finished_workflow_events()` | `REQ-001`/`REQ-003` | No DELETE exists (grep); recovery structure verified | `tests/agent/workflow/test_state_store.py`, `test_workflow_state_store.py` | `Verified` |
| `scripts/agent/workflow/idempotency_ops.py` | Modify | Replace false comment block (L43-46) with accurate recovery description | `REQ-004` | Comment claims event-ID removal that does not happen (Step 2 validation) | n/a (comment) | `Verified` |
| `scripts/agent/orchestrator.py` | Modify | Call the startup purge after `recover_stale_attempts` (L92 region) | `REQ-003` | Recovery is already called there once per process start | `tests/agent/test_orchestrator.py` | `Verified` |
| `scripts/agent/workflow/attempt_ops.py` | Modify | Ensure recovered attempt dicts expose the identity needed to rebuild the event key (task_id/stage_id already selected by `_classify_running_attempts`; extend the selected columns if missing) | `REQ-001` | `state_store.py:258` classification query column set | `tests/agent/workflow/` | `Verified` |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Modify | Add the retention/purge behavior to the `processed_events` table row | `REQ-003` | Table documented with no retention | docs checkers | `Verified` |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | State that recovery now prunes event rows and describe the startup purge | `REQ-001`/`REQ-003` | Recovery doc currently describes attempts only | docs checkers | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow/workflow_engine.py` | Event-key construction (L311) and skip path (L321-325) the prune must unblock; lease/retry semantics around attempts | `REQ-001`/`REQ-002` |
| `scripts/agent/workflow/models.py` | `AttemptRecord` fields available in the recovery loop | `REQ-001` |
| `scripts/shared/mcp_dedup.py` | `purge_expired` precedent (L313) for purge shape and logging | `REQ-003` |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | No-migration policy context for retention docs | Documentation Impact |

## Acceptance Criteria
- `REQ-001`: Test: running attempt + event row for the same key; run recovery; both the attempt is `failed` and the event row is gone; a non-recovered (live-lease) attempt's event row survives.
- `REQ-002`: Integration test: after recovery, re-running the stage through `begin_stage_if_new` returns an `AttemptRecord` (not None) — no permanent skip.
- `REQ-003`: Purge test: terminal task older than the horizon → its event rows deleted; recent terminal task and running task untouched; deleted count logged.
- `REQ-004`: `grep -n "removes their event IDs" scripts/` returns nothing; replacement comment matches implemented behavior.
- `REQ-005`: New tests fail on HEAD (row survives / no purge) and pass after; full `tests/agent/` suite green.

## Tests
- Recovery-prune unit tests in `tests/agent/workflow/test_state_store.py` (extend existing recovery test fixtures).
- Resume re-execution test through `begin_stage_if_new`.
- Purge boundary tests (older/newer than horizon, terminal vs running tasks).
- Existing lease semantics tests (`test_workflow_state_store.py`) stay green.

## Documentation Impact
- `docs/41_db/db_02_architecture_and_schema-schema-reference.md` — `processed_events` row gains its retention behavior.
- `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` — recovery section updated (event prune + startup purge).
- Run docs checkers for domain db per `routing.md`.

## Assumptions
- Deleting the event row for a recovered attempt is safe because the attempt is already terminal (`failed`) and the engine assigns new event IDs by attempt number; re-execution uses the same attempt number only on a fresh resume (validated by the resume flow through `_init_workflow_task`).
- Purging events of terminal tasks does not break resume: resume only operates on tasks with live attempts, not terminal ones (halt guard reads `halted` status — a halted task's events are retained until the horizon passes).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | retention horizon value (candidate: 30 days, mirroring dedup retention) and whether it should be config-driven | owner preference | named constant now (wflease001 precedent: constants before configuration); revisit if ops demand config | `False` |
| `UNK-02` | whether terminal `tasks`/`attempts` rows themselves should also be purged (issue asks for "a retention story for the workflow tables" — this plan covers events + their task rows via the FK; attempts cascade via `ON DELETE CASCADE` only if tasks are deleted) | scope of purge target tables | decide at implementation: delete tasks older than horizon (cascade removes attempts/events) OR events-only | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/state_store.py` | Modify | recovery + startup path | 6 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/idempotency_ops.py` | Modify | comment only (behavior via state_store) | 2 | N/A | not applicable (rsynced) |
| `scripts/agent/orchestrator.py` | Modify | process initialization | 8 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow/attempt_ops.py` | Modify | classification query columns | 1 | N/A | not applicable (rsynced) |
| docs (2 files) | Modify | docs only | N/A | N/A | not applicable |

## Design
**Prune inside the existing compare-and-swap.** Recovery already logs per-attempt success (rowcount==1). The DELETE runs only in that branch, keyed by the deterministic event format rebuilt from the attempt row (`task_id`, `stage_id`, attempt number — `_classify_running_attempts` must select the columns needed; extend its SELECT, do not guess). Same transaction as the attempt UPDATE, preserving the begin-immediate discipline the surrounding code documents.

**Startup purge, not a scheduler.** One purge call after `recover_stale_attempts` at orchestrator init (orchestrator.py:92 region) mirrors the "called once during process initialization" convention already documented for recovery. Retention horizon is a named module constant (precedent: `_LEGACY_STALE_AGE_SEC`, wflease001 constant policy). Purge target: `processed_events` rows whose task is terminal and older than the horizon (`UNK-02` decides whether task rows are deleted too; the FK `ON DELETE CASCADE` makes the cascade path available if tasks are purged).

**Comment correction.** The `begin_stage_if_new` comment block is replaced with a statement of the real contract: processed means started; recovery prunes rows for attempts it fails.

## Implementation steps
1. **Phase 1: Recovery prune (`REQ-001`, `REQ-002`, `REQ-004`).** Extend the recovery transaction with the event DELETE; fix the comment; add prune/resume tests.
2. **Phase 2: Startup purge (`REQ-003`).** Implement the purge + orchestrator wiring + horizon constant + tests.
3. **Phase 3: Documentation.** Update the two `docs/41_db` files; run docs checkers.

### Release units
**Unit**: wfaudit001-full | **Phases**: 1, 2, 3 | **Reason**: the semantic fix (no permanent skip) and its retention story ship together; a prune without purge leaves unbounded growth, a purge without prune leaves the bug.

## Validation plan
- `uv run pytest tests/agent/workflow/ -q` after each phase; full `uv run pytest tests/ -q` before completion.
- New tests must fail on HEAD (event survives recovery; no purge exists).
- Production observability: after deploy, `SELECT COUNT(*) FROM processed_events;` before/after first restart to confirm the purge runs and reports its count in logs.
- Lint/type gates per `rules/toolchain.md`; docs checkers after Phase 3.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Deleting an event row for an attempt that is actually still owned by a live process | Low | High (duplicate stage execution) | DELETE only inside the rowcount==1 branch, which already proves the attempt was orphaned (compare-and-swap pinned to owner/lease state) |
| Purge horizon too short removes events a long-paused resume still needs | Low | Medium (stage re-executes for a terminal task — but terminal tasks are not resumable) | Resume operates on non-terminal tasks; halted-task guard verified in Step 2; horizon constant generous (30d) |
| `_classify_running_attempts` lacks the attempt-number column needed to rebuild the key | Medium | Low (implementation detail) | Inspect the SELECT at implementation time; extend columns (target-file row covers it) |

## Execution Status
### Execution Status
| Work Item | Status | Owner | Started | Completed | Notes |
|---|---|---|---|---|---|
| Phase 1: recovery prune | Planned | engineer | | | |
| Phase 2: startup purge | Planned | engineer | | | |
| Phase 3: documentation | Planned | engineer | | | |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Work Item | Type | Link | Created |
|---|---|---|---|

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203214_wfaudit001_processed-events-never-pruned.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084003
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Problem | `scripts/agent/workflow/state_store.py` | Recovered attempt's event row deleted in-transaction | recovery prune test |
| `REQ-002` | Issue Summary ("not permanently skipped") | recovery + `begin_stage_if_new` path | Resume re-executes | resume integration test |
| `REQ-003` | Issue Required Changes (retention) | state_store + `scripts/agent/orchestrator.py` | Purge with horizon, logged | purge boundary tests |
| `REQ-004` | Issue Problem (false claims) | `scripts/agent/workflow/idempotency_ops.py` | Comment accurate | grep assertion |
| `REQ-005` | Issue Testing Expectations | tests | Fail on HEAD, pass after | pytest |

## Notes
- The adapter comment the issue cites was already removed (verified at HEAD `926dbc109`, likely by `dee33ce7b`) — only the `idempotency_ops.py` comment remains, per the issue's Adversarial Validation.
- Sequence: `wfaudit005` (vocabulary) → this plan → `wfaudit007` (task-status reconciliation in the same recovery transaction).
