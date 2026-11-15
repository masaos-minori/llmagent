## Goal

Add a unique `X-Idempotency-Key` header to the side-effecting `POST /v1/call_tool`
in `tests/mcp_servers/test_write_dangerous_audit.py` so the REQ-004 idempotency
boundary no longer rejects these keyless calls with 422. (fallout of `REQ-001`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Defining `ALL_SIDE_EFFECTING_TOOLS` (row 01, `REQ-001`) activates the previously
  inert `_idempotency_key_middleware` in `scripts/mcp_servers/server.py`, which now
  rejects any keyless side-effecting `POST /v1/call_tool` with 422 before the route
  handler runs.
- The test is parametrized over `_CASES` (every `(server_key, tool)` pair in
  `_SERVER_TOOLS`). Every tool in `_CASES` is a `WRITE_DANGEROUS` / side-effecting
  tool and is a member of `ALL_SIDE_EFFECTING_TOOLS`, so every parametrized case hits
  the boundary.
- Because the cases run in one process and the real dispatch dedup is active, the
  dedup store rejects a repeated key carrying different content; each case must carry
  a distinct key.

## Design decisions

- Add a per-case unique header to the single parametrized POST; derive the value from
  the test args (`server_key`, `tool`) so each parametrization is distinct.

## Alternatives considered

- Patching `server.py` to exempt tests. Rejected: the boundary must stay; the tests
  are the fallout and must carry their own keys.

## Implementation
### Target file
`tests/mcp_servers/test_write_dangerous_audit.py`

### Procedure
1. Locate the single `client.post("/v1/call_tool", json={"name": tool, "args": args})`
   inside `test_write_dangerous_tool_emits_audit_record`.
2. Add a `headers={"x-idempotency-key": f"{server_key}::{tool}"}` argument so each
   parametrized case carries a distinct key.

### Method
Use the FastAPI `TestClient.post(..., headers={...})` argument.

### Details

- The key is derived from both `server_key` and `tool`, the parametrized test args,
  so no two cases share a key and the dedup store never rejects a repeated key.
- A whitespace-only key counts as missing; the derived value is always non-empty.

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
| `tests/mcp_servers/test_write_dangerous_audit.py` | Unit: each parametrized case carries a distinct key; boundary satisfied | `uv run pytest tests/mcp_servers/test_write_dangerous_audit.py` | all tests pass (no 422 from the middleware) |

## Completion criteria

- The parametrized POST carries a per-case `x-idempotency-key` derived from
  `server_key` and `tool`.
- The full file passes under `pytest`.

## Out of Scope

- Modifying `server.py` or the middleware.
- Changing `_CASES` / `_SERVER_TOOLS` or the audit-record assertions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add a per-case unique X-Idempotency-Key header to the parametrized call_tool POST | Completed | 20261116-071355 | 20261116-071355 |  |
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
- **Related target files**: `tests/mcp_servers/test_write_dangerous_audit.py`