# Invoker-level health-cascade tests

## Goal

Add tests to `tests/shared/test_tool_transport_invoker.py` proving three consecutive tool-level
results leave the server `HEALTHY` and a following valid call is dispatched, while transport
statuses still drive `record_failure` (Plan REQ-002 / REQ-007 / AC-005).

## Scope

- New class `TestToolLevelHealthCascade` (new) appended after `TestToolTransportInvoker`.
- Existing tests untouched — `test_success_records_health_success` (:86),
  `test_tool_error_increments_stat_tool_errors` (:104),
  `test_transport_error_records_health_failure` (:136) are the regression baseline.

## Assumptions

- Verified 20261102: the module drives `ToolTransportInvoker` with a real
  `McpServerHealthRegistry` and a mocked transport whose `call` returns canned `ToolCallResult`
  values; `_record_success` (`tool_transport_invoker.py:234-237`) calls
  `registry.record_success` and increments `stat_tool_errors` only for
  `is_error and error_type == "tool"`.
- The mocked `call` returns exactly the row-01 result shape (`is_error=True`,
  `error_type="tool"`), so this file pins the invoker-side consequence (no `record_failure`,
  registry stays `HEALTHY`); row 02 pins that `HttpTransport.call` produces that shape from real
  statuses. Together they cover REQ-002 end to end.
- Red-first (AC-005): with the pre-fix transport these scenarios correspond to `TransportError`
  cascades; the invoker-level tests pass on the mocked shape but are written and landed with this
  Plan's Phase 2, mirroring row 02's red-first status.

## Design decisions

- Use the REAL registry (not a mock) and assert `registry.get_state(server_key) == HEALTHY` after
  three tool-level results — REQ-007's claim is about registry state, not call counts.
- The fourth call returns a normal success result and asserts the transport was called 4 times —
  the "following valid call is sent" half of REQ-007.

## Alternatives considered

- Spy `record_success`/`record_failure` counts only — rejected: call counts miss the circuit-state
  outcome the Issue is about (cooldown self-outage).

## Implementation
### Target file
`tests/shared/test_tool_transport_invoker.py`

### Procedure
Append `TestToolLevelHealthCascade` (new) at the end of the module.

### Method
- `test_three_tool_level_results_keep_server_healthy` (new): mocked `call` side_effect = three
  `ToolCallResult(output="no such file", is_error=True, request_id="", server_key=KEY,
  error_type="tool")` then one success result; run four `invoker.invoke(...)`-equivalent calls;
  assert registry state for `KEY` is `HEALTHY` (no failure recorded), `stat_tool_errors == 3`,
  `stat_transport_errors == 0`, and the transport was called 4 times (the valid call was sent).
- `test_transport_statuses_still_record_failure` (new): mocked `call` raising `TransportError`
  (standing in for `401`/`5xx`, proven at transport level in row 02); assert
  `record_failure` took effect — registry state is no longer `HEALTHY` after the configured
  failure threshold, `stat_transport_errors == 1`, and the returned result carries
  `error_type="transport"`.

### Details
- Reuse the module's existing invoker/registry construction helpers and `ToolCallResult` import
  style; assert on registry state via its public read method (`get_state` / equivalent used by
  `test_health_unavailable_returns_error_result` :54-66).

## Compatibility considerations

- `tests/shared` full-module run must stay green; MCP integration tests run in the validation plan
  unchanged.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_tool_transport_invoker.py` then `uv run pytest tests/shared`
  (Plan regression list).
- `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages` on the touched
  file; coverage via `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- After three tool-level results the registry state is `HEALTHY` and the fourth valid call is
  dispatched; a `TransportError` case still advances `record_failure` and reports
  `error_type="transport"`; all pre-existing tests pass unchanged.

## Out of Scope

- Transport-level status-to-result proof (row 02); docs (row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestToolLevelHealthCascade` (new) tests | Pending | — | — | Land with rows 01-02 (Plan Phase 2) |
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
- **Requirement ID**: REQ-002 (tool-level outcomes use the success path), REQ-007 (three outcomes leave HEALTHY; transport set still fails)
- **Source issue**: issues/20261101-073450_healthcascade001_tool-4xx-trips-circuit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-141054_healthcascade001_tool-4xx-trips-circuit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132712
- **Related target files**: tests/shared/test_tool_transport_invoker.py
