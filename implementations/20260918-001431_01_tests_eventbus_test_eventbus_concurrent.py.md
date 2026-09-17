## Goal
Fix three failing eventbus tests: add missing `consumer_id` to `/nack` calls in `test_concurrent_dlq_requeue`; investigate and fix consumer-identity-ownership issues in `test_concurrent_ack_same_event` and `test_partial_ack_replay`.

## Scope
- **In-Scope**: Fix `test_concurrent_dlq_requeue`'s missing `consumer_id` param; add status-code assertions to ack calls in `test_concurrent_ack_same_event` and `test_partial_ack_replay`; investigate and fix consumer-identity-ownership issues for both.
- **Out-of-Scope**: Do not fix the `_TOKEN_CONSUMER_MAP` `ImportError`s (filed separately). Do not fix the 14 `test_eventbus_auth.py` failures beyond coordinating on a shared root cause if one is confirmed (fileed separately). Do not fix `test_eventbus_dlq_pagination.py` (fileed separately). Do not weaken `require_consumer_identity` or the `/nack` mandatory-`consumer_id` contract.

## Assumptions
- Adding `consumer_id` to `/nack` calls in `test_concurrent_dlq_requeue` will resolve the 422 errors and allow events to reach the DLQ as expected.
- The consumer-identity-ownership theory for #2/#3 is plausible: the `client` fixture uses a shared admin token, and `require_consumer_identity` may enforce per-consumer ownership that rejects acks from tokens not scoped to the requested `consumer_id`.
- The `offsets_dir does not exist` warning is benign and unrelated to the failures.

## Design decisions
- For Cause 1: Add `consumer_id="consumer-A"` to the three `/nack` calls in `test_concurrent_dlq_requeue`'s setup loop (line 148), matching the pattern already used correctly elsewhere (e.g., `test_nack_event_mandatory_consumer_id`).
- For Cause 2: In `test_concurrent_ack_same_event`, add `assert resp.status_code == 200` after the ack call (lines 73-76) to convert silent failures into immediate errors. Then investigate why acks fail — likely due to consumer-identity-ownership enforcement.
- For Cause 3: In `test_partial_ack_replay`, add `assert resp1.status_code == 200` after the ack call (lines 146-149) to convert silent failures into immediate errors. Then investigate the consumer-identity-ownership issue for `consumer-B`.
- For causes 2 and 3, the most likely fix is to ensure the `client` fixture or test uses a Principal scoped to the specific `consumer_id` being tested, following the pattern used in passing tests like `test_nack_event_mandatory_consumer_id`.

## Alternatives considered
- Weakening `require_consumer_identity` or the `/nack` mandatory-`consumer_id` contract to make these tests pass — rejected because the Plan explicitly forbids this approach.
- Investigating whether the `offsets_dir does not exist` warning affects these tests — rejected because it was ruled out as harmless in the Plan's verification.

## Implementation
### Target file
`tests/eventbus/test_eventbus_concurrent.py`

### Procedure
Add `consumer_id` to `/nack` calls (line 148); add status-code assertions to ack calls (lines 73-76); investigate and fix consumer-identity-ownership issues.

### Method
Mechanical edit for Cause 1; investigative + mechanical edit for Causes 2 and 3.

### Details
1. **Cause 1: Fix `test_concurrent_dlq_requeue`'s missing `consumer_id`**
   - Line 148: Change `resp = client.post("/nack", params={"event_id": event_id})` to `resp = client.post("/nack", params={"event_id": event_id, "consumer_id": "consumer-A"})`
   - After line 148: Add `assert resp.status_code == 200`

2. **Cause 2: Investigate and fix `test_concurrent_ack_same_event`**
   - Lines 73-76: Add `assert resp.status_code == 200` after the ack call to convert silent failures into immediate errors
   - Investigate why acks fail — likely due to consumer-identity-ownership enforcement
   - If the cause matches the Principal/consumer-identity-ownership question raised in the sibling `test_eventbus_auth.py` issue, coordinate the fix approach with that issue rather than diverging
   - Likely fix: ensure the `client` fixture or test uses a Principal scoped to the specific `consumer_id` being tested, following the pattern used in passing tests like `test_nack_event_mandatory_consumer_id`

## Compatibility considerations
N/A: test-only change with no production behavior impact.

## Security considerations
N/A: test-only change.

## Rollback considerations
If the fix causes unexpected side effects, revert the changes and investigate whether the consumer-identity-ownership enforcement is correct for these call patterns.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_concurrent.py | Unit test execution | `uv run pytest tests/eventbus/test_eventbus_concurrent.py -v` | Both `test_concurrent_dlq_requeue` and `test_concurrent_ack_same_event` pass |
| tests/eventbus/ | Integration regression | `uv run pytest tests/eventbus/ -q` | No new failures in eventbus test suite |

## Completion criteria
- [ ] REQ-EB-003-001: `uv run pytest tests/eventbus/test_eventbus_concurrent.py -v` passes
- [ ] REQ-EB-003-002: `uv run pytest tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_partial_ack_replay -v` passes
- [ ] REQ-EB-003-003: No other test in either file regresses

## Out of scope
- Changing the `/nack` endpoint's mandatory-`consumer_id` contract
- Fixing other eventbus test issues filed separately (`_TOKEN_CONSUMER_MAP`, `test_eventbus_auth.py`, concurrency/crash-recovery)

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | REQ-EB-003-001; Add consumer_id to /nack calls | Pending | — | — | |
| 2 | REQ-EB-003-002; Add status assertions to concurrent ack calls | Pending | — | — | |
| 3 | REQ-EB-003-003; Investigate consumer-identity-ownership in concurrent ack test | Pending | — | — | |
| 4 | REQ-EB-003-001; Run targeted test (concurrent) | Pending | — | — | |
| 5 | REQ-EB-003-003; Run regression test | Pending | — | — | |

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
- **Requirement ID**: REQ-EB-003-001, REQ-EB-003-002, REQ-EB-003-003
- **Source issue**: issues/20260917-110534_eb03_eventbus-concurrency-and-crash-recovery-test-failures.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260917-224117_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260918-001431
- **Related target files**: tests/eventbus/test_eventbus_concurrent.py
