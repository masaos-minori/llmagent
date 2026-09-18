## Goal

Remove the unused `_principal: Principal | None = None` parameter from `scripts/eventbus/publish_route.py::publish()` to eliminate dead-code inconsistency across EventBus route handlers.

## Scope
- **In-Scope**: Remove `_principal: Principal | None = None` from `publish()`'s function signature in `scripts/eventbus/publish_route.py`.
- **Out-of-Scope**: Do not change `require_role`/`require_consumer_identity` authorization logic itself. Do not fix the `_TOKEN_CONSUMER_MAP` `ImportError`s in other four eventbus test files (fileed separately). Do not fix `test_partial_ack_replay` or concurrent/DLQ pagination test failures (fileed separately).

## Assumptions
- The `_principal` parameter in `publish()` serves no functional purpose — it is accepted but never read anywhere in the function body or its call chain.
- The existing `require_role(Role.PUBLISHER)` dependency in FastAPI's `Depends(...)` provides sufficient authorization for the publish operation.
- Removing `_principal` does not break any callers because both known callers pass `_principal=_principal` as a keyword argument — removing the parameter eliminates the need for this forwarding entirely.
- Other route handlers (ack/nack/subscribe) use `_principal` for concrete authorization logic (consumer_id validation, topic access control), while `publish()` does not need these checks.

## Design decisions
- Remove the unused `_principal` parameter rather than making it required: adding a required-but-unused parameter creates an inconsistent API compared to other route handlers (which keep it optional `Principal | None = None`) and adds maintenance burden without functional value.
- Keep `require_role(Role.PUBLISHER)` in the FastAPI route registration — this is the actual authorization mechanism for publish, and `_principal` was never wired into any authorization logic within the function.

## Alternatives considered
- Making `_principal` a required parameter (`_principal: Principal`) instead of removing it — rejected because it creates an inconsistent API (other handlers keep it optional), adds maintenance burden, and introduces no functional value (the parameter is never read).
- Keeping `_principal: Principal | None = None` as-is — rejected because it is dead code that misleads future developers into thinking it serves a purpose; also creates semantic inconsistency with other route handlers where `_principal` is actively used for authorization.
- Removing `_principal=_principal` from the test harness's local `/publish` wrapper only — rejected because the production code should be cleaned up directly rather than having tests diverge from it.

## Implementation
### Target file
`scripts/eventbus/publish_route.py`

### Procedure
Remove the unused `_principal: Principal | None = None` parameter from `publish()`'s function signature.

### Method
Mechanical edit: modify the function signature on line 37–39 of `publish_route.py`.

### Details
1. Line 37–39: Change `async def publish(` / `request: Request,` / `_principal: Principal | None = None,` to `async def publish(request: Request,`:
   - Remove the `_principal` parameter entirely
   - Remove the trailing comma after `request: Request,` (no longer needed since `_principal` is removed)
2. Verify that `_principal` is not referenced anywhere else in the function body (it is not — confirmed via adversarial verification).
3. Verify that the `Principal` import at line 13 can potentially be removed if no other symbols from `eventbus.auth` are still used in this file (check before removal).
4. Update the test harness's local `/publish` wrapper in `tests/eventbus/test_eventbus_auth.py` to remove `_principal=_principal` from the keyword arguments passed to `eb_app.publish_route()`.

## Compatibility considerations
Removing `_principal` from `publish()` changes the function signature. However, based on the Plan's verification, the only callers are the FastAPI route handler (`app.py:161`) and the test harness (`test_eventbus_auth.py:89`), both of which pass `_principal=_principal` as a keyword argument — removing the parameter eliminates the need for this forwarding entirely. No direct programmatic callers outside FastAPI DI exist, so this change is safe.

Note: This change makes `publish()` consistent with route handlers that do not need `_principal` for authorization (dlq_list, dlq_requeue, replay), which also omit the parameter entirely.

## Security considerations
N/A: adding a parameter to an internal function signature does not introduce new security concerns. The `_principal` parameter is already used by other route handlers and is part of the existing Principal-based authorization model.

## Rollback considerations
If the fix causes unexpected side effects (e.g., someone later needs `_principal` for audit logging), revert the signature change and restore `_principal: Principal | None = None`. This rollback path is acceptable because the parameter would then be wired into actual audit logic before being made required.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/publish_route.py | Type safety check | `uv run mypy scripts/eventbus/publish_route.py` | No new type errors |
| tests/eventbus/test_eventbus_auth.py | Unit test execution | `uv run pytest tests/eventbus/test_eventbus_auth.py -v` | All 14 originally-failing tests pass, or remaining failures documented |
| tests/eventbus/ | Integration regression | `uv run pytest tests/eventbus/ -q` | No new failures in eventbus test suite |

## Completion criteria
- [ ] REQ-EB-002-001: `_principal` parameter removed from `publish()` signature
- [ ] REQ-EB-002-001: `uv run mypy scripts/eventbus/publish_route.py` stays green
- [ ] REQ-EB-002-001: Test harness's `/publish` wrapper updated to remove `_principal=_principal` forwarding
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
| 1 | REQ-EB-002-001; Remove _principal parameter from publish() | Completed | — | 20260918-175252 | Removed unused _principal param + Principal import; updated test harness /publish wrapper |
| 2 | REQ-EB-002-001; Run mypy type check | Pending | — | — | |
| 3 | REQ-EB-002-001; Update test harness /publish wrapper | Pending | — | — | |
| 4 | REQ-EB-002-001; Run targeted test | Pending | — | — | |
| 5 | REQ-EB-002-003; Run regression test | Pending | — | — | |

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
