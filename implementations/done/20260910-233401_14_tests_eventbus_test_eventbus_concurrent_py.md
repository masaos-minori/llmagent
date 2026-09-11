# Update `test_concurrent_dlq_requeue`'s assertion for the new success shape

## Goal

Update `tests/eventbus/test_eventbus_concurrent.py`'s `test_concurrent_dlq_requeue`'s assertion for the new success shape (a new `seq`/`event_id` in the response) while preserving its core "only one requeue succeeds" assertion.

## Scope

- Modify `test_concurrent_dlq_requeue`: update the response shape assertion to account for new fields added by `redeliver_event()`.

## Assumptions

- Current test only checks `resp.get("requeued") is True` count; response shape gains new fields under this Plan (confirmed by reading test body).
- The new response fields include `"new_event_id"` and `"new_seq"` per UNK-01 default.

## Design decisions

- Preserve the existing assertion: exactly one of several simultaneous requeue requests succeeds.
- Add assertions on the successful response:
  1. `"requeued"` is `True`.
  2. `"new_event_id"` is present and is a valid UUID v4 string.
  3. `"new_seq"` is present and is an integer greater than the original event's seq.
- The failed responses should still have `"requeued"` as `False` (or HTTP error).

## Alternatives considered

- Rewriting the concurrency test entirely: rejected because the existing test structure validates the right invariant (single-winner-under-concurrency); only the response assertions need updating.

## Compatibility considerations

- These are unit tests — no external API contract impact.
- The tests must be updated simultaneously with the implementation changes.

## Security considerations

- No security surface change.

## Rollback considerations

- Reverting means restoring the old boolean-only response assertions.

## Validation plan

- Run `uv run pytest tests/eventbus/test_eventbus_concurrent.py::TestConcurrentDlqRequeue::test_concurrent_dlq_requeue -v` to confirm:
  - Exactly one concurrent requeue request succeeds.
  - Successful response includes `new_event_id` and `new_seq`.
  - Failed responses do not include these fields.

## Completion criteria

- Test preserves the "only one requeue succeeds" assertion.
- Test asserts `new_event_id` is a valid UUID v4 in the successful response.
- Test asserts `new_seq` is present and > original seq in the successful response.
- Tests pass.

## Out of scope

- Changes to `redeliver_event()` itself (handled separately in REQ-005).
- Changes to `dlq_route.py` call site (handled separately in REQ-006).

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Preserve single-winner concurrency assertion | Pending | — | — | |
| 2 | Add new_event_id/new_seq assertions on success | Pending | — | — | |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260907-125042_eb_h03_dlq_requeue_real_redelivery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-100315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-233401
- **Related target files**: tests/eventbus/test_eventbus_concurrent.py
