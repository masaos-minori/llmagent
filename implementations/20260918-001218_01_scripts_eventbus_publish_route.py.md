## Goal
Add `_principal: Principal` parameter to `scripts/eventbus/publish_route.py::publish()` to match the signature used by other route handlers.

## Scope
- **In-Scope**: Modify `scripts/eventbus/publish_route.py::publish()` function signature to accept `_principal: Principal` parameter.
- **Out-of-Scope**: Do not change `require_role`/`require_consumer_identity` authorization logic itself. Do not fix the `_TOKEN_CONSUMER_MAP` `ImportError`s in other four eventbus test files (fileed separately). Do not fix `test_partial_ack_replay` or concurrent/DLQ pagination test failures (fileed separately).

## Assumptions
- Adding `_principal: Principal` to `publish()` is the correct design decision — publish should participate in Principal-based per-request auditing like other routes. If publish intentionally has no Principal-specific behavior beyond the existing role check, the alternative fix is to remove `_principal=_principal` forwarding from the test harness's local `/publish` wrapper.

## Design decisions
- Mirror the pattern used by other route handlers (ack/nack/dlq/replay) which all accept `_principal: Principal` from FastAPI's `Depends(...)`. This ensures consistency across the EventBus module after the Principal refactor (commit c85362a36).

## Alternatives considered
- Removing `_principal=_principal` from the test harness's local `/publish` wrapper instead of adding it to production code — rejected because the test harness should mirror production, not diverge from it. The Plan explicitly states this approach.
- Not adding `_principal` at all and treating cause 1 as a test-harness bug only — rejected because the Plan's intent is to align with the Principal refactor pattern.

## Implementation
### Target file
`scripts/eventbus/publish_route.py`

### Procedure
Add `_principal: Principal` parameter to `publish()` function signature to match the signature used by other route handlers.

### Method
Mechanical edit: modify the function signature on line 36 of `publish_route.py`.

### Details
1. Line 36: Change `async def publish(` to `async def publish(_principal: Principal, `
2. Ensure the `Principal` type is imported at the top of the file (check if already imported; if not, add `from eventbus.auth import Principal`)
3. Verify that the rest of the function body does not reference `_principal` directly (it may be used implicitly via FastAPI's `Depends(...)` mechanism in the route registration)

## Compatibility considerations
Adding `_principal` to `publish()` changes the function signature. If any callers outside the FastAPI dependency injection system call `publish()` directly (e.g., in production code paths), they will need to provide a `Principal` argument. However, based on the Plan's verification, the only caller is the FastAPI route handler which uses `Depends(...)`, so this should not break production behavior.

## Security considerations
N/A: adding a parameter to an internal function signature does not introduce new security concerns. The `_principal` parameter is already used by other route handlers and is part of the existing Principal-based authorization model.

## Rollback considerations
If the fix causes unexpected side effects, revert the signature change and instead remove `_principal=_principal` from the test harness's local `/publish` wrapper. This rollback path is less desirable because it leaves the test harness diverging from production.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/publish_route.py | Type safety check | `uv run mypy scripts/eventbus/publish_route.py` | No new type errors |
| tests/eventbus/test_eventbus_auth.py | Unit test execution | `uv run pytest tests/eventbus/test_eventbus_auth.py -v` | All 14 originally-failing tests pass, or remaining failures documented |
| tests/eventbus/ | Integration regression | `uv run pytest tests/eventbus/ -q` | No new failures in eventbus test suite |

## Completion criteria
- [ ] REQ-EB-002-001: `publish()` accepts `_principal: Principal` parameter matching other route handlers
- [ ] REQ-EB-002-001: `uv run mypy scripts/` stays green after signature change
- [ ] REQ-EB-002-001: `TestPublishAuth::test_publish_with_valid_publisher_token` passes

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
| 1 | REQ-EB-002-001; Add _principal parameter to publish() | Pending | — | — | |
| 2 | REQ-EB-002-001; Run mypy type check | Pending | — | — | |
| 3 | REQ-EB-002-001; Run targeted test | Pending | — | — | |
| 4 | REQ-EB-002-003; Run regression test | Pending | — | — | |

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
- **Requirement ID**: REQ-EB-002-001
- **Source issue**: issues/20260917-110320_eb02_test_eventbus_auth.py-has-14-failing-tests-after-principal-refactor.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260917-223656_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260918-001218
- **Related target files**: scripts/eventbus/publish_route.py
