## Goal
Replace the false docstring claim in `begin_stage_if_new` (REQ-004: the comment promises recovery "removes their event IDs", which the code never did) with an accurate description of the post-change contract.

## Scope
**Release unit**: wfaudit001-full

- Covers Plan `plans/20261108-084003_wfaudit001_processed-events-never-pruned.md` row 2 only: `scripts/agent/workflow/idempotency_ops.py`.

## Assumptions
- The replacement text describes the behavior implemented by the row 1 document (`20261108-134201_01_scripts_agent_workflow_state_store.py.md`): recovery deletes the (`task_id`, `stage_id`) event rows of attempts it marks failed.

## Design decisions
- Comment-only change: `begin_stage_if_new` behavior is untouched; the semantics block keeps its three existing bullets and corrects the recovery bullet.

## Alternatives considered
- N/A: comment-only change, no behavioral alternative.

## Implementation
### Target file
`scripts/agent/workflow/idempotency_ops.py`

### Procedure
Replace the semantics comment block (L42-46, the false bullet at L46) with an accurate description.

### Method
Keep the first two bullets (processed means STARTED; a running attempt's event ID is present while in progress). Replace the third bullet with: recovery marks stale running attempts `failed` and deletes the `processed_events` rows for their (`task_id`, `stage_id`) pair, so a resumed stage runs again.

### Details
- The false claim is the phrase `removes their event IDs` at L46; the acceptance grep asserts that exact phrase no longer exists under `scripts/`.

## Compatibility considerations
- N/A: comment-only change.

## Security considerations
- N/A: comment-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `grep -rn "removes their event IDs" scripts/` returns nothing (Plan Acceptance Criteria REQ-004).
- Lint gates per `rules/toolchain.md`; no behavior change so existing suite suffices.

## Completion criteria
- The comment matches implemented behavior and the false phrase is gone; no code path changed.

## Out of Scope
- All behavior changes (row 1 document owns them).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the false comment block per Procedure/Method | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md` + REQ-004 grep) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (comment accuracy)
- **Source issue**: `issues/20261107-203214_wfaudit001_processed-events-never-pruned.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084003_wfaudit001_processed-events-never-pruned.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-134201
- **Related target files**: `scripts/agent/workflow/idempotency_ops.py`
