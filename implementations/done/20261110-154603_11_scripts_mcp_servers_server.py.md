## Goal

Remove the test-only authentication bypass `accept_all_for_tests` from `attach_auth_middleware` and delete the unused `MCPServer` helpers `list_tools()`, `list_tools_with_server_key()` and the base `health()` (REQ-005, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

Edit `scripts/mcp_servers/server.py` and its companion `tests/mcp_servers/test_mcp_server_base.py`. `tests/mcp_servers/mdq/test_mdq_routing.py` and `tests/mcp_servers/test_require_auth_token.py` are separate Plan rows; the `mdq_server.py` docstring is a separate row.

## Assumptions

- Phase 2 of the Plan. No production caller passes `accept_all_for_tests`: every server module routes its token through `require_auth_token()` (`tests/mcp_servers/test_require_auth_token.py` globs the server sources).
- Deleting the base `health()` (not making it abstract) is the Plan's default (UNK-02); servers serve `/health` from module-level handlers, and `rg` found no caller outside `tests/mcp_servers/mdq/test_mdq_routing.py` and the companion test. If the maintainer prefers abstract, restore `health` as an abstract method implemented by `CiCdMCPServer` and `MdqMCPServer` before executing.
- Out-of-repository callers of the removed helpers cannot be seen (UNK-03); the stop rule applies if one is reported.
- `HEALTH_STATUS_OK` and `HEALTH_STATUS_DEGRADED` (imported at line 24) are used only by the base `health()`; the import is removed with it. `Any` stays (used by `ToolArgs`).

## Design decisions

- With the flag gone, `_is_authorized` returns False for an empty token: every request gets 401. That is already the default behavior; the change removes the opt-out only.
- The `attach_auth_middleware` docstring is rewritten to state that an empty token rejects every request and that production servers refuse to start with one (`require_auth_token`).

## Alternatives considered

Keeping the flag as a private test hook was rejected (a production module must contain only production behavior). A test-only fixture in `tests/` that builds a middleware stack was unnecessary: tests inject a non-empty dummy token.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
1. Change the signature of `attach_auth_middleware` (line 96) to `(app, token)`, removing the keyword-only `accept_all_for_tests` parameter (lines 99-100) and rewrite the docstring (lines 101-120).
2. In `_is_authorized` (line 122) replace `return accept_all_for_tests` with `return False` and fix its docstring.
3. Delete `MCPServer.list_tools` (line 194), `MCPServer.list_tools_with_server_key` (line 203) and `MCPServer.health` (line 218) with their docstrings.
4. Remove the now-unused `from mcp_servers.health_response import HEALTH_STATUS_DEGRADED, HEALTH_STATUS_OK` import (line 24).

### Method
- Edit by symbol; keep `dispatch`, `_enforce_startup_posture_gate`, `run_http` and `require_auth_token` untouched.
- Afterwards `rg -n "accept_all_for_tests|list_tools_with_server_key|def list_tools\(self|HEALTH_STATUS" scripts/mcp_servers/server.py` returns nothing, and `rg -n accept_all_for_tests scripts tests` returns nothing once the companion and the other test rows land (AC-05).

### Details
- `mcp_tools` class attribute stays: subclasses declare it and `rg` shows it is read elsewhere (check with `rg -n "mcp_tools" scripts` before deciding; if it becomes unused by the removed helpers only, leave it, as removal is not in the Plan).
- No change to the 401 response body or the `X-Request-Id` handling.

### Companion test files
- `tests/mcp_servers/test_mcp_server_base.py`
  - Procedure: Delete `TestListTools` (line 198) and the base `health()` tests (lines 202-236) and the `accept_all_for_tests` argument of `_make_test_app` (line 249); rewrite `test_no_token_allows_any_request` (line 269), `test_no_token_response_contains_request_id`, `test_each_request_gets_unique_id` and `test_empty_token_accept_all_is_not_a_supported_mode` to use a non-empty dummy token, and add one case asserting an empty token returns 401 for every request; update the module docstring (lines 2-3).
  - Validation: `uv run pytest tests/mcp_servers/test_mcp_server_base.py -v`

## Compatibility considerations

`attach_auth_middleware(app, token, accept_all_for_tests=...)` now raises `TypeError`; the only in-repo callers are the ten server modules (token argument only) and tests (own rows). No behavior change for production servers.

## Security considerations

Removes an authentication bypass reachable only by a code change; an empty token continues to reject all requests (fail closed).

## Rollback considerations

`git revert`; no persisted state.

## Validation plan

- `uv run pytest tests/mcp_servers/test_mcp_server_base.py tests/mcp_servers/test_require_auth_token.py tests/mcp_servers/mdq/test_mdq_routing.py -v`.
- `uv run ruff format`/`ruff check` on both files; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports`; `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` (Plan final validation).

## Completion criteria

- `accept_all_for_tests`, `list_tools`, `list_tools_with_server_key` and base `health` are gone from the source; the companion test passes with non-empty dummy tokens plus an explicit empty-token 401 case.

## Out of Scope

- Server-side audit and the MCP authentication ADR (`issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md`).
- `mdq_server.py` docstring, `test_mdq_routing.py` and `test_require_auth_token.py` (own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the bypass flag from `attach_auth_middleware` and `_is_authorized` | Done | 20261110-172551 | 20261110-172551 | REQ-005 |
| 2 | Delete `list_tools`, `list_tools_with_server_key`, base `health` and the unused import | Done | 20261110-172551 | 20261110-172551 | REQ-006; rg check clean |
| 3 | Update the companion test file (dummy tokens, empty-token 401 case, deleted helper tests) | Done | 20261110-172551 | 20261110-172551 | Verification finding: 401 does not carry X-Request-Id (denial precedes call_next); `test_no_token_response_contains_request_id` rewritten to assert header absence per the Details rule "No change to the X-Request-Id handling". New case `test_empty_token_denies_request_without_credentials` added. `TestListTools`/`TestHealth` deleted; `_EmptyServer` fixture left in place (policy: no unrelated cleanup). |
| 4 | Run ruff, mypy, lint-imports and the MCP server tests | Done | 20261110-172551 | 20261110-172551 | ruff+mypy clean; test_mcp_server_base.py+test_require_auth_token.py 62 passed; test_mdq_rag_boundary.py 5 passed; test_mdq_routing.py 3 red until row 35 lands (allowed red) |

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
- **Requirement ID**: `REQ-005`, `REQ-006`
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/mcp_servers/server.py`, `tests/mcp_servers/test_mcp_server_base.py`
