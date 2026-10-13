---
title: "MCP Authentication Setup"
area: mcp
tags:
  - mcp
  - configuration
related:
  - mcp_00_document-guide.md
  - mcp_06_01_configuration-file-inventory.md
  - security_01_architecture-and-trust-boundaries.md
  - mcp_05_05_mdq-enforcement-and-lockdown.md
---

# MCP Authentication Setup

## Setting up MCP authentication

Every environment enforces the authentication requirements below at
startup; there is no profile switch. For the production token setup, see section 2.5 (MCP Authentication Tokens) of
the deployment document.

### Setup Requirements

- Set non-empty authentication secrets for all HTTP MCP servers
  - For each enabled `[mcp_servers.*]` entry (`startup_mode` other than `none`) in `config/agent.toml`, a non-empty `auth_token` is required, normally an `"${ENV:MCP_<SERVER_KEY>_AUTH_TOKEN}"` reference.
  - Use environment variable injection or secret management (e.g., files under `conf.d/`) instead of hardcoding secrets in configuration files.
  - mdq-mcp does not verify Bearer tokens at the HTTP layer (see `mcp_05_05_mdq-enforcement-and-lockdown.md`), but its agent-side `auth_token` must still be non-empty.
  - web-search uses the single `MCP_WEB_SEARCH_AUTH_TOKEN` variable on both sides: the agent's `[mcp_servers.web_search].auth_token` and the server's `auth_token` in `config/web_search_mcp_server.toml` resolve the same value, as for git and cicd; no second secret is needed. (Explicit in code — `config/web_search_mcp_server.toml`, `scripts/mcp_servers/web_search/web_search_server.py`)

- Restart the agent process (do NOT use `/reload`)
  - `/reload` does not change `[mcp_servers.*]` at runtime — changes to MCP server definitions require a full agent restart.
  - Automatic restarts of subprocess mode servers (`ensure_ready()` during the next tool dispatch) only use existing startup configurations and do not apply pending `/reload` configuration changes.

- Verify with `/mcp status`
  - Ensure all servers show an `OK` status.
  - Confirm that no servers are reporting authentication-related failures.

- Check startup logs for missing or mismatched authentication tokens
  - Verify there are no errors regarding authentication failure during startup.
  - For servers that now require authentication, check transport layer errors in `<log_dir>/agent.log`.

### Troubleshooting

#### `auth_token` is empty

**Symptom:** The agent fails to start due to authentication errors.

**Cause:** At least one HTTP MCP server has an empty `auth_token` (for example, the referenced environment variable is unset). An empty token on an enabled server is rejected at startup.

**Solution:** Set a valid `auth_token` for each relevant server in `config/agent.toml`.

#### Missing secrets via environment variables

**Symptom:** The server starts, but health checks fail due to dependency failures.

**Cause:** The environment variable referenced by `auth_token` (`${ENV:...}`) is not set.

**Solution:** Ensure necessary secrets are available in the agent process environment before starting.

#### Bearer token mismatch

**Symptom:** Tool calls return authentication errors even though `auth_token` is set.

**Cause:** The value of the Bearer token does not match what the MCP server expects.

**Solution:** Verify that the token matches the credentials expected by the MCP server. Tokens are passed in the `Authorization: Bearer <token>` header.

#### web-search answers 401 on every request

**Symptom:** The web-search server is running, but tool calls and health probes are rejected with `401`.

**Cause:** The agent and the server resolved different values for the web-search token, for example a server configuration left from before web-search shared `MCP_WEB_SEARCH_AUTH_TOKEN` with the agent. A configuration that still contains the removed `browser_auth_token` key is rejected when the server loads it. (Explicit in code — `scripts/mcp_servers/web_search/web_search_models.py`)

**Solution:** Set the one `MCP_WEB_SEARCH_AUTH_TOKEN` variable, deploy the configuration and the scripts together, and restart the agent. The server's `/health` endpoint is additionally admitted from a loopback client without a token.

#### Difference between `/reload` and full restart

**Symptom:** Changes to `auth_token` in the config are not reflected after running `/reload`.

**Cause:** `/reload` never modifies `[mcp_servers.*]` at runtime. Changes to MCP server definitions (URLs, authentication tokens, startup modes, transports, commands, environments) always require a full agent restart.

**Solution:** Stop and restart the agent process to apply new authentication settings.


## Keywords

- configuration
