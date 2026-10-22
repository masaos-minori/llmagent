## Goal

Remove event-level counter setup and assertions from the DLQ promotion tests while keeping the per-consumer promotion gating tests intact (REQ-006).

## Scope

- Modify `tests/eventbus/test_eventbus_dlq_promotion.py` only.

## Assumptions

- Promotion is gated solely on `consumer_delivery_failure_count` (per-consumer); the events-level counters never gated promotion.
- `dlq.py` still selects the per-consumer count for promotion.

## Design decisions

- Delete any test setup that seeds `delivery_failure_count` / `cycle_failure_count` and any assertion reading them.
- Preserve the promotion-threshold tests that drive `consumer_delivery_failure_count` to `max_retry`.

## Alternatives considered

- Deleting the whole promotion test file: rejected — the per-consumer gating stays and must stay tested.

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq_promotion.py`

### Procedure

1. Remove setup lines that insert/set `delivery_failure_count` / `cycle_failure_count` on `events` rows used by promotion tests.
2. Remove any assertion reading those columns from the promoted row.
3. Verify each remaining promotion test gates purely on `consumer_delivery_failure_count >= max_retry`; keep them unchanged.

### Method

~34 references exist, but most are the per-consumer count or unrelated; only the event-level seeding/assertions are removed. The promotion behavior under test is unchanged.

## Compatibility considerations

- Run after `dlq.py` (promotion SELECT).

## Security considerations

- N/A: test-only.

## Rollback considerations

- revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py -q`.

## Completion criteria

- No event-level counter setup or assertion remains; promotion-gating tests on the per-consumer count still pass.

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
- **Related target files**: `tests/eventbus/test_eventbus_dlq_promotion.py`
