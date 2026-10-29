## Goal

Add a DLQ requeue audit assertion test (`REQ-002`, `REQ-005`; AC-1, AC-4): a successful requeue emits one privileged record carrying the operator token fingerprint and the real request id.

## Scope

Append one test function to `tests/eventbus/test_eventbus_dlq.py`. No change to the existing fixture, helpers, or tests.

## Assumptions

- Source claims re-verified this cycle (2026-10-29): the file has no `log_privileged_action` assertions today (grep); `test_dlq_requeue` at `:121` shows the working requeue recipe (publish -> nack until the event lands in the DLQ -> `POST /dlq/{event_id}/requeue` with `eventbus_auth_headers("operator")`, asserting `body["requeued"] is True`); the audit call lands in `dlq_route.py:70-76` (kwarg call), so patching `eventbus.dlq_route.log_privileged_action` intercepts it.
- The `client` fixture builds config via `eventbus_test_tokens("test-token")`, so the operator credential is `eventbus_test_tokens("test-token")["operator_token"]`.
- Sequencing: land after seq 04 (the `actor` kwarg exists) and after `implementations/20261029-085348_02_tests_eventbus_test_eventbus_dlq.py.md` (ebdlqrecon002 edits this file; append after its additions); `implementations/20261029-102038_03_tests_eventbus_test_eventbus_dlq.py.md` (comment cleanup) re-runs its identifier search at implementation time and lands after this row.

## Design decisions

- New test `test_requeue_audit_record_carries_actor_and_request_id` (new) (reuses the exact DLQ-driving recipe of `test_dlq_requeue`): wrap only the requeue POST in `patch("eventbus.dlq_route.log_privileged_action")`, then assert on `mock_log.call_args.kwargs`:
  - `kwargs["route"] == "/dlq/requeue"` -- the exact literal the call site passes at `dlq_route.py:73`.
  - `kwargs["target"] == event_id`.
  - `kwargs["actor"] == _derive_token_fingerprint(eventbus_test_tokens("test-token")["operator_token"])`.
  - `kwargs["request_id"]` non-empty.
- Assert via the shared derivation function (no hardcoded hash), mirroring seq 07's decision.

## Alternatives considered

- Extending `test_dlq_requeue` itself with assertions: rejected; that test already pins the requeue outcome and DB effects, and mixing audit mocking into it obscures failure attribution.

## Implementation
### Target file

`tests/eventbus/test_eventbus_dlq.py`

### Procedure

1. Add `from unittest.mock import patch` to the module imports and `from eventbus.auth import _derive_token_fingerprint`, `from tests.eventbus.eventbus_helpers import eventbus_test_tokens` (the helpers import already exists; extend it).
2. Append the new test after `test_dlq_requeue`, reusing its DLQ-driving steps verbatim.

### Method

Append-only test addition; no fixture or helper changes.

### Details

- Patch scope covers only the requeue POST so `call_count == 1` is unambiguous.

## Compatibility considerations

- Test-only change; append position keeps existing tests untouched.

## Security considerations

- Pins that the record carries the fingerprint derived from the operator token, never the token value.

## Rollback considerations

- Delete the appended test together with the seq 04 revert.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_dlq.py -v`.
- `uv run ruff check tests/eventbus/test_eventbus_dlq.py` and `uv run mypy tests/eventbus/test_eventbus_dlq.py`.

## Completion criteria

- New test passes against the seq 04 implementation and asserts the four kwargs above.

## Out of Scope

- `dlq_list` audit behavior (no privileged record today), DLQ logic, comment-label cleanup (102038_03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Land after seq 04 |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row is the tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-002, REQ-005 (AC-1, AC-4)
- **Source issue**: `issues/20261028-122415_ebaudit005_privileged-audit-actor-context.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-115727
- **Related target files**: tests/eventbus/test_eventbus_dlq.py
