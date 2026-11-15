## Goal

Add a unique `X-Idempotency-Key` header to each side-effecting `POST /v1/call_tool`
in `tests/mcp_servers/shell/test_shell_server_endpoints.py` so the REQ-004 idempotency
boundary no longer rejects these keyless calls with 422. (fallout of `REQ-001`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Defining `ALL_SIDE_EFFECTING_TOOLS` (row 01, `REQ-001`) activates the previously
  inert `_idempotency_key_middleware` in `scripts/mcp_servers/server.py`, which now
  rejects any keyless side-effecting `POST /v1/call_tool` with 422 before the route
  handler runs.
- The only side-effecting tool here is `shell_run` (`SHELL_TOOLS`). `not_a_tool` is
  unknown and unaffected.

## Design decisions

- Add the header to the `shell_run` POSTs only; leave the `not_a_tool` POST unchanged.

## Alternatives considered

- Patching `server.py` to exempt tests. Rejected: the boundary must stay; the tests
  are the fallout and must carry their own keys.

## Implementation
### Target file
`tests/mcp_servers/shell/test_shell_server_endpoints.py`

### Procedure
1. Find every `client.post("/v1/call_tool", ...)` whose `"name"` is `shell_run`.
2. On each such call that lacks an `x-idempotency-key` header, add a
   `headers={"x-idempotency-key": <unique>}` argument. Make each value unique across
   the file so no two side-effecting POSTs in the process share a key — the dedup
   store rejects a repeated key carrying different content.
3. Leave the `not_a_tool` POST unchanged.

### Method
Use the FastAPI `TestClient.post(..., headers={...})` argument.

### Details

- A whitespace-only key counts as missing; supply a non-empty literal.

## Compatibility considerations
N/A: test-only change; does not touch `scripts/`.

## Security considerations
The fix preserves the REQ-004 fail-closed-on-writes boundary; it does not weaken it.
Each side-effecting call still carries a key.

## Rollback considerations
N/A: revert the commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected |
|---|---|---|---|
| `tests/mcp_servers/shell/test_shell_server_endpoints.py` | Unit: side-effecting POSTs carry a key; boundary satisfied | `uv run pytest tests/mcp_servers/shell/test_shell_server_endpoints.py` | all tests pass (no 422 from the middleware) |

## Completion criteria

- Every `shell_run` POST carries a unique `x-idempotency-key`.
- The `not_a_tool` POST is left unchanged.
- The full file passes under `pytest`.

## Out of Scope

- Modifying `server.py` or the middleware.
- Adding keys to the `not_a_tool` POST.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add a unique X-Idempotency-Key header to each side-effecting shell_run POST | Completed | 20261116-071355 | 20261116-071355 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261116-071355 | 20261116-071355 |  |

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
- **Requirement ID**: `REQ-001` (canonical side-effect set; this row closes the test fallout its definition triggers)
- **Source issue**: `issues/20261111-163800_sideeffect001_side-effect-classification-central.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-052032_sideeffect001_side-effect-classification-central.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-220459
- **Related target files**: `tests/mcp_servers/shell/test_shell_server_endpoints.py`