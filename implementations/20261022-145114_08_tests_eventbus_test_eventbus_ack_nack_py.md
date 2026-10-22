## Goal

Rewrite the NACK result and response assertions to the status model and the renamed response key; delete the assertions that check the legacy event-level counters (REQ-006).

## Scope

- Modify `tests/eventbus/test_eventbus_ack_nack.py` only.

## Assumptions

- `delivery_repo.py` (status model) and `ack_route.py` (renamed key) are edited first; this test exercises the final contract.
- The five NACK outcomes (not-found, DLQ'd, already-ACKed, idempotent-repeat, success) keep their HTTP results.

## Design decisions

- Assert `NackResult(status="ok"/"not_found"/"invalid_state", consumer_failure_count=...)` instead of the sentinel values.
- Assert the response body holds `consumer_delivery_failure_count` instead of `delivery_failure_count`.

## Alternatives considered

- Keeping the old `NackResult(delivery_failure_count=..., cycle_failure_count=...)` assertions: rejected — those fields no longer exist.

## Implementation

### Target file

`tests/eventbus/test_eventbus_ack_nack.py`

### Procedure

1. Replace every `NackResult(delivery_failure_count=<v>, cycle_failure_count=<v>)` assertion with the matching `NackResult(status="<not_found|invalid_state|ok>", ...)` (add `consumer_failure_count=<v>` where a consumer_id is involved).
2. Replace the idempotent-repeat assertion (currently `NackResult(delivery_failure_count=0, cycle_failure_count=0)` / with `consumer_failure_count=1`) with `NackResult(status="ok", consumer_failure_count=<v>)`.
3. In the response-body assertions, replace the `delivery_failure_count` key with `consumer_delivery_failure_count`.
4. Remove the inline SQL `SELECT delivery_failure_count, cycle_failure_count FROM events` expectations and the `row["delivery_failure_count"] == 0` / `row["cycle_failure_count"] == 0` assertions (the route no longer reads those columns).
5. Keep the 404 / 409 / 200 HTTP assertions unchanged.

### Method

This file has ~30 references to the legacy counters; all express either the sentinel return values or the response key, both of which the two source documents change. The outcome/HTTP mapping is preserved.

### Details

- Representative assertions at lines 359, 365-366, 387, 397, 403, 433, 440-441, 474, 514 (the idempotent-repeat case at line 474 keeps reporting `ok` with the per-consumer count).

## Compatibility considerations

- Depends on `delivery_repo.py` + `ack_route.py` being updated; run this test after both.

## Security considerations

- N/A: test-only change.

## Rollback considerations

- revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -q`.

## Completion criteria

- No `delivery_failure_count` / `cycle_failure_count` assertion remains; each of the five NACK outcomes asserts the correct status and HTTP result, and the response asserts `consumer_delivery_failure_count`.

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
- **Related target files**: `tests/eventbus/test_eventbus_ack_nack.py`
