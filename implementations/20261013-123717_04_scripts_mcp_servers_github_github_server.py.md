## Goal
- Make `github-mcp` fail closed: importing the module raises `RuntimeError` when the configured `auth_token` is empty, and otherwise every request, `/health` included, passes through the shared Bearer middleware (REQ-003 startup refusal; REQ-004 middleware registration).

## Scope
- In: this module only — extend the `mcp_servers.server` import and add the refusal plus the middleware call immediately after the application is created.
- Out: `GitHubConfig` (row 3), `config/github_mcp_server.toml` (row 12), the tests (rows 16-31), `scripts/mcp_servers/server.py` (owned by `mcp006`).

## Assumptions
- Rows 3 and 12 are applied first, so `_cfg.auth_token` exists and resolves from `MCP_GITHUB_AUTH_TOKEN` (REQ-001, REQ-002).
- `tests/conftest.py` keeps its non-empty default for `MCP_GITHUB_AUTH_TOKEN`, so importing this module during test collection does not raise (Plan A-5).
- `attach_auth_middleware(app, token)` skips authentication only for an empty token; the refusal below makes that case unreachable here.

## Design decisions
- Enforce the refusal in the server module, not in `GitHubConfig.from_dict`: tests build the model from minimal dictionaries (Plan Design, option b).
- Use the same two statements in all five servers; no shared helper (`scripts/mcp_servers/server.py` belongs to `mcp006`).

## Alternatives considered
- Raise inside `from_dict`: rejected — many existing tests construct the model from `{}` or partial dictionaries.
- A shared `require_token()` helper in `scripts/mcp_servers/server.py`: rejected for this change — that file is owned by `mcp006`.

## Implementation
### Target file
`scripts/mcp_servers/github/github_server.py`

### Procedure
1. Extend the `mcp_servers.server` import (see Details, change A).
2. Insert the refusal and the middleware registration directly after the application is created (see Details, change B).
3. Run the validation commands; the paired authentication tests (row 30) prove the behavior.

### Method
- Anchors: the import block that starts at line 57; the `app = FastAPI(` block at line 82 (closing parenthesis at line 86); the configuration object is `_cfg = GitHubConfig.load()` at line 67. `cast` is already imported from `typing` in this module.
- Order matters: the refusal comes before `attach_auth_middleware(...)` and before any exception handler or route registration. The `app` block is followed by a banner comment (`Domain exception handlers + register routers`); keep one blank line before the new statements and two blank lines after them so the banner stays separated.
- After editing, let `uv run ruff check scripts/mcp_servers/github/github_server.py --fix` (rule `I`) settle the import order; the expected order is `MCPServer`, `ToolArgs`, `_FastAPIApp`, `attach_auth_middleware`, `build_tools_response`, `extract_request_context`.

### Details
Change A — import (Before/After):

```python
# Before:
from mcp_servers.server import (
    MCPServer,
    ToolArgs,
    build_tools_response,
    extract_request_context,
)
# After:
from mcp_servers.server import (
    MCPServer,
    ToolArgs,
    _FastAPIApp,
    attach_auth_middleware,
    build_tools_response,
    extract_request_context,
)
```

Change B — refusal and registration (Before/After):

```python
# Before:
app = FastAPI(
    title="github-mcp",
    version="1.0.0",
    description="MCP server equivalent to @modelcontextprotocol/server-github",
)
# After:
app = FastAPI(
    title="github-mcp",
    version="1.0.0",
    description="MCP server equivalent to @modelcontextprotocol/server-github",
)

if not _cfg.auth_token:
    raise RuntimeError(
        "github-mcp: auth_token is empty; set MCP_GITHUB_AUTH_TOKEN to a non-empty "
        "value (the server does not start without Bearer authentication)"
    )
attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token)
```

The environment variable named in the message is the one the Agent configuration already uses for this server (`config/agent.toml`), so no new variable is introduced.

## Compatibility considerations
- Runtime contract: a request without a matching `Authorization: Bearer` header now returns 401 on every route, `/health` included; the Agent already sends the token on tool calls and in the health poll.
- Production runs a compiled binary: this change takes effect only after `deploy/build_binaries.sh`, and the binary and `config/github_mcp_server.toml` must be deployed together (a new binary with an old configuration has no `auth_token` key, resolves to an empty token, and refuses to start).

## Security considerations
- Fail closed: no empty or absent token can leave this server unauthenticated. The error message names the variable, never a value.
- `/health` gets no exemption (the loopback admission is `mcp006`'s scope).

## Rollback considerations
- Revert this file's two edits (import and the block after `app`); rows 3 and 12 can stay (an unused field and key are harmless).
- If already deployed, restore the previous binary and configuration together.

## Validation plan
- `uv run ruff format scripts/mcp_servers/github/github_server.py` and `uv run ruff check scripts/mcp_servers/github/github_server.py --fix`, then `uv run ruff check scripts/mcp_servers/github/github_server.py`.
- `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports`.
- `uv run bandit scripts/mcp_servers/github/github_server.py` (no new finding).
- `uv run pytest tests/mcp_servers/github/test_github_server_auth.py -q` and `uv run pytest tests/mcp_servers -q -rs` (the measured set returns to 2049 passed and 6 skipped with the test-preparation rows 16-28 applied).

## Completion criteria
- Importing the module with `MCP_GITHUB_AUTH_TOKEN` set to an empty string raises `RuntimeError`; with the variable unset it raises `ValueError`; with a non-empty value it imports.
- A request without the token, or with a wrong token, returns 401 on a tool route and on `/health`; with the right token a tool route returns 200.
- The module calls `attach_auth_middleware` exactly once, right after the application is created.

## Out of scope
- Any change to `scripts/mcp_servers/server.py`, token comparison, or the loopback health admission.
- The git, cicd, rag-pipeline, web-search, and mdq servers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply change A and change B | Pending | — | — | Plan Step 4; after rows 3 and 12 |
| 2 | Confirm the paired tests in row 30 pass | Pending | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-003` (refuse to start on an empty token), `REQ-004` (register the authentication middleware)
- **Source issue**: issues/20261013-113008_mcp007_register-bearer-auth-in-shell-github-file-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-120538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-123717
- **Related target files**: scripts/mcp_servers/github/github_server.py
