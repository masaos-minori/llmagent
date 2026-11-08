## Goal
Document crash-recovery task-status reconciliation in the agent platform-databases doc: after `recover_stale_attempts()` fails a task's last live attempt, the owning `tasks` row is reconciled from `running` to `failed` in the same transaction, and the reconciled count is observable (REQ-001/REQ-002/REQ-004).

## Scope
**Release unit**: wfaudit007-full

- Covers Plan `plans/20261108-084004_wfaudit007_task-status-never-reconciled.md` row 3 only: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`.

## Assumptions
- Behavior documented is what row 1 implements: after attempt recovery, each task that had a recovered attempt, is still `running`, and has no remaining live attempt is written to `failed`; `halted`, `completed`, and live-leased tasks are untouched.
- `failed` is the terminal value used (vocabulary member from `wfaudit005`); no new status value appears in the doc.

## Design decisions
- Add the reconciliation narrative to the existing `StateStore`/`begin_stage_if_new` operational bullets (verification finding 2026-11-09: this doc has no stale-recovery
  narrative yet — the recovery narrative is in `docs/41_db/db_07` via `implementations/20261108-134201_05_...`, landed earlier); no new top-level section.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`

### Procedure
State task-status reconciliation as part of the workflow stale-recovery description.

### Method
Document: after recovery fails lease-expired attempts (and prunes their `processed_events` rows), every task whose last live attempt was just failed — still `running` with no remaining live attempt — is reconciled to `failed` in the same transaction. The report counts include a reconciled-task count `tasks_reconciled` (new) alongside the existing `recovered` and `still_live` counts. State that `halted` and `completed` tasks are never reconciled and resume halt-guard semantics are unchanged.

### Details
- Name the new count `tasks_reconciled` (new) exactly as row 1 declares it.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` per `routing.md`.

## Completion criteria
- The workflow persistence narrative states task reconciliation and the `tasks_reconciled` (new) count accurately after the code lands.

## Out of Scope
- Status-based report consumers (plan `UNK-02`).
- The `processed_events` prune narrative (owned by `implementations/20261108-134201_05_...`, landed earlier).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the task-reconciliation narrative and `tasks_reconciled` (new) count per Procedure/Method | Completed | 20261109-064151 | 20261109-064151 | reconciliation bullet added after begin_stage_if_new bullet (Operational Notes) |
| 2 | Run the documentation checkers (`routing.md` Tools) | Completed | 20261109-064151 | 20261109-064151 | docs quality/structure/consistency(db,agent) all pass |

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
- **Requirement ID**: `REQ-001` (task reconciliation documented), `REQ-002` (untouched states), `REQ-004` (reconciled count)
- **Source issue**: `issues/20261107-203220_wfaudit007_task-status-never-reconciled.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084004_wfaudit007_task-status-never-reconciled.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-135741
- **Related target files**: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`