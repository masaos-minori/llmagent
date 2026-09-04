## Goal
Confirm (no logic change) `attach_auth_middleware()`'s 401 behavior is
correct when a token is configured, and add a docstring note that
empty-token accept-all is a startup-time-rejected state, not a supported
production mode.

## Scope
- **In-Scope**: `attach_auth_middleware()`'s docstring (verified
  2026-09-04, lines 94-100).
- **Out-of-Scope**: `_is_authorized()` (lines 104-108) and `_auth_middleware()`
  (lines 110-119) logic itself — REQ-003 explicitly requires no logic
  change here, only confirmation and a documentation update; this row's
  loopback-binding validation (added by `plans/done/20260903-091921_plan.md`'s
  own row 2 for this same file) is a separate, unrelated concern handled by
  that Plan.

## Assumptions
- REQ-003 is a confirm-only requirement for the runtime logic: `_is_authorized()`'s
  `if not token: return True` / `return request.headers.get("Authorization",
  "") == f"Bearer {token}"` (lines 106-108) already correctly returns 401 via
  `_auth_middleware()` (line 115-116) for a missing/mismatched Bearer header
  when a token is configured — confirmed by direct read 2026-09-04, no
  change needed to this logic itself.
- This file is also a target of `plans/done/20260903-091921_plan.md`
  (loopback-only bind-address validation, that Plan's own row 2, already
  implemented via a separate implementation-procedure document under a
  different Source plan) — the two Plans edit non-overlapping regions of
  this file (`run_http()`'s bind-address check vs. this row's
  `attach_auth_middleware()` docstring); no conflict, but both should be
  applied before a final regression run of this file's full test suite.

## Design decisions
- Add a docstring sentence to `attach_auth_middleware()` stating that an
  empty `token` argument's accept-all behavior is retained here (the
  middleware itself is not the enforcement point), but that
  `scripts/agent/startup_validation.py` (row 3) now rejects any
  configuration that would produce an empty token before this middleware
  ever runs in a real Agent-managed startup — clarifying that this
  function's own permissive default is intentional (needed for the
  function's standalone testability, e.g. tests constructing a server with
  no token by design) and is not itself a production-mode gate.

## Alternatives considered
- Removing the `if not token: return True` accept-all branch from
  `_is_authorized()` entirely, forcing every call to require a non-empty
  token: rejected — REQ-003 explicitly scopes this row to "no logic
  change"; removing this branch would be a REQ-001-flavored behavioral
  change that this Plan already places at the startup/config-validation
  layer (rows 1, 3), not inside the HTTP middleware itself, per the Plan's
  Design section's separation of concerns.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
Add a clarifying sentence to `attach_auth_middleware()`'s docstring
(verified 2026-09-04, lines 95-100).

### Method
Direct `Edit`.

### Details
Current (verified 2026-09-04, lines 94-100):
```python
def attach_auth_middleware(app: _FastAPIApp, token: str) -> None:
    """Register Bearer-token auth + X-Request-Id middleware on a FastAPI app.

    When token is non-empty, requests without a matching Authorization header
    receive a 401 response.  When token is empty, auth is skipped and the
    middleware only injects the X-Request-Id response header.
    """
```
After:
```python
def attach_auth_middleware(app: _FastAPIApp, token: str) -> None:
    """Register Bearer-token auth + X-Request-Id middleware on a FastAPI app.

    When token is non-empty, requests without a matching Authorization header
    receive a 401 response.  When token is empty, auth is skipped and the
    middleware only injects the X-Request-Id response header.

    An empty token is not a supported production configuration: Agent
    startup (scripts/agent/startup_validation.py) rejects any MCP server
    configuration with an empty auth_token before this middleware would ever
    run for a real Agent-managed server. The accept-all fallback above
    exists for this function's own standalone testability, not as a
    supported deployment mode.
    """
```

## Compatibility considerations
No behavioral change — docstring-only edit. Coordinate with
`plans/done/20260903-091921_plan.md`'s own edit to this same file (different
region, `run_http()`'s bind-address check).

## Security considerations
None directly — documentation clarification only; the actual security
enforcement is rows 1 and 3.

## Rollback considerations
Docstring-only edit under version control; revert via `git revert` if
needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/server.py` | Unit | `uv run pytest tests/mcp_servers/test_mcp_server_base.py -v` | Existing `TestAttachAuthMiddleware` tests (401/200 behavior) pass unchanged |

## Completion criteria
`attach_auth_middleware()`'s docstring documents that empty-token accept-all
is not a supported production mode; no logic change to `_is_authorized()`/
`_auth_middleware()`.

## Out of scope
`_is_authorized()`, `_auth_middleware()`, and `run_http()`'s loopback-binding
validation (owned by `plans/done/20260903-091921_plan.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Docstring-only; confirm-only requirement per REQ-003 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by row 13 (`tests/mcp_servers/test_mcp_server_base.py`) — no new test required for this row's docstring change itself |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Plan's Documentation Impact: Yes — MCP authentication reference docs, sequenced after this Plan lands |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260902-143335_mcpauth_preserve_mandatory_mcp_authentication_under_loopback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-092407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-093656
- **Related target files**: scripts/mcp_servers/server.py
