## Goal

Add a replay audit assertion test (`REQ-002`, `REQ-005`; AC-1, AC-4): a `GET /replay` request emits one privileged record carrying the operator token fingerprint and the real request id.

## Scope

Append one test function to `tests/eventbus/test_eventbus_replay_pagination.py`. No change to the existing fixture or tests.

## Assumptions

- Source claims re-verified this cycle (2026-10-29): the file drives `GET /replay?since_seq=0&format=json&limit=100&offset=0` with `eventbus_auth_headers("operator")` in `test_replay_json_returns_paginated_response` (`:51+`); the audit call is at `replay_route.py:38-44` with kwargs (`consumer_id=""`, `request_id=request.state.request_id`, `route="/replay"`, `target=f"seq:{since_seq}"`); the file has no `log_privileged_action` assertions today (grep).
- The `client` fixture builds config via `eventbus_test_tokens("test-token")`, so the operator credential is `eventbus_test_tokens("test-token")["operator_token"]`.
- Sequencing: land after seq 05 (the `actor` kwarg exists). No other generated procedure edits this file; the ebpage003 procedures target other files.

## Design decisions

- New test `test_replay_audit_record_carries_actor_and_request_id` (new): publish one event, then wrap only the `GET /replay?since_seq=0&format=json` call in `patch("eventbus.replay_route.log_privileged_action")`, and assert on `mock_log.call_args.kwargs`:
  - `call_count == 1` (one record per replay request).
  - `kwargs["route"] == "/replay"`.
  - `kwargs["target"] == "seq:0"`.
  - `kwargs["actor"] == _derive_token_fingerprint(eventbus_test_tokens("test-token")["operator_token"])`.
  - `kwargs["request_id"]` non-empty.
- Fingerprint asserted via the shared derivation function (no hardcoded hash), mirroring seq 07/08.

## Alternatives considered

- Using the SSE variant of `/replay`: rejected; the JSON variant is already exercised in this file and the audit record is emitted before the format split.

## Implementation
### Target file

`tests/eventbus/test_eventbus_replay_pagination.py`

### Procedure

1. Add `from unittest.mock import patch`, `from eventbus.auth import _derive_token_fingerprint`, and extend the existing `tests.eventbus.eventbus_helpers` import with `eventbus_test_tokens`.
2. Append the new test after `test_replay_json_returns_paginated_response`, reusing its `_event` helper and publish step.

### Method

Append-only test addition; no fixture changes.

### Details

- The patch must target `eventbus.replay_route.log_privileged_action` (the module-level imported name; `tools/check_mock_patch_targets.py` convention).

## Compatibility considerations

- Test-only change; existing pagination tests untouched.

## Security considerations

- Pins the fingerprint-not-token property for the replay record.

## Rollback considerations

- Delete the appended test together with the seq 05 revert.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_replay_pagination.py -v`.
- `uv run ruff check tests/eventbus/test_eventbus_replay_pagination.py` and `uv run mypy tests/eventbus/test_eventbus_replay_pagination.py`.

## Completion criteria

- New test passes against the seq 05 implementation and asserts the kwargs above.

## Out of Scope

- Pagination contract tests, SSE behavior, subscribe endpoint.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Land after seq 05 |
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
- **Related target files**: tests/eventbus/test_eventbus_replay_pagination.py
