## Goal

Give the Agent a control client for the two control endpoints that sends the control Bearer token and reports every failure as a typed result instead of raising or leaking response bodies.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: a new synchronous `ControlClient` (new) class and `ControlCallResult` (new) dataclass in this module. `HttpTransport.call` and its retry/transport-error behavior are unchanged. The file is about 14 KB.

## Assumptions

- Verified: `build_turn_control_message` runs synchronously and is called from the async `_run_execute_stage`, i.e. inside a running event loop; an async transport cannot be awaited there, so the control client is synchronous (Plan corrected in this cycle).
- Verified: `HttpTransport` holds an `httpx.AsyncClient` and registers `auth_token` with `register_secret`; the control client mirrors the secret registration.

## Design decisions

- `ControlCallResult` (new) (frozen dataclass): `ok`, `status_code`, `payload` (dict or None), `error` (short fixed label: control_unconfigured, `timeout`, `transport_error`, bad_response, `http_<status>`).
- `ControlClient(base_url, control_token, timeout_sec=3.0)` builds a short-timeout `httpx.Client` per call; `get_call_state(key)` issues GET `/v1/call_state/{key}` and `request_reconcile(key)` issues POST `/v1/call_state/{key}/reconcile`, URL-quoting the key.
- An empty control token returns control_unconfigured without any HTTP send.

## Alternatives considered

Rejected: async methods on `HttpTransport` (unusable from the synchronous stale-classification path); rejected: modifying `build_turn_control_message` to be async (touches the adapter and engine beyond this Plan).

## Implementation
### Target file
`scripts/shared/http_transport.py`

### Procedure
1. Add `ControlCallResult` (new) and `ControlClient` (new) below `HttpTransport`.
2. Implement both methods with fixed-label error mapping; parse JSON only on 2xx and require a dict.
3. Register the control token with `register_secret` in the constructor.

### Method
Use `httpx.Client` as a context manager inside each method so no connection outlives the call; catch `httpx.TimeoutException` and `httpx.RequestError` and map to labels. Never include `resp.text` in a result.

### Details
- Never retry: control reads are single attempts; the caller decides.
- Do not send `X-Idempotency-Key` or the tool token on control requests.

## Compatibility considerations

Additive classes; no existing behavior changes.

## Security considerations

The control Bearer token is the only credential sent; the tool token never reaches control paths; errors carry fixed labels, not raw bodies or exception text.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_mcp_call_recovery.py tests/shared/test_http_transport.py`

## Completion criteria

- `ControlClient` (new) returns typed results for success, timeout, transport failure, non-2xx, and unconfigured token, and never raises on those paths.

## Out of Scope

Recovery decisions (row 11) and server endpoints (row 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-141607 | 20261123-141607 | ControlCallResult and ControlClient added below HttpTransport; fixed-label errors, single attempt, per-call context manager, register_secret in the constructor |
| 2 | Add or update tests per Validation plan | Completed | 20261123-141607 | 20261123-141607 | TestControlClient added in the existing test module (7 tests); 35 tests green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-141607 | 20261123-141607 | ruff, mypy, lint-imports, bandit, module-size gate pass |

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
- **Requirement ID**: `REQ-001` (control endpoints and response shape), `REQ-005` (ledger-state to Agent-state mapping and Agent recovery)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `scripts/shared/http_transport.py`
