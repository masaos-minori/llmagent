## Goal

Add a unique `X-Idempotency-Key` header to each side-effecting `POST /v1/call_tool`
in `tests/mcp_servers/file/test_call_tool_validation.py` so the REQ-004 idempotency
boundary no longer rejects these keyless calls with 422. (fallout of `REQ-001`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Defining `ALL_SIDE_EFFECTING_TOOLS` (row 01, `REQ-001`) activates the previously
  inert `_idempotency_key_middleware` in `scripts/mcp_servers/server.py`, which now
  rejects any keyless side-effecting `POST /v1/call_tool` with 422 before the route
  handler runs.
- Side-effecting tools here are `write_file` (`WRITE_TOOLS`), `delete_file`
  (`DELETE_TOOLS`), and `git_commit` (`GIT_WRITE_TOOLS`). Read tools
  `list_directory` and `git_status` are not members and are unaffected.

## Design decisions

- Add the header to the `write_file`, `delete_file`, and `git_commit` POSTs only;
  leave the `list_directory` and `git_status` POSTs unchanged.

## Alternatives considered

- Patching `server.py` to exempt tests. Rejected: the boundary must stay; the tests
  are the fallout and must carry their own keys.

## Implementation
### Target file
`tests/mcp_servers/file/test_call_tool_validation.py`

### Procedure
1. Find every `client.post("/v1/call_tool", ...)` whose `"name"` is
   `write_file`, `delete_file`, or `git_commit`.
2. On each such call that lacks an `x-idempotency-key` header, add a
   `headers={"x-idempotency-key": <unique>}` argument. Make each value unique across
   the file so no two side-effecting POSTs in the process share a key — the dedup
   store rejects a repeated key carrying different content.
3. Leave every `list_directory` and `git_status` POST unchanged.

### Method
Use the FastAPI `TestClient.post(..., headers={...})` argument. The disabled-gate
POSTs reach the middleware before the disabled-gate handler, so they too need a key.

### Details

- The middleware runs before the disabled-gate route handler, so the disabled-gate
  POSTs of `write_file`, `delete_file`, and `git_commit` are rejected without a key
  and must receive one even though they assert a "Tool disabled" result.
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
| `tests/mcp_servers/file/test_call_tool_validation.py` | Unit: side-effecting POSTs carry a key; boundary satisfied | `uv run pytest tests/mcp_servers/file/test_call_tool_validation.py` | all tests pass (no 422 from the middleware) |

## Completion criteria

- Every `write_file`, `delete_file`, and `git_commit` POST carries a unique
  `x-idempotency-key`.
- The read-tool (`list_directory`, `git_status`) POSTs are left unchanged.
- The full file passes under `pytest`.

## Out of Scope

- Modifying `server.py` or the middleware.
- Adding keys to the read-tool (`list_directory`, `git_status`) POSTs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add a unique X-Idempotency-Key header to each side-effecting write_file/delete_file/git_commit POST | Completed | 20261116-071355 | 20261116-071355 |  |
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
- **Related target files**: `tests/mcp_servers/file/test_call_tool_validation.py`