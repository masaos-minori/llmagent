## Goal
- Describe, in the setup chapter, the shared per-server variable on both sides for the shell, github, and file servers and the refusal for an empty or unset value (REQ-007).

## Scope
- In: one new bullet in the Setup Requirements list, after the web-search bullet (line 27).
- Out: anything the `mcp006` change edits in this file (the web-search loopback paragraph).

## Assumptions
- Ordering gate: apply only after the `mcp006` implementation, which edits this file too (Plan A-4, Step 8). At the time of this procedure `scripts/mcp_servers/server.py` still contains `exempt_health_on_loopback`, so `mcp006` is not implemented.
- Re-read the file before editing: `mcp006` may have changed the neighboring lines.

## Design decisions
- Mirror the existing web-search bullet's shape; no configuration values.

## Alternatives considered
N/A: one bullet.

## Implementation
### Target file
`docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`

### Procedure
1. After `mcp006` lands, locate the web-search bullet and add the new bullet right after it.

### Method
- Anchor on the text of the web-search bullet (its first words `web-search uses the single`), not on the line number, because `mcp006` may shift it.

### Details
Add after the web-search bullet (Before/After; the Before line is the anchor):

```markdown
# Before:
  - web-search uses the single `MCP_WEB_SEARCH_AUTH_TOKEN` variable on both sides: the agent's `[mcp_servers.web_search].auth_token` and the server's `auth_token` in `config/web_search_mcp_server.toml` resolve the same value, as for git and cicd; no second secret is needed. (Explicit in code — `config/web_search_mcp_server.toml`, `scripts/mcp_servers/web_search/web_search_server.py`)
# After:
  - web-search uses the single `MCP_WEB_SEARCH_AUTH_TOKEN` variable on both sides: the agent's `[mcp_servers.web_search].auth_token` and the server's `auth_token` in `config/web_search_mcp_server.toml` resolve the same value, as for git and cicd; no second secret is needed. (Explicit in code — `config/web_search_mcp_server.toml`, `scripts/mcp_servers/web_search/web_search_server.py`)
  - The shell, github, and file servers use one variable on both sides as well: `MCP_SHELL_AUTH_TOKEN`, `MCP_GITHUB_AUTH_TOKEN`, `MCP_FILE_READ_AUTH_TOKEN`, `MCP_FILE_WRITE_AUTH_TOKEN`, and `MCP_FILE_DELETE_AUTH_TOKEN` are resolved both by the agent's `[mcp_servers.*].auth_token` entry and by the server's own `auth_token` in `config/<server>_mcp_server.toml`. These servers refuse to start when the value is empty or the variable is unset; deploy the new binaries and the configuration together.
```

## Compatibility considerations
- Documentation only.

## Security considerations
N/A: documentation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`.

Manual deployment verification (REQ-008; Plan Step 10; no file is modified, so it has no procedure document of its own): after Steps 3-9, rebuild the binaries with `deploy/build_binaries.sh`, deploy configuration and scripts together with `deploy/deploy.sh`, start the Agent, then confirm (1) startup, (2) health polling, (3) one tool call per server, and (4) that an unauthenticated request to each of the five servers returns 401. Record any missing `MCP_*_AUTH_TOKEN` variable on the host (Plan UNK-01) and any external caller that sends no token (UNK-03).

## Completion criteria
- The bullet is present after the web-search bullet and consistent with `mcp006`'s edit; the checkers pass.

## Out of scope
- The `mcp006` paragraph and any other chapter.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm `mcp006` is implemented, then add the bullet | Pending | — | — | Plan Step 8; gated on `mcp006` |
| 2 | Run the documentation checkers | Pending | — | — |  |

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
- **Requirement ID**: `REQ-007` (the setup chapter describes the per-server variable on both sides and the refusal)
- **Source issue**: issues/20261013-113008_mcp007_register-bearer-auth-in-shell-github-file-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-120538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-123717
- **Related target files**: docs/22_mcp/mcp_06_14_mcp-authentication-setup.md
