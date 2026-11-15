## Goal

Add a unique `X-Idempotency-Key` header to each side-effecting `POST /v1/call_tool`
in `tests/mcp_servers/git/test_git_security_compliance.py` so the REQ-004 idempotency
boundary no longer rejects these keyless calls with 422. (fallout of `REQ-001`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Defining `ALL_SIDE_EFFECTING_TOOLS` (row 01, `REQ-001`) activates the previously
  inert `_idempotency_key_middleware` in `scripts/mcp_servers/server.py`, which now
  rejects any keyless side-effecting `POST /v1/call_tool` with 422 before the route
  handler runs.
- This file has an autouse fixture `_disable_dispatch_duplicate_cache` that sets
  `dispatch._is_side_effecting` to always return `False` for every test. That only
  disables dispatch's dedup duplicate-cache; it does **not** disable the REQ-004
  middleware, whose gate reads `ALL_SIDE_EFFECTING_TOOLS` directly. A key is still
  required.
- Side-effecting tools here are `git_checkout`, `git_pull`, and `git_push`
  (`GIT_WRITE_TOOLS`). `git_status` is a read tool and is unaffected.

## Design decisions

- Add the header to the `git_checkout`, `git_pull`, and `git_push` POSTs only; leave
  the `git_status` POSTs unchanged.

## Alternatives considered

- Relying on the existing `_disable_dispatch_duplicate_cache` fixture to cover this.
  Rejected: the fixture disables dedup, not the middleware, so keyless side-effecting
  POSTs are still rejected with 422.
- Patching `server.py` to exempt tests. Rejected: the boundary must stay; the tests
  are the fallout and must carry their own keys.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_security_compliance.py`

### Procedure
1. Find every `client.post("/v1/call_tool", ...)` whose `"name"` is `git_checkout`,
   `git_pull`, or `git_push`.
2. On each such call that lacks an `x-idempotency-key` header, add a
   `headers={"x-idempotency-key": <unique>}` argument. Use a non-empty value; since
   the autouse fixture disables dedup here, uniqueness is not strictly required by
   the dedup store, but a distinct value per call keeps behavior consistent with the
   other fallout rows.
3. Leave every `git_status` POST unchanged.

### Method
Use the FastAPI `TestClient.post(..., headers={...})` argument. These POSTs live in
the `TestPostConditionBypassPrevention`, `TestCompletePipelineCoverage`, and
`TestLiveCallToolAuthorization` classes.

### Details

- The middleware runs before the route handler regardless of the dispatch fixture, so
  the side-effecting POSTs are rejected without a key and must receive one.
- A whitespace-only key counts as missing; supply a non-empty literal.

## Compatibility considerations
N/A: test-only change; does not touch `scripts/` and does not alter the existing
autouse fixture.

## Security considerations
The fix preserves the REQ-004 fail-closed-on-writes boundary and the existing
dedup-disabling fixture; it does not weaken either. Each side-effecting call still
carries a key.

## Rollback considerations
N/A: revert the commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected |
|---|---|---|---|
| `tests/mcp_servers/git/test_git_security_compliance.py` | Unit: side-effecting POSTs carry a key; boundary satisfied | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py` | all tests pass (no 422 from the middleware) |

## Completion criteria

- Every `git_checkout`, `git_pull`, and `git_push` POST carries a non-empty
  `x-idempotency-key`.
- The `git_status` POSTs are left unchanged; the autouse fixture is untouched.
- The full file passes under `pytest`.

## Out of Scope

- Modifying `server.py` or the middleware.
- Altering the `_disable_dispatch_duplicate_cache` fixture.
- Adding keys to the read-tool (`git_status`) POSTs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add a unique X-Idempotency-Key header to each side-effecting git_checkout/git_pull/git_commit POST | Completed | 20261116-071355 | 20261116-071355 |  |
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
- **Related target files**: `tests/mcp_servers/git/test_git_security_compliance.py`