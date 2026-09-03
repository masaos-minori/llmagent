---
title: "Pre-Production Fail-Open Checklist"
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

# Pre-Production Fail-Open Checklist

Before deploying to production, verify the following:

- [ ] `tool_definitions_strict = true` (Default is `false`; explicitly enable in production to treat schema mismatches as fatal errors)
- [ ] `routing_drift_strict = true` (Treat routing drift as a fatal error)
- [ ] `serial_tool_calls = false` (Default; DAG scheduling is always enabled. Setting to `true` switches to legacy sequential/parallel determination mode. Note: The setting field `use_tool_dag` does not exist — see [05_agent_08_03](05_agent_08_03_configuration-tools-memory.md#toolconfig-cfgtool))
- [ ] `allowed_tools` is explicitly configured (Empty = allow all tools; should be whitelisted)
- [ ] All registered tools have an entry in `tool_safety_tiers` (Missing tier → Fatal error in production)
- [ ] No unknown keys in `tool_safety_tiers` (Unknown key → Fatal error in production)
- [ ] shell-mcp: `shell_sandbox_backend = "firejail"` (`"none"` is NOT allowed) and the `firejail` binary is installed
- [ ] cicd-mcp: `workflow_allowlist` is explicitly configured (Empty = fails to start with `RuntimeError`/`CicdAuthorizationError` due to fail-closed behavior)
- [ ] `config/agent.toml` has `security_profile = "production"` (Enables strict checks during startup)
- [ ] Health check thresholds (`startup_timeout_sec`, `McpServerHealthRegistry.failure_threshold`) have been reviewed
- [ ] External process supervision with defined restart policy: REQUIRED for persistent-mode MCP servers (no automatic recovery exists at all — see [04_mcp_06_09_mcp-failure-diagnosis.md](04_mcp_06_09_mcp-failure-diagnosis.md)'s `ensure_ready` section); RECOMMENDED as defense-in-depth for subprocess-mode servers (covers the idle-crash window before the next tool call triggers `ensure_ready()`'s reactive recovery). Example: a systemd unit with `Restart=on-failure` and `RestartSec=<N>` — the requirement is the outcome (an explicit restart policy), not a mandate to use systemd specifically.
- [ ] Audit log path is configured and writable
- [ ] API keys (`github_token`, `auth_token`) are set via environment variables and not hardcoded in configuration files
- [ ] `repo_allowlist` in `cicd_mcp_server.toml` is not empty (Empty = reject all repositories)
- [ ] `allowed_repos` in `github_mcp_server.toml` is not empty (Empty = reject all GitHub write operations)

### Firejail Installation and Configuration

For instructions on installing `firejail` and configuring the sandbox backend, please refer to the "Sandbox Backend (shell-mcp)" section in [04_mcp_05_02_auth-profiles-and-sandboxing.md](04_mcp_05_02_auth-profiles-and-sandboxing.md).

Refer to `04_mcp_05_01_access-control-and-allowlists.md` for the complete table of fail-open/fail-closed policies.

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)
- `00_security_01_architecture-and-trust-boundaries.md` — System security architecture / Trust boundaries / Threat modeling / AuthN/AuthZ / Auditing / Local vs Production / Fail-open/Fail-closed / Prompt injection responsibility boundaries

## Keywords

configuration
