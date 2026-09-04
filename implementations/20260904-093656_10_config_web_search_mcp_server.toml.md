## Goal
Migrate `browser_auth_token` from an empty literal to an environment-variable
reference.

## Scope
- **In-Scope**: `browser_auth_token = ""` (verified 2026-09-04, line 26) and
  its preceding comment (lines 24-25).
- **Out-of-Scope**: `default_max_results`, `max_results_limit`,
  `search_timeout_sec`, `browser_allowed_domains`, `browser_max_response_kb`,
  `browser_timeout_sec` — confirmed by direct read to be unrelated to
  authentication; this file has no separate top-level `auth_token` field
  (confirmed via `grep -n "auth_token" config/web_search_mcp_server.toml`,
  which returns only `browser_auth_token` matches).

## Assumptions
- `browser_auth_token` is a distinct credential from
  `config/agent.toml`'s `[mcp_servers.web_search].auth_token` — per the
  file's own comment, it controls a separate "auth middleware" specific to
  the `browser_fetch` tool, not the MCP server's own Bearer-token check
  (that is `[mcp_servers.web_search].auth_token`, migrated as part of row
  7). This row's environment variable must therefore be named distinctly
  from `MCP_WEB_SEARCH_AUTH_TOKEN` (row 7's variable for the same-named
  server), to avoid the two unrelated secrets colliding under one name.
- `web_search_models.py:132`'s `get_str(d, "browser_auth_token", "")` call
  (confirmed by direct read) transparently resolves `${ENV:...}` once row
  2's `get_str()` change lands — no code change needed in
  `web_search_models.py` itself.

## Design decisions
- Use `${ENV:MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN}` — distinct from row 7's
  `MCP_WEB_SEARCH_AUTH_TOKEN`, reflecting that this is a different secret
  for a different auth middleware within the same server.

## Alternatives considered
- Reusing `MCP_WEB_SEARCH_AUTH_TOKEN` (row 7's variable) for this field
  too: rejected — per Assumptions, `browser_auth_token` and
  `[mcp_servers.web_search].auth_token` are confirmed-distinct credentials
  for distinct middleware; sharing one environment variable across two
  unrelated secrets would prevent independent rotation and misrepresent
  them as the same credential.

## Implementation
### Target file
`config/web_search_mcp_server.toml`

### Procedure
Replace `browser_auth_token = ""` (line 26) with
`browser_auth_token = "${ENV:MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN}"`.

### Method
Direct `Edit`.

### Details
Current (verified 2026-09-04, lines 24-26):
```toml
# browser_auth_token: Bearer token for browser_fetch's auth middleware; empty string = auth
# disabled.
browser_auth_token = ""
```
After:
```toml
# browser_auth_token: Bearer token for browser_fetch's auth middleware,
# resolved from the MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN environment variable.
# Distinct from config/agent.toml's [mcp_servers.web_search].auth_token —
# see that file for the MCP server's own Bearer-token credential.
browser_auth_token = "${ENV:MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN}"
```

## Compatibility considerations
This is the live deployed configuration for the web_search MCP server
subprocess — a deploy step (Plan Implementation steps Phase 3) is mandatory
after this edit. Unlike rows 8/9, this row's environment variable is
independent of row 7's `agent.toml` change (no shared-value requirement),
since it protects a distinct middleware.

## Security considerations
This row's edit is part of REQ-002/AC-5's environment-variable-based secret
loading for the web_search MCP server's `browser_fetch` auth middleware.

## Rollback considerations
Single-line config edit under version control; revert via `git revert` if
needed.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `config/web_search_mcp_server.toml` | Deployment | `skills/deploy/workflow.md`'s deploy sequence, with `MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN` set beforehand | `browser_fetch`'s auth middleware validates incoming requests against the resolved value |

## Completion criteria
`browser_auth_token` references `${ENV:MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN}`;
no literal empty-string value remains.

## Out of scope
`default_max_results`, `max_results_limit`, `search_timeout_sec`,
`browser_allowed_domains`, `browser_max_response_kb`, `browser_timeout_sec`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | `browser_auth_token = "${ENV:MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN}"` — a distinct env var and field from row 7's `agent.toml` `[mcp_servers.web_search].auth_token`, confirmed not conflated |
| 2 | Add or update tests per Validation plan | N/A | — | — | Configuration file, no dedicated test — validated via deploy step |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | `tomllib` parse-valid; deployed via `bash deploy/deploy.sh` (see row 7's Notes). Adversarial verification found this change (an eagerly-loaded module-level `WebSearchConfig.load()` at import time) broke test collection/execution across `tests/mcp_servers/web_search/*` and `tests/mcp_servers/test_mcp_server_base.py::TestAppModuleImportability` when the referenced env var was unset — fixed via `tests/conftest.py` defaulting `MCP_GIT_AUTH_TOKEN`/`MCP_CICD_AUTH_TOKEN`/`MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN` to `""` (empty, not a real token) so collection succeeds while preserving each server's pre-existing empty-token accept-all test behavior |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260904 | 20260904 | Covered by row 7's `docs/02_deployment.md` update (single combined edit covering rows 7-10's env var naming) |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260902-143335_mcpauth_preserve_mandatory_mcp_authentication_under_loopback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-092407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-093656
- **Related target files**: config/web_search_mcp_server.toml
