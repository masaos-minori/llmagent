## Goal

Replace the inline `if not _cfg.auth_token: raise RuntimeError(...)` guard in `scripts/mcp_servers/shell/shell_server.py` with a call through the shared enforcement point `require_auth_token()`, so the shell server refuses an empty token via the single consolidated path instead of a per-file copy (`REQ-001`/`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The plan resolves to approach (a): every server routes its token through `require_auth_token()` (`UNK-01`).
- `require_auth_token(label, env_var, token)` raises `RuntimeError(f"{label}: auth_token is empty; set {env_var} ...")` and returns the token otherwise (`scripts/mcp_servers/server.py` `L137-151`); calling it at module level preserves the current import-time refusal.
- The shell server reads its token from `_cfg.auth_token`; the label/env pair is `("shell-mcp", "MCP_SHELL_AUTH_TOKEN")`.

## Design decisions
- **Call `require_auth_token` in place of the inline guard.** Insert `require_auth_token("shell-mcp", "MCP_SHELL_AUTH_TOKEN", _cfg.auth_token)` where the inline guard currently is, immediately before `attach_auth_middleware(...)`. The message produced is byte-identical to the current inline guard, so no test asserting the wording changes.
- **Add the import.** Add `require_auth_token` to the `from mcp_servers.server import (...)` block (`shell_server.py` `L35-39`) alongside `attach_auth_middleware`.

## Alternatives considered
- **Keep the inline guard and add only a structural checker (approach b).** Rejected by the plan — it leaves the duplication the issue flags. Approach (a) removes the drift.

## Implementation
### Target file
`scripts/mcp_servers/shell/shell_server.py`
### Procedure
1. Add `require_auth_token` to the `from mcp_servers.server import (` block at `L35-39`.
2. Delete the inline guard `if not _cfg.auth_token:\n    raise RuntimeError(\n        "shell-mcp: auth_token is empty; set MCP_SHELL_AUTH_TOKEN to a non-empty "\n        "value (the server does not start without Bearer authentication)"\n    )` at `L120-125`.
3. Insert `require_auth_token("shell-mcp", "MCP_SHELL_AUTH_TOKEN", _cfg.auth_token)` on its own line immediately before `attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token)` at `L125`.

### Method
Two localized edits — the import addition and the guard→call swap — at the bottom of the module; no other function changes.

### Details
Current import block, `shell_server.py` `L35-39`:
```python
from mcp_servers.server import (
    MCPServer,
    ToolArgs,
    _FastAPIApp,
    attach_auth_middleware,
    build_tools_response,
```
Add `require_auth_token` alphabetically after `attach_auth_middleware`.
Current guard + attach, `shell_server.py` `L119-125`:
```python
if not _cfg.auth_token:
    raise RuntimeError(
        "shell-mcp: auth_token is empty; set MCP_SHELL_AUTH_TOKEN to a non-empty "
        "value (the server does not start without Bearer authentication)"
    )
attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token)
```
Replace the `if not ...:` block with:
```python
require_auth_token("shell-mcp", "MCP_SHELL_AUTH_TOKEN", _cfg.auth_token)
```

### Companion test files
- `tests/mcp_servers/shell/test_shell_server_auth.py`
  - Procedure: preserve the existing empty-token refusal assertion; no change needed because `require_auth_token()` still raises `RuntimeError` at import time with the same message.
  - Validation: `uv run pytest tests/mcp_servers/shell/test_shell_server_auth.py` passes after the `shell_server.py` consolidation.

## Compatibility considerations
- Behavior is unchanged for callers: an empty token still raises `RuntimeError` at import time with the same message; a non-empty token still proceeds to `attach_auth_middleware`.

## Security considerations
- No change to the security posture: the empty-token refusal is preserved and now shares one implementation with the other nine servers.

## Rollback considerations
- Revert the commit; the two edits are isolated to the import block and the module-level auth call.

## Validation plan
- `uv run pytest tests/mcp_servers/shell/test_shell_server_auth.py` — empty-token refusal still asserted.
- `uv run pytest tests/mcp_servers/test_require_auth_token.py::test_empty_token_prevents_every_server_from_importing` — parametrized over the shell module; passes.
- `uv run ruff check scripts/` — clean.

## Completion criteria
- `REQ-003`: importing `shell_server` with an empty `MCP_SHELL_AUTH_TOKEN` raises `RuntimeError` naming `shell-mcp` and the variable.
- The shell server now calls `require_auth_token()` rather than an inline guard.

## Out of Scope
- Changing the shell server's token source (`_cfg.auth_token`) or environment-variable name.
- The middleware accept-all default — handled in the `server.py` procedure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261108-170747 | 20261108-170747 | — |
| 2 | Add or update tests per Validation plan | Completed | 20261108-170747 | 20261108-170747 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261108-170747 | 20261108-170747 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261108-170747 | 20261108-170747 | — |

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
- **Requirement ID**: `REQ-001` (shared enforcement point), `REQ-003` (import-time empty-token refusal preserved)
- **Source issue**: `issues/20261107-132052_mcpstartup003_auth-guard-single-point.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-214719_mcpstartup003_auth-guard-single-point.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-083903
- **Related target files**: `scripts/mcp_servers/shell/shell_server.py`, `tests/mcp_servers/shell/test_shell_server_auth.py`
