---
title: "Local to Production Auth Migration"
area: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# Local to Production Auth Migration

## Migrating from local to production environments

**Note (2026-09-04)**: `security_profile=local` no longer exists — `SecurityProfile`
has a single `PRODUCTION` member (`plans/done/20260903-091417_plan.md`, "localremoval").
Every environment now enforces the authentication requirements below
unconditionally; there is no profile switch to perform. The canonical, current
migration procedure for an existing deployment (bind-address migration together
with MCP authentication token setup) is
[`02_deployment.md`'s "Production-Only Migration Procedure"](02_deployment.md#production-only-migration-procedure) —
follow that document for a step-by-step deployment migration. This document's
Migration Steps below are retained as a historical record of the pre-removal
procedure and as a focused authentication-only reference; its Troubleshooting
section below remains current and applicable to any deployment.

### Migration Steps (historical — see `02_deployment.md` for the current procedure)

1. ~~Switch `security_profile` from `local` to `production` in `config/agent.toml`~~ —
   no longer applicable; mandatory authentication requirement checks now run
   unconditionally at startup for every environment.

2. Set non-empty authentication secrets for all HTTP MCP servers
   - For each `[mcp_servers.*]` entry using `transport="http"` in `config/agent.toml`, a non-empty `auth_token_env` or `auth_token_file` is required.
   - Use environment variable injection or secret management (e.g., files under `conf.d/`) instead of hardcoding secrets in configuration files.

3. Restart the agent process (do NOT use `/reload`)
   - `/reload` does not change `[mcp_servers.*]` at runtime — changes to MCP server definitions require a full agent restart.
   - Automatic restarts of subprocess mode servers (`ensure_ready()` during the next tool dispatch) only use existing startup configurations and do not apply pending `/reload` configuration changes.

4. Verify with `/mcp status`
   - Ensure all servers show an `OK` status.
   - Confirm that no servers are reporting authentication-related failures.

5. Check startup logs for missing or mismatched authentication tokens
   - Verify there are no errors regarding authentication failure during startup.
   - For servers that now require authentication, check transport layer errors in `/opt/llm/logs/agent.log`.

### Troubleshooting

#### `auth_token_env` / `auth_token_file` is empty

**Symptom:** The agent fails to start due to authentication errors.

**Cause:** At least one HTTP MCP server has `auth_token_env=""` or `auth_token_file` unset. The historical local-mode allowance for an empty token was removed unconditionally (`plans/done/20260903-092407_plan.md`), not only gated by a "production" profile.

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


### Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)
- `00_security_01_architecture-and-trust-boundaries.md` — System security architecture / Trust boundaries / Threat modeling / AuthN/AuthZ / Auditing / Local vs Production / Fail-open/Fail-closed / Prompt injection responsibility boundaries

### Keywords

configuration
