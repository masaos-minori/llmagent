## Goal

Remove assertions on the copied/reset legacy counters in the requeue lineage tests; redelivery no longer copies or resets the event-level counters (REQ-006).

## Scope

- Modify `tests/eventbus/test_eventbus_requeue_edge_cases.py` only.

## Assumptions

- `dlq_repo.py` drops the `_COL_DELIVERY_FAILURE_COUNT` / `_COL_CYCLE_FAILURE_COUNT` copy/reset; the redelivered `events` row carries no event-level counter.

## Design decisions

- Drop the assertions that the redelivered row's `delivery_failure_count` / `cycle_failure_count` were copied / reset to `0`.
- Keep the lineage assertions (`redelivered_from`, topic/payload copy) that are unaffected.

## Implementation

### Target file

`tests/eventbus/test_eventbus_requeue_edge_cases.py`

### Procedure

1. Remove assertions checking the redelivered `delivery_failure_count` / `cycle_failure_count` values (copied or reset to 0).
2. Keep the redelivery lineage checks (`redelivered_from` set, other columns copied).

### Method

~20 references assert the legacy counter behavior of redelivery; removing them matches the dropped copy/reset in `dlq_repo.py`.

## Compatibility considerations

- Run after `dlq_repo.py`.

## Security considerations

- N/A: test-only.

## Rollback considerations

- revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py -q`.

## Completion criteria

- No redelivery assertion on the legacy counters remains; lineage checks still pass.

## Out of Scope

- Other test files, source, documents.

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

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006
- **Source issue**: `issues/20261022-124142_evcounter_decide-event-level-failure-counters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130338_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-145114
- **Related target files**: `tests/eventbus/test_eventbus_requeue_edge_cases.py`
