## Goal
Document the new retention behavior of `processed_events` (REQ-003: the workflow tables now have a retention story).

## Scope
**Release unit**: wfaudit001-full

- Covers Plan `plans/20261108-084003_wfaudit001_processed-events-never-pruned.md` row 4 only: `docs/41_db/db_02_architecture_and_schema-schema-reference.md`.

## Assumptions
- Behavior documented is what the row 1 document implements: recovery deletes the (`task_id`, `stage_id`) event rows of attempts it fails; startup purge deletes event rows of terminal tasks older than the 30-day `_EVENT_RETENTION_SEC` constant.

## Design decisions
- Extend the existing `processed_events`/task-tables narrative in place; no new section or file.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/41_db/db_02_architecture_and_schema-schema-reference.md`

### Procedure
Add the recovery prune and startup retention behavior to the `processed_events` description (the task-tables paragraph at L46-48).

### Method
State: recovery deletes the event rows of the (`task_id`, `stage_id`) pair of every attempt it marks failed, so a resumed stage re-executes; a startup purge deletes event rows whose task is terminal (`completed`/`failed`/`halted`) with `updated_at` older than a fixed 30-day horizon; `tasks`/`attempts` rows are retained (the `ON DELETE CASCADE` FK path is documented as available, not applied).

### Details
- Keep the existing stage re-execution sentence consistent with the new prune semantics; do not restate the 30-day value in more than one place.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` per `routing.md`.

## Completion criteria
- The `processed_events` entry states its pruning and retention behavior accurately after the code lands.

## Out of Scope
- The recovery narrative in db_07 (row 5 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the `processed_events` retention narrative per Procedure/Method | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` (retention documentation)
- **Source issue**: `issues/20261107-203214_wfaudit001_processed-events-never-pruned.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084003_wfaudit001_processed-events-never-pruned.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-134201
- **Related target files**: `docs/41_db/db_02_architecture_and_schema-schema-reference.md`
