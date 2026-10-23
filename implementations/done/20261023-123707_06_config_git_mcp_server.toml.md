## Goal
State in the git server config that an empty or missing `auth_token` prevents startup (`REQ-003`).

## Scope
- Comment-only addition to the `auth_token` comment block (lines 21-24).

## Assumptions
- The shell and file server configs already carry the same sentence; reuse its wording.

## Design decisions
- Append one sentence to the existing comment; do not touch the value.

## Alternatives considered
- N/A: comment-only change.

## Implementation
### Target file
`config/git_mcp_server.toml`

### Procedure
1. Append to the `auth_token` comment: "An empty or missing value makes the server refuse to start." (matching `config/shell_mcp_server.toml`).

### Method
- No key, value or default changes; the `auth_token = "${ENV:MCP_GIT_AUTH_TOKEN}"` line stays as is.

### Details
- Reference only: the `auth_token` comment in `config/shell_mcp_server.toml`.

## Compatibility considerations
- N/A: comment-only.

## Security considerations
- N/A: documentation of an enforced control; no secret values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Load the file through the server's own tests (`uv run pytest tests/mcp_servers`) to confirm it still parses.

## Completion criteria
- The comment states the refusal and the file parses.

## Out of Scope
- Any value or key change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the comment change per Implementation > Procedure | Completed | 20261023-130211 | 20261023-130211 | implemented; tests/mcp_servers 2468 passed; one additional test file discovered and added to the Plan (row 25); full suite run at the end of the batch |
| 2 | Run the validation sequence (`rules/toolchain.md`): server tests confirm the file parses | Completed | 20261023-130211 | 20261023-130211 |  |

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
- **Requirement ID**: `REQ-003` (document the refusal)
- **Source issue**: issues/20261023-114044_mcpstart003_four-mcp-servers-start-without-authentication-when-auth_token-is-empty.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115211_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123707
- **Related target files**: config/git_mcp_server.toml