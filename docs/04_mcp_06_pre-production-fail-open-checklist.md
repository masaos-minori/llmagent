---
title: "Pre-Production Fail-Open Checklist"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_configuration-file-inventory.md
source:
  - 04_mcp_06_configuration-file-inventory.md
---

# Pre-Production Fail-Open Checklist

## Pre-Production Fail-Open Checklist

Before deploying to production, verify:

- [ ] `tool_definitions_strict = true` (fatal on schema mismatch)
- [ ] `routing_drift_strict = true` (fatal on routing drift)
- [ ] `plugin_strict = true` (fail-fast on plugin errors)
- [ ] `use_tool_dag = true` (DAG scheduling; `false` is legacy non-production behavior)
- [ ] `allowed_tools` explicitly set (empty = allow all tools; should be a whitelist)
- [ ] All registered tools have entries in `tool_safety_tiers` (missing tiers → fatal in production)
- [ ] No unknown keys in `tool_safety_tiers` (unknown keys → fatal in production)
- [ ] shell-mcp: `shell_sandbox_backend = "firejail"` (not `"none"`) and firejail binary installed
- [ ] `cicd-mcp`: `workflow_allowlist` explicitly set (empty = fail-closed: deny all)
- [ ] `security_profile = "production"` in `config/agent.toml` (enables startup enforcement)
- [ ] `mcp_watchdog_interval = 30.0` (auto-restart enabled)
- [ ] Health check thresholds reviewed (`startup_timeout_sec`, `mcp_watchdog_max_restarts`)
- [ ] Audit log paths configured and writable
- [ ] API keys (`github_token`, `auth_token`) set via environment variables, not hardcoded in config
- [ ] `repo_allowlist` non-empty in `cicd_mcp_server.toml` (empty = deny all repos)
- [ ] `allowed_repos` non-empty in `github_mcp_server.toml` (empty = deny all GitHub write ops)

### Installing firejail

```bash
# Debian/Ubuntu
sudo apt-get install firejail

# Alpine
apk add firejail

# Verify installation
firejail --version
```

After installation, update `config/shell_mcp_server.toml`:

```toml
shell_sandbox_backend = "firejail"
```

See `04_mcp_05_security_and_safety_model.md` for the full fail-open/closed policy table.

---


## Related Documents

- [04_mcp_06_configuration-file-inventory.md](04_mcp_06_configuration-file-inventory.md)

## Keywords

configuration
