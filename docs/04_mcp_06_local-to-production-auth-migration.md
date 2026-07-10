---
title: "Local to Production Auth Migration"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_configuration_and_operations.md
source:
  - 04_mcp_06_configuration_and_operations.md
---

# Local to Production Auth Migration

## Local to Production Auth Migration

When migrating from local development to production, authentication configuration must change. Follow these steps carefully.

### Migration Steps

1. Switch `security_profile` from `local` to `production` in `config/agent.toml`
   - This enables startup enforcement of auth requirements
   - In `security_profile="local"`, empty `auth_token=""` is allowed; in `security_profile="production"`, it is rejected at startup

2. Set non-empty `auth_token` for all HTTP MCP servers
   - Each `[mcp_servers.*]` entry in `config/agent.toml` that uses `transport="http"` must have a non-empty `auth_token`
   - Use environment variable injection or secret management (e.g., `/etc/conf.d/` files), never hardcode secrets in config files

3. Restart the agent process (do NOT use `/reload`)
   - `/reload` does not modify `[mcp_servers.*]` at runtime — MCP server definition changes require a full agent restart
   - The watchdog (`mcp_watchdog_interval`, `mcp_watchdog_max_restarts`) does not apply pending `/reload` config changes either

4. Verify with `/mcp status`
   - Confirm all servers show `OK` status
   - Check that no servers report authentication-related failures

5. Inspect startup logs for missing/mismatched auth tokens
   - Look for errors mentioning auth failures during startup
   - Check `/opt/llm/logs/agent.log` for transport-level errors on newly authenticated servers

### Troubleshooting

#### Empty `auth_token`

Symptom: Agent fails to start with auth error when `security_profile="production"`.

Cause: At least one HTTP MCP server has `auth_token=""` while `security_profile="production"`.

Fix: Set a valid `auth_token` for each affected server in `config/agent.toml`.

#### Missing env secret

Symptom: Server starts but health checks fail with dependency failure.

Cause: Environment variable referenced by `env` field or config key is not set.

Fix: Ensure the required secret is available in the agent process environment before starting.

#### Mismatched Bearer token

Symptom: Tool calls return authentication errors despite having an `auth_token` set.

Cause: The Bearer token value does not match what the MCP server expects.

Fix: Verify the token value against the MCP server's expected credentials. Tokens are passed as `Authorization: Bearer <token>` headers.

#### `/reload` vs full restart

Symptom: After changing `auth_token` in config, `/reload` reports no effect.

Cause: `/reload` never modifies `[mcp_servers.*]` at runtime. Changes to MCP server definitions (URL, auth token, startup mode, transport, command, environment) always require a full agent restart.

Fix: Stop the agent process and restart it to pick up the new auth configuration.


## Related Documents

- [04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration-file-inventory.md)

## Keywords

configuration
