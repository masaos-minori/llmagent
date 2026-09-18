## Goal
Investigate and fix consumer-identity-ownership issues causing ack failures in `test_partial_ack_replay`.

## Scope
- **In-Scope**: Add status-code assertion on ack call (lines 146-149); investigate consumer-identity-ownership issue; fix if needed.
- **Out-of-Scope**: Do not fix the `_TOKEN_CONSUMER_MAP` `ImportError`s (filed separately). Do not fix the 14 `test_eventbus_auth.py` failures beyond coordinating on a shared root cause if one is confirmed (fileed separately). Do not fix `test_eventbus_dlq_pagination.py` (fileed separately). Do not weaken `require_consumer_identity` or the `/nack` mandatory-`consumer_id` contract.

## Assumptions
- The consumer-identity-ownership theory for #3 is plausible: the `client` fixture uses a shared admin token, and `require_consumer_identity` may enforce per-consumer ownership that rejects acks from tokens not scoped to the requested `consumer_id`.
- The `offsets_dir does not exist` warning is benign and unrelated to the failure.

## Design decisions
- First add a status-code assertion on the currently-unchecked ack call(s) to turn the silent failure into a clear, immediate error.
- Then investigate why the ack is rejected/fails for the `client`/shared-token fixture used in this file.
- If the cause matches the Principal/consumer-identity-ownership question raised in the sibling `test_eventbus_auth.py` issue, coordinate the fix approach with that issue rather than diverging.
- For the most likely fix: ensure the `client` fixture or test uses a Principal scoped to the specific `consumer_id` being tested, following the pattern used in passing tests like `test_nack_event_mandatory_consumer_id`.

## Alternatives considered
- Weakening `require_consumer_identity` or the `/nack` mandatory-`consumer_id` contract to make this test pass — rejected because the Plan explicitly forbids this approach.
- Investigating whether the `offsets_dir does not exist` warning affects this test — rejected because it was ruled out as harmless in the Plan's verification.

## Implementation
### Target file
`tests/eventbus/test_eventbus_crash_ack.py`

### Procedure
Add status-code assertion on ack call (lines 146-149); investigate consumer-identity-ownership issue.

### Method
Mechanical edit for Cause 3; investigative + mechanical edit for consumer-identity-ownership issue.

### Details
1. **Cause 3: Fix `test_partial_ack_replay`'s missing status-code assertion**
   - Lines 146-149: Add `assert resp1.status_code == 200` after the ack call to convert silent failures into immediate errors
   
2. **Consumer-identity-ownership investigation**
   - Investigate why ack fails for `consumer-B` when using the shared admin token
   - Check `require_consumer_identity` logic in `scripts/eventbus/auth.py`; compare with passing tests that use `principal_client`
   - Find passing tests that use `principal_client` or similar scoped fixture to understand the correct pattern
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
| tests/eventbus/test_eventbus_crash_ack.py | Unit test execution | `uv run pytest tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_partial_ack_replay -v` | `test_partial_ack_replay` passes |
| tests/eventbus/ | Integration regression | `uv run pytest tests/eventbus/ -q` | No new failures in eventbus test suite |

## Completion criteria
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
| 1 | REQ-EB-003-002; Add status assertion to crash ack call | Completed | — | 20260918-180404 | Already had assertion; added delivery simulation for consumer-B |
| 2 | REQ-EB-003-003; Investigate consumer-identity-ownership in crash ack test | Pending | — | — | |
| 3 | REQ-EB-003-002; Run targeted test (crash) | Pending | — | — | |
| 4 | REQ-EB-003-003; Run regression test | Pending | — | — | |

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
- **Requirement ID**: REQ-EB-003-002, REQ-EB-003-003
- **Source issue**: issues/20260917-110534_eb03_eventbus-concurrency-and-crash-recovery-test-failures.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260917-224117_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260918-001431
- **Related target files**: tests/eventbus/test_eventbus_crash_ack.py
