---
title: "Pre-Production Fail-Open Checklist"
area: mcp
tags:
  - mcp
  - configuration
related:
  - mcp_00_document-guide.md
  - mcp_06_01_configuration-file-inventory.md
---

# Pre-Production Fail-Open Checklist

Before deploying to production, verify the following:

- [ ] `tool_definitions_strict = true` (Required in production: `ProductionConfigValidator` rejects an absent or `false` value; schema mismatches are fatal errors)
- [ ] `routing_drift_strict = true` (Treat routing drift as a fatal error)
- [ ] `serial_tool_calls = false` (Default; DAG scheduling is always used. Setting to `true` forces every call into its own serial phase — see [agent_08_03](../23_agent/agent_08_03_configuration-tools-memory.md))
- [ ] `allowed_tools` is not an empty list (Required: `ProductionConfigValidator` rejects `allowed_tools=[]` at startup)
- [ ] All registered tools have an entry in `tool_safety_tiers` (Missing tier → Fatal error in production)
- [ ] No unknown keys in `tool_safety_tiers` (Unknown key → Fatal error in production)
- [ ] shell-mcp: `shell_sandbox_backend = "firejail"` (`"none"` is NOT allowed) and the `firejail` binary is installed
- [ ] cicd-mcp: `workflow_allowlist` is explicitly configured (Empty = the server still starts but logs a warning, and all workflow triggers are rejected with `CicdAuthorizationError` at call time due to fail-closed behavior)
- [ ] `security_profile` is `"production"` (the default and only `SecurityProfile` value; when the key is omitted from `config/agent.toml`, production is used)
- [ ] Health check thresholds (`startup_timeout_sec`, `McpServerHealthRegistry.failure_threshold`) have been reviewed
- [ ] Note: There is no MCP watchdog (automatic health polling or restart loop). Recovery for crashed subprocess-mode MCP servers is limited to retry attempts via `ensure_ready()` during the next tool dispatch or manual restart of the agent process itself. Ensure external process monitoring (e.g., systemd) is set up for liveness monitoring and restarts.
- [ ] Audit log path is configured and writable
- [ ] API keys (`github_token`, `auth_token`) are set via environment variables and not hardcoded in configuration files
- [ ] `repo_allowlist` in `cicd_mcp_server.toml` is not empty (Empty = reject all repositories)
- [ ] `allowed_repos` in `github_mcp_server.toml` is not empty (Empty = reject all GitHub write operations)

### Firejail Installation and Configuration

For instructions on installing `firejail` and configuring the sandbox backend, please refer to the "Sandbox Backend (shell-mcp)" section in [mcp_05_02_auth-profiles-and-sandboxing.md](mcp_05_02_auth-profiles-and-sandboxing.md).

Refer to `mcp_05_01_access-control-and-allowlists.md` for the complete table of fail-open/fail-closed policies.

---


## Keywords

- configuration
