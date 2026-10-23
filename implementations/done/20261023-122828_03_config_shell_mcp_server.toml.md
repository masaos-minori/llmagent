## Goal
Document in the shell server configuration comments that commands receive an allowlisted environment and never secret-shaped variables (`REQ-004`).

## Scope
- Comment-only addition next to `env_allowlist` / `env_denylist` (`config/shell_mcp_server.toml:32-37`).

## Assumptions
- The listed base keys match `build_command_env()` (new) as implemented in the helper row.

## Design decisions
- Place the contract right after the `env_denylist` comment so all environment rules sit together.

## Alternatives considered
- N/A: comment-only change.

## Implementation
### Target file
`config/shell_mcp_server.toml`

### Procedure
1. Add a comment block stating the base keys (`HOME`, `USER`, `LOGNAME`, `SHELL`, `LANG`, `LC_*`, `TMPDIR`, `TMP`, `TEMP`, `PATH`), that `req.env` entries pass the filters above, and that `MCP_*` and `TOKEN`/"SECRET"/`PASSWORD`/"CREDENTIAL"/`API_KEY` variables are always removed.

### Method
- No key, value or default changes; comments only.

### Details
- Keep the existing wording style (`# key: description`).

## Compatibility considerations
- N/A: comment-only.

## Security considerations
- N/A: documentation of an existing control; no secret values written.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Load the file with `ShellConfig.load()` equivalent (`uv run pytest tests/mcp_servers/shell`) to confirm it still parses.

## Completion criteria
- The comment describes the contract and matches the helper; the file still parses.

## Out of Scope
- Any setting change or new config key.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the comment change per Implementation > Procedure | Completed | 20261023-125404 | 20261023-125404 | implemented and validated per plan batch (targeted shell tests, full suite 9713 passed) |
| 2 | Run the validation sequence (`rules/toolchain.md`): shell tests confirm the file still parses | Completed | 20261023-125404 | 20261023-125404 |  |

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
- **Requirement ID**: `REQ-004` (document the environment contract)
- **Source issue**: issues/20261023-114000_mcpstart001_shell-sandbox-commands-inherit-all-mcp-auth-tokens-and-github_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-114629_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-122828
- **Related target files**: config/shell_mcp_server.toml