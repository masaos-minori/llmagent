## Goal

Rewrite the tests in `tests/mcp_servers/web_search/test_web_search_health.py` so they lock
in that `/health` requires the token (instead of asserting the loopback admission) and that
no server passes a keyword to the middleware (`REQ-001`, `REQ-002`; AC-1, AC-2, AC-4).

## Scope

Only `tests/mcp_servers/web_search/test_web_search_health.py`. The four classes that test
`health.py` directly (`TestProviderHealth`, `TestHealthEndpointWiring`,
`TestBrowserProviderHealth`, `TestBrowserHealthEndpointWiring`) are unchanged and stay.

## Assumptions

- The framework `TestClient` accepts an explicit client source pair
  (`TestClient(app, client=("127.0.0.1", 50000))`), already used in this file, so tests can
  parametrize over loopback IPv4, loopback IPv6, and a remote address.
- The real application reads its token from the environment at import time, so it runs in a
  separate interpreter with `MCP_WEB_SEARCH_AUTH_TOKEN` set.

## Design decisions

- `_guarded_app` loses its `exempt_health_on_loopback` switch and builds the app with the
  default (strict) call shape, matching every other server.
- `TestLoopbackHealthExemption` becomes a parametrized "health requires the token" class
  over client addresses and the three credential cases.
- `TestHealthExemptionOptIn` becomes a pure wiring class: drop the method that asserted the
  keyword was present, keep the shared-token check, and assert that no server passes any
  keyword.

## Alternatives considered

N/A: a test-only rewrite confined to one file; no design family applies beyond the test
strategy already in this file.

## Implementation

### Target file

`tests/mcp_servers/web_search/test_web_search_health.py`

### Procedure

1. Rewrite `_guarded_app` (current lines 221-237): drop the
   `*, exempt_health_on_loopback: bool` parameter and the `extra = {...}` dict; call
   `attach_auth_middleware(app, "browser-secret")` with the default strict shape.
2. Replace the `TestLoopbackHealthExemption` class (current lines 240-305) with a new class
   (e.g. `TestHealthRequiresToken`), parametrized over client addresses
   `{_LOOPBACK, ("::1", 50000), _REMOTE}` and the credential cases:
   - `/health` without a token → 401
   - `/health` with a wrong token → 401
   - `/health` with the correct token (`Bearer browser-secret`) → 200
   - `/v1/protected` still requires the correct token even on loopback (401 then 200).
3. In `TestHealthExemptionOptIn` (current lines 319-350): delete
   `test_web_search_server_opts_in` (it asserted the keyword was present); keep
   `test_web_search_server_uses_the_shared_token`; generalize
   `test_other_servers_do_not_opt_in` so the class asserts that every
   `attach_auth_middleware` call across all five server files carries no keyword argument,
   and that web-search's second positional argument is the config's `auth_token`.
4. Update `_REAL_APP_SCRIPT` (current lines 353-370): add a `/health` call WITH the shared
   token; update `TestRealAppSharedToken`'s expected dict so `health_from_loopback` (without
   token) is now `401` and add `health_with_token` == `200`.

### Method

Apply the four edits, run the file, then run the leftover-reference search.

### Details

- The current `_guarded_app` builds the switch via
  `extra = {"exempt_health_on_loopback": True} if exempt_health_on_loopback else {}` and
  `attach_auth_middleware(app, "browser-secret", **extra)` (lines 226-227).
- Parametrized client addresses reuse the existing `_LOOPBACK` / `_REMOTE` constants and
  the inline `("::1", 50000)` form already used at lines 243-248.
- The real-app script runs at lines 380-403 with
  `MCP_WEB_SEARCH_AUTH_TOKEN=shared-test-token` and `PYTHONPATH` set to the repo root
  (line 384); the health expectation currently asserts `health_from_loopback: 200`, which
  is now `401` because the admission is gone.

## Compatibility considerations

Renamed/removed symbols (`TestLoopbackHealthExemption`, `test_web_search_server_opts_in`,
`_guarded_app`'s parameter) must not be referenced elsewhere in the suite.

## Security considerations

These tests encode the restored security property — `/health` is authenticated from every
client address — rather than documenting the removed bypass.

## Rollback considerations

Revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/web_search/test_web_search_health.py -q`:
  `/health` returns 401 without the token and 200 with it (AC-4); the wiring assertions
  pass.
- `rg -n "exempt_health_on_loopback|_is_loopback_client" scripts tests docs` — no matches
  (AC-2).
- Full sequence per `rules/toolchain.md`.

## Completion criteria

No `exempt_health_on_loopback` or `_is_loopback_client` remain anywhere; the middleware
wiring test passes; the real-application test reports 401 without the token and 200 with it
for `/health`.

## Out of scope

The middleware definition (`scripts/mcp_servers/server.py`), the web-search server
(`scripts/mcp_servers/web_search/web_search_server.py`), the agent poll tests
(`tests/agent/test_http_lifecycle_health_check.py`), and the two documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (`/health` requires the token from every client), `REQ-002` (remove the admission names and opt-in), `REQ-004` (real-application expectation)
- **Source issue**: issues/20261012-185047_mcp006_remove-the-loopback-health-admission-from-the-shared-auth-middleware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-185654_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-185934
- **Related target files**: tests/mcp_servers/web_search/test_web_search_health.py
