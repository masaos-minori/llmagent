## Goal
Document the workflow stale-attempt recovery behavior and the new startup retention purge in the operations reference (REQ-001/REQ-003: the recovery doc currently describes neither the event prune nor any retention).

## Scope
**Release unit**: wfaudit001-full

- Covers Plan `plans/20261108-084003_wfaudit001_processed-events-never-pruned.md` row 5 only: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`.

## Assumptions
- Behavior documented is what the row 1 document implements: recovery deletes the (`task_id`, `stage_id`) event rows of attempts it marks failed; the startup purge deletes event rows of terminal tasks older than the 30-day horizon and logs its count.

## Design decisions
- Add a short operational paragraph to the workflow domain narrative (near the workflow data/operations sections, e.g. around the workflow startup material at L85-93); no new top-level section.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
State the stale-attempt recovery semantics and the startup purge for `workflow.sqlite`.

### Method
Document: at process initialization `recover_stale_attempts()` marks lease-expired running attempts `failed` and deletes the `processed_events` rows of their (`task_id`, `stage_id`) pair so a resumed stage re-executes instead of being permanently skipped; `purge_finished_workflow_events()` then deletes event rows whose task is terminal (`completed`/`failed`/`halted`) with `updated_at` older than a fixed 30-day horizon, logging the deleted count. Cross-reference db_02 for the schema-level retention narrative.

### Details
- Keep the existing physical-corruption wording untouched — this is operational (logical) recovery of stale attempts, distinct from the `no_recovery_allowed` physical policy already documented for `workflow` targets.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` per `routing.md`.

## Completion criteria
- The workflow operations narrative states recovery pruning and startup purge accurately after the code lands.

## Out of Scope
- The schema-reference retention narrative (row 4 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the recovery-purge and startup-purge narrative per Procedure/Method | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (recovery prune documented), `REQ-003` (startup purge documented)
- **Source issue**: `issues/20261107-203214_wfaudit001_processed-events-never-pruned.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084003_wfaudit001_processed-events-never-pruned.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-134201
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
