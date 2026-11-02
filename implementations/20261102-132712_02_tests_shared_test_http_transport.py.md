# Transport-level status classification tests

## Goal

Add `HttpTransport.call` cases to `tests/shared/test_http_transport.py` proving the tool-level set
returns tool error results and the transport set keeps raising `TransportError` (Plan REQ-001 /
REQ-003, AC for the tool-level/transport split with `httpx.MockTransport`).

## Scope

- New class `TestToolLevelStatusClassification` (new) appended after `TestDeriveIdempotencyKey`.
- Existing tests untouched — notably `test_ambiguous_status_not_retried_for_write_tool` (:181),
  `test_429_retried_for_write_tool` (:202), and the timeout/retry-exhaustion cases: they are the
  REQ-003/REQ-004 regression that stays green.

## Assumptions

- Verified 20261102: the module builds transports over `httpx.MockTransport` handlers and asserts
  `pytest.raises(TransportError)` for status failures today; the new class reuses that handler
  style.
- Red-first (Plan AC-005): the tool-level cases fail (currently `TransportError`) until row 01
  lands.
- Expected outputs follow row 01's contract: `detail` body, `result` body, and non-JSON body
  fallback.

## Design decisions

- Parametrize the five tool-level statuses with a `{"detail": "no such file"}` body and assert the
  returned result's `is_error is True`, `error_type == "tool"`, `output` contains the reason, and
  `server_key` is set — the full REQ-001 contract in one parametrized test.
- Keep the transport-set cases as separate tests (not merged) so a regression in either direction
  fails unambiguously.

## Alternatives considered

- Assert only "no exception raised" — rejected: REQ-001 fixes the result fields; the parametrized
  asserts are the contract.

## Implementation
### Target file
`tests/shared/test_http_transport.py`

### Procedure
Append `TestToolLevelStatusClassification` (new) at the end of the module.

### Method
- `test_tool_level_status_returns_tool_error_result` (new), parametrized over `400/403/404/409/422`
  with body `{"detail": "no such file"}`: result (not `TransportError`); `is_error True`,
  `error_type == "tool"`, `"no such file" in output`, `request_id` from the mocked header when set.
- `test_tool_level_status_with_result_body` (new): `403` with `{"result": "denied by policy"}` →
  output carries `denied by policy`.
- `test_tool_level_status_with_malformed_body` (new): `422` with body `not-json` → result returned,
  output is the raw text, no `TransportError`, no `ValueError` (row 01 tolerant parsing).
- `test_401_still_transport_error` (new): `401` → `pytest.raises(TransportError)` (REQ-003).
- `test_5xx_still_transport_error` (new): `500` → `TransportError`; the mocked call count shows no
  retry (health-failure path preserved).
- `test_write_tool_ambiguous_status_gate_unchanged` (new): `write_file` with `503` → the fail-closed
  `TransportError` message contains `retry suppressed` (REQ-004) and only one HTTP attempt was made.

### Details
- Reuse the module's existing helper that wraps `httpx.MockTransport` and constructs
  `HttpTransport(base_url, auth_token=..., server_key=...)` with the same kwargs as the existing
  tests.

## Compatibility considerations

- `tests/mcp_servers/*` unaffected (Option B rows not modified); MCP integration tests run in the
  validation plan unchanged.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_http_transport.py` — tool-level cases red before row 01 lands.
- `uv run ruff format`, `uv run ruff check` on the touched file; `uv run mypy --no-namespace-packages`
  per the Plan's validation plan; coverage via `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- All six new tests pass with row 01 applied; every pre-existing test in the module passes
  unchanged.

## Out of Scope

- Registry-level cascade proof (row 03); docs (row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestToolLevelStatusClassification` (new) tests (tool-level cases red before row 01 lands) | Pending | — | — | Plan Phase 2, AC-005 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (tool-level statuses return), REQ-003 (401/5xx stay transport), REQ-004 (fail-closed gate)
- **Source issue**: issues/20261101-073450_healthcascade001_tool-4xx-trips-circuit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-141054_healthcascade001_tool-4xx-trips-circuit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132712
- **Related target files**: tests/shared/test_http_transport.py
