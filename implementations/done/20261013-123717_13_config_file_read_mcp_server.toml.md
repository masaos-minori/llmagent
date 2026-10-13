## Goal
- Add the server-side `auth_token` entry to `config/file_read_mcp_server.toml`, resolved from `MCP_FILE_READ_AUTH_TOKEN`, the variable `config/agent.toml` already uses for this server (REQ-002).

## Scope
- In: one comment block and one key, placed at the end of the file, after `max_search_results`.
- Out: the model (row 5), the server module (row 6), tests.

## Assumptions
- the `[mcp_servers.file_read]` entry of `config/agent.toml` defines `auth_token` as `${ENV:MCP_FILE_READ_AUTH_TOKEN}`; the variable name must be identical (Plan A-2).
- The file currently has no `auth_token` key.

## Design decisions
- Reuse the wording of `config/git_mcp_server.toml` (comment plus `auth_token = "${ENV:...}"`), adapted to name the fail-closed behavior.

## Alternatives considered
N/A: the entry shape is fixed by the git and cicd precedent.

## Implementation
### Target file
`config/file_read_mcp_server.toml`

### Procedure
1. Append the block below at the end of the file, after `max_search_results`.
2. Compare the variable name with the `[mcp_servers.file_read]` entry of `config/agent.toml`.

### Method
- Keep one blank line before the comment block; the file keeps ending with a newline.

### Details
Anchor (the text the block follows):

```toml
# Before:
# max_search_results: maximum number of results returned by search_files
max_search_results = 200
# After:
# max_search_results: maximum number of results returned by search_files
max_search_results = 200

# auth_token: Bearer token for MCP server call authentication, resolved from the
# MCP_FILE_READ_AUTH_TOKEN environment variable. Must match config/agent.toml's
# [mcp_servers.file_read].auth_token value. An empty or missing value makes the
# server refuse to start (fail closed).
auth_token = "${ENV:MCP_FILE_READ_AUTH_TOKEN}"
```

## Compatibility considerations
- An old binary ignores the new key (no unknown-key rejection in `ConfigLoader`); a new binary requires it. Deploy configuration and binaries together (Plan Design, Deployment).

## Security considerations
- The file holds a `${ENV:...}` reference only; never write a token value here.

## Rollback considerations
- Remove the added block.

## Validation plan
- `uv run python -c "import tomllib,sys;print(tomllib.load(open('config/file_read_mcp_server.toml','rb'))['auth_token'])"` prints the reference.
- `uv run pytest tests/mcp_servers/file/test_file_server_auth.py -q` (model/TOML tests, row 31) and `uv run pytest tests/mcp_servers -q`.

## Completion criteria
- `config/file_read_mcp_server.toml` defines `auth_token = "${ENV:MCP_FILE_READ_AUTH_TOKEN}"` and the name equals the one in `config/agent.toml`.

## Out of scope
- Any other key, the deployment scripts, and `config/agent.toml`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `auth_token` block | Pending | — | — | Plan Step 5 |
| 2 | Confirm the TOML test in the paired new test file passes | Pending | — | — | row 31 |

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
- **Requirement ID**: `REQ-002` (server-side `auth_token` entry using the Agent's variable name)
- **Source issue**: issues/20261013-113008_mcp007_register-bearer-auth-in-shell-github-file-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-120538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-123717
- **Related target files**: config/file_read_mcp_server.toml
