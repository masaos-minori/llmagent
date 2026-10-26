## Goal

Remove the masking assertion at `tests/eventbus/test_eventbus_ack_endpoint.py:228` that
accepts `status_code in (403, 409)`, replacing it with exactly `403` for the
unauthorized-consumer case, and assert that the 403 precedes any delivery-state check.

## Scope

- Modify only `tests/eventbus/test_eventbus_ack_endpoint.py` (line 228 and any related
  unauthorized-consumer assertion).

## Assumptions

- The implementation (seq 03) makes the handler return exactly 403 for an unauthorized
  consumer ID before any delivery-state check (REQ-005; Acceptance 3).
- Line 228 currently asserts `resp.status_code in (403, 409)` (plan Background).

## Design decisions

- Tighten the assertion to exactly `403`; this is the defect being fixed, so the test must
  fail against the pre-fix behavior and pass once 403 precedes 409.

## Alternatives considered

- Leaving the masked assertion: rejected — it hides the missing ordering (REQ-005).

## Implementation

### Target file

`tests/eventbus/test_eventbus_ack_endpoint.py`

### Procedure

1. At line 228, replace `resp.status_code in (403, 409)` with `resp.status_code == 403`
   for the unauthorized-consumer case.
2. If the test exercises an unauthorized consumer ID followed by a delivery-state check,
   assert the 403 is returned before any delivery-state response.
3. Search the file for any other `(403, 409)` masking and tighten consistently.

### Method

Edit the assertion(s); no new tests required beyond tightening.

### Details

- Coordinate with seq 08 (`test_eventbus_consumer_authorization.py`), which asserts the
  same ordering at the consumer-identity layer.

## Compatibility considerations

- The test now fails against pre-fix code; that is intended.

## Security considerations

- Confirms fail-closed 403 for unauthorized consumers (INV-01/02).

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py` — exactly-403 assertion
  passes against the fixed handler.
- `uv run pytest tests/eventbus/` — full suite passes.

## Completion criteria

- No `(403, 409)` masking remains for the unauthorized-consumer case; exactly 403 is asserted.

## Out of Scope

- Other test files (seq 07, 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row IS the test update |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation if in scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261023-154326_eventbus006_runtime-authorization-update-consistency.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-122243_eventbus006_runtime-authorization-update-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-090956
- **Related target files**: `tests/eventbus/test_eventbus_ack_endpoint.py`
