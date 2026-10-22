## Goal

Remove the reference to the now-removed event-level counter `delivery_failure_count` from a setup comment in `tests/eventbus/test_eventbus_concurrent.py`, per `REQ-006` (update the tests to the new contract) and `AC-6`.

## Scope

Only `tests/eventbus/test_eventbus_concurrent.py`. The single legacy-counter reference is a comment in `TestConcurrentDlqRequeue.test_concurrent_dlq_requeue`; the per-consumer `consumer_delivery_failure_count` INSERT in the same test is retained.

## Assumptions

- `schema.sql` (row 6 of this plan) removes `delivery_failure_count` from the `events` DDL in the same pass.
- The per-consumer gating model (`consumer_delivery_failure_count`) is the source of truth and stays.

## Design decisions

- Edit the comment in place rather than deleting the whole setup block: the comment explains why a seeded prior failure is needed, and the per-consumer gating rationale should remain even after the shared-counter mention is dropped.

## Alternatives considered

- Deleting the entire four-line comment — rejected: it documents the seeding intent, which is still accurate and useful.
- Rewriting the test to seed via a different mechanism — out of scope; this row only removes the stale counter reference.

## Implementation

### Target file

`tests/eventbus/test_eventbus_concurrent.py`

### Procedure

1. Remove the shared-`delivery_failure_count` clause from the setup comment.
2. Run the EventBus test suite.

### Method

- In `TestConcurrentDlqRequeue.test_concurrent_dlq_requeue`, change the comment:

  ```python
  # Simulate one prior failure for consumer-A so a single NACK reaches
  # max_retry. Under per-consumer gating (REQ-002) one consumer reaching
  # its own budget promotes; the shared delivery_failure_count is not used
  # for gating.
  ```

  to drop the shared-counter sentence while keeping the seeding and per-consumer rationale:

  ```python
  # Simulate one prior failure for consumer-A so a single NACK reaches
  # max_retry. Under per-consumer gating (REQ-002) one consumer reaching
  # its own budget promotes.
  ```

### Details

- Evidence in-file: the reference is the word `delivery_failure_count` on the third comment line (preceded by "the shared "). The per-consumer `consumer_delivery_failure_count` in the `INSERT INTO consumer_delivery (...)` below is a different symbol and is left untouched.

## Compatibility considerations

N/A: test-only change; no runtime or on-disk contract is affected.

## Security considerations

N/A: no auth, authorization, or input-handling path is touched.

## Rollback considerations

N/A: revert the commit that makes this change.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_concurrent.py` | Integration | `uv run pytest tests/eventbus/test_eventbus_concurrent.py -q` | Pass |
| Whole EventBus suite | Regression | `uv run pytest tests/eventbus -q` | No new failures |

## Completion criteria

The setup comment in `test_concurrent_dlq_requeue` no longer names `delivery_failure_count`, and `uv run pytest tests/eventbus/test_eventbus_concurrent.py -q` passes.

## Out of Scope

- Any change to the real `scripts/eventbus/schema.sql` (row 6).
- Other test files' comments or inline schemas (each row is handled by its own document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the stale shared-counter reference from the setup comment | Pending | — | — | |
| 2 | Update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: test-only change | — | — | |

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
- **Requirement ID**: `REQ-006` — update the tests to the new contract after removing the legacy event-level counters
- **Source issue**: `issues/20261022-124142_evcounter_decide-event-level-failure-counters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130338_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-145114
- **Related target files**: `tests/eventbus/test_eventbus_concurrent.py`
