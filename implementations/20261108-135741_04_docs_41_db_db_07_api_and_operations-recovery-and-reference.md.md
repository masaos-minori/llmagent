## Goal
Document crash-recovery task-status reconciliation in the DB operations/recovery reference: recovery now reconciles the parent `tasks` row (`running` -> `failed` when no live attempt remains) in the same transaction as the attempt fails and the event prune, and reports a reconciled-task count (REQ-001/REQ-004).

## Scope
**Release unit**: wfaudit007-full

- Covers Plan `plans/20261108-084004_wfaudit007_task-status-never-reconciled.md` row 4 only: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`.

## Assumptions
- `implementations/20261108-134201_05_...` (wfaudit001) lands first: the recovery narrative this document extends already describes the attempt fail and the `processed_events` prune; this procedure appends the task-reconciliation step to that same narrative.
- Behavior documented is what `implementations/20261108-135741_01_...` implements: guarded `UPDATE tasks ... WHERE task_id=? AND status='running'` after the no-live-attempt check, inside the same recovery transaction.

## Design decisions
- Extend the existing recovery paragraphs in place (the paragraphs created by 134201_05 in this file); no new top-level section, no schema table changes — the `tasks.status` CHECK already includes `halted`/`failed`.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
State the task-reconciliation step as the final step of the stale-attempt recovery sequence.

### Method
Document: after `recover_stale_attempts()` fails lease-expired attempts and prunes their `processed_events` rows, every task whose last live attempt was just failed — still `running` with no remaining live attempt — is reconciled to `failed` in the same transaction. The recovery report counts gain a reconciled-task count `tasks_reconciled` (new) alongside the existing attempt-recovery counts. State that `halted` and `completed` tasks are never reconciled.

### Details
- Keep the physical-corruption wording (already present) untouched; reconciliation is part of the logical-recovery narrative.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` per `routing.md`.

## Completion criteria
- The recovery narrative states task reconciliation and the `tasks_reconciled` (new) count accurately after the code lands.

## Out of Scope
- Status-based report consumers (plan `UNK-02`).
- The event-prune paragraphs owned by `implementations/20261108-134201_05_...`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the task-reconciliation step and `tasks_reconciled` (new) count to the recovery narrative per Procedure/Method | Pending | — | — | |
| 2 | Run the documentation checkers (`routing.md` Tools) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (task reconciliation documented), `REQ-004` (reconciled count observable)
- **Source issue**: `issues/20261107-203220_wfaudit007_task-status-never-reconciled.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084004_wfaudit007_task-status-never-reconciled.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-135741
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
