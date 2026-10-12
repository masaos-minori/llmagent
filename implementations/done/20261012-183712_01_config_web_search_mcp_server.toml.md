## Goal
- Replace the separate browser token setting with the shared auth_token reference, as the git and cicd server configurations do (`REQ-001, REQ-002`)

## Scope
- The browser-token comment and setting in `config/web_search_mcp_server.toml`; no other setting changes.

## Assumptions
- The agent's web-search entry resolves the same environment variable, so both sides share one secret.
- The new key is read by procedure 02; until that change the server ignores it.

## Design decisions
- Copy the comment style of `config/git_mcp_server.toml`: what the key is, the environment variable it resolves from, and that it must match the agent entry.
- Do not mention the removed key in a comment; the plan requires that no reference to it remains outside the loader's error path.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`config/web_search_mcp_server.toml`

### Procedure
1. Replace the comment block and the setting that precede the end of the browser settings with a comment saying the key is the Bearer token for MCP server call authentication, resolved from the web-search authentication environment variable, and that it must match the agent configuration's web-search auth_token value.
2. Add the setting auth_token as an environment reference to the environment variable MCP_WEB_SEARCH_AUTH_TOKEN in the same place.

### Method
- Keep the file's other settings, order, and blank-line style unchanged.

### Details
- The environment reference resolves at load time and raises if the variable is unset, as for the other servers.

## Compatibility considerations
A deployment must receive this file and procedure 02's code together; see the Plan risks. An old configuration with the removed key is rejected by the new loader.

## Security considerations
The file holds a reference to an environment variable, never a literal secret.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_models.py -q` after procedures 02 and 05.
- `uv run python tools/check_docs_consistency.py --domain mcp` is unaffected; this file is checked through the config-loading tests.
- Execution order for the whole plan: tests first (procedures 05, 06, 07, 08, 09, 04), then the code (01, 02, 03), then the documentation (10 to 15); the new tests must be seen failing before the code is edited.

## Completion criteria
- The file contains the auth_token setting and no browser token, and the model tests pass.

## Out of scope
- The model change (procedure 02) and every other server's configuration.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the browser token setting with the shared auth_token setting | Completed | 20261012-184531 | 20261012-184531 | stale_detector clean; changed: config/web_search_mcp_server.toml (auth_token referencing MCP_WEB_SEARCH_AUTH_TOKEN replaces the browser token) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-184531 | 20261012-184531 | model and server tests pass |

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
- **Requirement ID**: `REQ-001, REQ-002`
- **Source issue**: issues/done/20261012-182600_mcp005_web-search-tool-calls-return-401-when-browser_auth_token-differs-from-auth_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-183348_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183712
- **Related target files**: config/web_search_mcp_server.toml