---
title: "MCP Authentication Setup"
area: mcp
tags:
  - mcp
  - configuration
related:
  - mcp_00_document-guide.md
  - mcp_06_02_configuration-file-inventory.md
  - security_01_architecture-and-trust-boundaries.md
source:
  - mcp_06_02_configuration-file-inventory.md
---

# MCP Authentication Setup

## Setting up MCP authentication

Every environment enforces the authentication requirements below unconditionally at
startup; there is no profile switch. For the step-by-step migration of an existing
deployment (bind-address migration together with MCP authentication token setup),
follow the Production-Only Migration Procedure in the deployment document.

### Setup Requirements

- Set non-empty authentication secrets for all HTTP MCP servers
  - For each `[mcp_servers.*]` entry using `transport="http"` in `config/agent.toml`, a non-empty `auth_token_env` or `auth_token_file` is required.
  - Use environment variable injection or secret management (e.g., files under `conf.d/`) instead of hardcoding secrets in configuration files.

- Restart the agent process (do NOT use `/reload`)
  - `/reload` does not change `[mcp_servers.*]` at runtime — changes to MCP server definitions require a full agent restart.
  - Automatic restarts of subprocess mode servers (`ensure_ready()` during the next tool dispatch) only use existing startup configurations and do not apply pending `/reload` configuration changes.

- Verify with `/mcp status`
  - Ensure all servers show an `OK` status.
  - Confirm that no servers are reporting authentication-related failures.

- Check startup logs for missing or mismatched authentication tokens
  - Verify there are no errors regarding authentication failure during startup.
  - For servers that now require authentication, check transport layer errors in `/opt/llm/logs/agent.log`.

### Troubleshooting

#### `auth_token_env` / `auth_token_file` is empty

**Symptom:** The agent fails to start due to authentication errors.

**Cause:** At least one HTTP MCP server has `auth_token_env=""` or `auth_token_file` unset. An empty token is rejected unconditionally at startup.

**Solution:** Set a valid `auth_token_env` or `auth_token_file` for each relevant server in `config/agent.toml`.

#### Missing secrets via environment variables

**Symptom:** The server starts, but health checks fail due to dependency failures.

**Cause:** The environment variable referenced by the `env` field or configuration key is not set.

**Solution:** Ensure necessary secrets are available in the agent process environment before starting.

#### Bearer token mismatch

**Symptom:** Tool calls return authentication errors even though `auth_token_env` or `auth_token_file` is set.

**Cause:** The value of the Bearer token does not match what the MCP server expects.

**Solution:** Verify that the token matches the credentials expected by the MCP server. Tokens are passed in the `Authorization: Bearer <token>` header.

#### Difference between `/reload` and full restart

**Symptom:** Changes to `auth_token_env` or `auth_token_file` in the config are not reflected after running `/reload`.

**Cause:** `/reload` never modifies `[mcp_servers.*]` at runtime. Changes to MCP server definitions (URLs, authentication tokens, startup modes, transports, commands, environments) always require a full agent restart.

**Solution:** Stop and restart the agent process to apply new authentication settings.


## Keywords

configuration
