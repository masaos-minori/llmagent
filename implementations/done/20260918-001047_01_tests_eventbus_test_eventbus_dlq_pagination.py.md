## Goal
Add the mandatory `consumer_id` query parameter to every `/nack` call in `test_dlq_pagination` so events are actually promoted to the DLQ, and add explicit status-code assertions on each nack call.

## Scope
- **In-Scope**: Fix `tests/eventbus/test_eventbus_dlq_pagination.py::test_dlq_pagination` setup to pass `consumer_id` to `/nack` calls and assert 200 responses.
- **Out-of-Scope**: Do not change the `/nack` endpoint's mandatory-`consumer_id` contract. Do not fix other eventbus test issues filed separately (`_TOKEN_CONSUMER_MAP`, `test_eventbus_auth.py`, concurrency/crash-recovery).

## Assumptions
- `"consumer-A"` is a valid consumer ID for the test token; no authorization failure will occur when passed to `/nack`.

## Design decisions
- Use `consumer_id="consumer-A"` as the consumer ID value, matching the naming convention used in other passing tests (e.g., `test_nack_event_mandatory_consumer_id`).
- Add explicit `assert r.status_code == 200` after each `/nack` call to fail immediately on regression rather than producing a confusing downstream pagination-count mismatch.

## Alternatives considered
- Using a different consumer ID value (e.g., `"consumer-B"`) — rejected because `"consumer-A"` follows the established naming convention and is verified against passing tests.
- Adding only `consumer_id` without status-code assertion — rejected because the Plan explicitly requires both REQ-EB-004-001 and REQ-EB-004-002.

## Implementation
### Target file
`tests/eventbus/test_eventbus_dlq_pagination.py`

### Procedure
Add `consumer_id="consumer-A"` to the `params` dict on both `/nack` calls (lines 70, 73), and add `assert r.status_code == 200` after each call.

### Method
Mechanical edit: modify two lines in `test_dlq_pagination` function.

### Details
1. Line 70: Change `client.post(f"/nack?event_id={event_id}")` to `client.post("/nack", params={"event_id": event_id, "consumer_id": "consumer-A"})`
2. After line 70: Add `assert r.status_code == 200`
3. Line 73: Change `client.post(f"/nack?event_id={event_id}")` to `client.post("/nack", params={"event_id": event_id, "consumer_id": "consumer-A"})`
4. After line 73: Add `assert r.status_code == 200`

## Compatibility considerations
N/A: test-only change with no production behavior impact.

## Security considerations
N/A: test-only change.

## Rollback considerations
If the fix causes unexpected authorization failures, revert to removing the `consumer_id` parameter and investigate whether the `/nack` endpoint's contract changed since this test was written.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_dlq_pagination.py | Unit test execution | `uv run pytest tests/eventbus/test_eventbus_dlq_pagination.py -v` | All tests pass, including `test_dlq_pagination` |
| tests/eventbus/ | Integration regression | `uv run pytest tests/eventbus/ -q` | No new failures in eventbus test suite |

## Completion criteria
- [ ] REQ-EB-004-001: `uv run pytest tests/eventbus/test_eventbus_dlq_pagination.py -v` passes
- [ ] REQ-EB-004-002: Each `/nack` call includes `consumer_id="consumer-A"` and asserts HTTP 200

## Out of scope
- Changing the `/nack` endpoint's mandatory-`consumer_id` contract
- Fixing other eventbus test issues filed separately

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | REQ-EB-004-001; Add `consumer_id="consumer-A"` to both `/nack` calls | Pending | — | — | |
| 2 | REQ-EB-004-002; Add `assert r.status_code == 200` after each `/nack` call | Pending | — | — | |
| 3 | REQ-EB-004-001; Run targeted test | Pending | — | — | |
| 4 | REQ-EB-004-001; Run regression test | Pending | — | — | |

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
- **Requirement ID**: REQ-EB-004-001, REQ-EB-004-002
- **Source issue**: issues/20260917-110721_eb04_eventbus-dlq-pagination-test-failure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260917-223308_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260918-001047
- **Related target files**: tests/eventbus/test_eventbus_dlq_pagination.py
