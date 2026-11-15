## Goal

Add a unique `X-Idempotency-Key` header to the side-effecting `POST /v1/call_tool`
in `tests/mcp_servers/git/test_mcp_git.py` so the REQ-004 idempotency boundary no
longer rejects these keyless calls with 422. (fallout of `REQ-001`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Defining `ALL_SIDE_EFFECTING_TOOLS` (row 01, `REQ-001`) activates the previously
  inert `_idempotency_key_middleware` in `scripts/mcp_servers/server.py`, which now
  rejects any keyless side-effecting `POST /v1/call_tool` with 422 before the route
  handler runs.
- The probe in `test_advertised_enabled_registered_reachable_sets_match` posts to
  every advertised git tool name in a single dynamic loop, including write tools
  (`git_add`, `git_commit`, `git_checkout`) that are members of
  `ALL_SIDE_EFFECTING_TOOLS` alongside read tools such as `git_status`.

## Design decisions

- Add the header to the single dynamic-loop POST; read tools ignore a present key,
  so one header covers both categories without changing the assertion.

## Alternatives considered

- Patching `server.py` to exempt tests. Rejected: the boundary must stay; the tests
  are the fallout and must carry their own keys.

## Implementation
### Target file
`tests/mcp_servers/git/test_mcp_git.py`

### Procedure
1. Locate the dynamic probe POST inside
   `test_advertised_enabled_registered_reachable_sets_match`, which iterates the
   advertised tool `name` over one `client.post("/v1/call_tool", ...)`.
2. Add a `headers={"x-idempotency-key": <value>}` argument to that POST. Derive the
   value from the loop variable `name` (for example
   `f"{server_key}-{name}"`) so each iteration carries a distinct key and the dedup
   store never sees a repeated key carrying different content.

### Method
Use the FastAPI `TestClient.post(..., headers={...})` argument.

### Details

- The middleware runs before the route handler, so the write-tool iterations are
  rejected without a key and must receive one.
- Deriving the key from `name` avoids an intra-loop dedup collision that a single
  shared key could cause if the store is keyed on the key alone.
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
| `tests/mcp_servers/git/test_mcp_git.py` | Unit: probe POST carries a per-name key; boundary satisfied | `uv run pytest tests/mcp_servers/git/test_mcp_git.py` | all tests pass (no 422 from the middleware) |

## Completion criteria

- The dynamic-loop POST in `test_advertised_enabled_registered_reachable_sets_match`
  carries a per-`name` `x-idempotency-key`.
- The full file passes under `pytest`.

## Out of Scope

- Modifying `server.py` or the middleware.
- Changing the `advertised == enabled == registered == reachable` assertion.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add a per-name unique X-Idempotency-Key header to the dynamic-loop call_tool POST | Completed | 20261116-071355 | 20261116-071355 |  |
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
- **Related target files**: `tests/mcp_servers/git/test_mcp_git.py`