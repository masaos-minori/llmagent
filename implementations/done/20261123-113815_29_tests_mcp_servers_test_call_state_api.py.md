## Goal

Test the control API end to end through a FastAPI TestClient: the authorization matrix, response shape, reconcile refusals, and operator review.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the new test module. Uses a small app, a real `DedupStore` in `tmp_path`, `configure_control`, and `attach_control_api`.

## Assumptions

- Verified: `attach_auth_middleware` is the shipped way to add tool auth; the test attaches it first and the control API second, matching production order.

## Design decisions

- Fixture builds the app with tool token `tool-secret` and control token `control-secret`, and seeds rows through `try_acquire_execution`, `record_completed`, and expired leases via `now_epoch`.

## Alternatives considered

N/A: plain pytest with TestClient.

## Implementation
### Target file
`tests/mcp_servers/test_call_state_api.py` (new)

### Procedure
1. Authorization matrix: control token accepted; tool token rejected (401); no header 401; empty configured token fails closed (401 even with an empty Bearer); tool paths still require the tool token and reject the control token.
2. Shape: a completed row returns the closed fields and `result_class` in the four-class vocabulary; the JSON contains no argument values, no `/home` or `/opt` paths, and no token strings; a failed row reports `handler_failed` with the error class.
3. Reconcile: live lease refuses (409, `lease_live`); exhausted attempts refuses with operator review; expired lease with no registered reconciler moves the row to interrupted and returns `operator_review`; a registered reconciler returning `ambiguous` leaves the row unchanged with operator review; `evidence_found` moves it and writes one history row; a completed row returns `reused_completed` without mutation.
4. Unknown key returns 404 `unknown_key`; a malformed key returns 422.

### Method
Reset module state between tests (`configure_control` with a fresh store) and clear the reconciler registry.

### Details
- Assert that response bodies are validated by the models from row 08 (extra fields forbidden).

## Compatibility considerations

N/A: new tests.

## Security considerations

N/A: tests only; dummy tokens.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/test_call_state_api.py tests/mcp_servers/test_mcp_server_base.py`

## Completion criteria

- All matrix, shape, and reconcile cases pass and fail when the control token check or a refusal is removed.

## Out of Scope

Per-tool reconcilers and the Agent client.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-144724 | 20261123-144724 | test module written: authorization matrix, response shape, reconcile refusals and operator review, 404/422; module state reset per test, rows seeded through the ledger entry points on tmp_path |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-144724 | 20261123-144724 | 19 tests green with test_mcp_server_base.py and test_require_auth_token.py; completion criteria checked by removing the control-token check (3 auth tests fail) and the live-lease refusal (1 test fails), then restored |

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
- **Requirement ID**: `REQ-001` (control endpoints and response shape), `REQ-002` (separate control Bearer authorization), `REQ-004` (reconciler contract)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `tests/mcp_servers/test_call_state_api.py`
