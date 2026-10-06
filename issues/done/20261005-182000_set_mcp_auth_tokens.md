# Set MCP auth tokens for all MCP servers

## Summary

All HTTP MCP servers have `auth_token=""` (empty string = authentication disabled). This causes a fatal startup error — AgentREPL cannot start until auth tokens are configured.

## Background

Each HTTP MCP server configuration file has an `auth_token` field. When empty, authentication is disabled for that server. Currently all HTTP MCP servers have this disabled. The check only applies to servers with `transport = "http"` and a non-empty `url`.

## Problem

Startup fails with:
```
RuntimeError: auth_token is required on all HTTP MCP servers. Violations: shell: no auth_token configured (auth disabled); git: no auth_token configured (auth disabled); ...
```

This is a fatal error — AgentREPL cannot start until auth tokens are configured for all HTTP MCP servers.

## Reason for Change

Without authentication, any client can call MCP server endpoints. Additionally, this is a startup blocker — AgentREPL cannot start with empty `auth_token` on HTTP MCP servers.

## Implementation Intent

Set valid `auth_token` values for each MCP server. This is a configuration change only — no code modifications required. Each token should be a unique, strong random value.

## Target Files or Areas

- `/opt/llm/config/shell_mcp_server.toml` — auth_token
- `/opt/llm/config/git_mcp_server.toml` — auth_token
- `/opt/llm/config/web_search_mcp_server.toml` — auth_token
- `/opt/llm/config/file_delete_mcp_server.toml` — auth_token
- `/opt/llm/config/file_write_mcp_server.toml` — auth_token
- `/opt/llm/config/file_read_mcp_server.toml` — auth_token
- `/opt/llm/config/github_mcp_server.toml` — auth_token
- `/opt/llm/config/cicd_mcp_server.toml` — auth_token
- `/opt/llm/config/rag_pipeline_mcp_server.toml` — auth_token
- `/opt/llm/config/mdq_mcp_server.toml` — auth_token

## Required Changes

For each MCP server config file, set a valid `auth_token`:
```toml
auth_token = "<valid-token-value>"
```

## Constraints

- Tokens must be strong random values (not hardcoded secrets in version control)
- Consider using a secrets manager or environment variable injection for production
- Do not reuse the same token across servers

## Out of Scope

- Implementing new authentication mechanisms
- Changing the token validation logic
- Modifying the security audit framework

## Dependencies

- N/A: none

## Acceptance Criteria

- [ ] No `auth_token is required on all HTTP MCP servers` RuntimeError during startup
- [ ] MCP server endpoints require authentication
- [ ] Existing authenticated clients continue to work

## Testing Expectations

- Run `bash /opt/llm/start_agent.sh` and verify no auth_token RuntimeError
- Test MCP server calls with and without authentication to confirm enforcement

## Documentation Impact

Update deployment documentation to document required auth_token configuration.

## Unresolved Questions

- What are the valid token values? (must be generated externally, not hardcoded)

## Evidence

- Startup failure: `RuntimeError: auth_token is required on all HTTP MCP servers. Violations: {server_key}: no auth_token configured (auth disabled)`
- Source: `/opt/llm/config/git_mcp_server.toml` (`auth_token = ""` at line 16)
- Source: `/opt/llm/config/cicd_mcp_server.toml` (`auth_token = ""` at line 23)
- Note: `web_search_mcp_server.toml` uses `browser_auth_token` (separate from MCP-level auth)
- Source: `scripts/agent/services/security_audit.py:55-70` (fatal error on empty auth_token for HTTP MCP servers)

## Priority

Medium
