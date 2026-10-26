## Goal

In `tests/eventbus/test_eventbus_consumer_authorization.py`, assert that an unauthorized
consumer ID returns exactly HTTP 403 before any delivery-state check (seq 03 unifies the
check) and that the unified `require_consumer_identity()` check rejects unauthorized topics
too.

## Scope

- Modify only `tests/eventbus/test_eventbus_consumer_authorization.py`.

## Assumptions

- `require_consumer_identity()` (auth.py:279) enforces consumer-id AND topic bindings and
  returns exactly 403 for an unauthorized consumer ID before any delivery-state check
  (REQ-005; Acceptance 3).
- The file exists as an existing suite row; if it does not exist, create it (mark `(new)`).

## Design decisions

- Add tests for: (a) exactly-403-before-409 ordering, (b) unauthorized topic rejection via
  the unified check.

## Alternatives considered

- Adding to test_eventbus_ack_endpoint.py instead: this file owns the consumer-identity /
  topic-binding assertions; keep them here.

## Implementation

### Target file

`tests/eventbus/test_eventbus_consumer_authorization.py`

### Procedure

1. Add a test that an unauthorized consumer ID returns exactly `403` (not `409`, not any of
   `(403, 409)`) and that this 403 precedes any delivery-state check (REQ-005).
2. Add a test that a Consumer token with an authorized `consumer_id` succeeds while an
   unauthorized `consumer_id` or topic returns 403 (INV-02, INV-07).
3. Assert the handler-level duplicate check is gone (seq 03) and identity is enforced by the
   dependency.

### Method

Add test functions; ensure no assertion uses the masked `(403, 409)` form.

### Details

- Coordinate with seq 09, which tightens `test_eventbus_ack_endpoint.py` line 228 from
  `(403, 409)` to `403`; both rows enforce the same ordering.

## Compatibility considerations

- Role-token boundaries (operator/monitoring/admin hold no Consumer role) must still pass
  (plan Tests).

## Security considerations

- Confirms fail-closed 403 for unauthorized identities (INV-01/02/07).

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_consumer_authorization.py` — 403-before-409
  and topic-binding assertions pass.
- `uv run pytest tests/eventbus/` — full suite passes.

## Completion criteria

- Exactly-403-before-409 ordering and unauthorized-topic rejection are asserted.

## Out of Scope

- Other test files (seq 09-10).

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
- **Related target files**: `tests/eventbus/test_eventbus_consumer_authorization.py`
