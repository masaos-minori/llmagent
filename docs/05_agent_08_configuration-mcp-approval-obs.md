---
title: "Agent Configuration"
category: agent
tags:
  - agent
  - agent
  - configuration
  - config
  - settings
related:
  - 05_agent_00_document-guide.md
---

# Agent Configuration

.*`)

Source: `config/*_mcp_server.toml` (each file's `[mcp_servers.<key>]` section)

| Field | Default | Description |
|---|---|---|
| `mcp_servers` | `{}` | Dict of `McpServerConfig` by server key |
| `mcp_watchdog_interval` | `30.0` (PRODUCTION) / `0.0` (LOCAL) | Watchdog poll interval (seconds; 0=disabled); profile-aware default |
| `mcp_watchdog_max_restarts` | `3` | Max watchdog restart attempts |

The GitHub MCP endpoint is configured only through `mcp_servers.github.url`
(a `McpServerConfig` entry) — the legacy top-level `github_server_url` key
has been removed and is now rejected by `build_agent_config()` with
`ConfigLoadError` if present.

See [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md) for `McpServerConfig` fields.

---

## ApprovalConfig (`cf

g.approval.*`)

Source: `config/agent.toml`

| Field | Default | Description |
|---|---|---|
| `approval_risk_rules` | (see below) | tool → none/medium/high |
| `approval_protected_paths` | `[/opt/, /etc/, /boot/, /usr/, /bin/, /sbin/]` | Escalate to high |
| `approval_high_risk_branches` | `[main, master]` | GitHub branch escalation |
| `approval_shell_safe_prefixes` | `[ls, cat, echo, git log, ...]` | shell_run auto-approve prefixes |
| `approval_resource_keys` | `{path_keys: [...], branch_keys: [...]}` | Arg keys for resource identification |
| `approval_dry_run_tools` | `[write_file, edit_file, delete_file, delete_directory, move_file]` | Pre-execute with dry_run=True |
| `tool_safety_tiers` | `{}` | tool → READ_ONLY/WRITE_SAFE/WRITE_DANGEROUS/ADMIN |

`tool_safety_tiers` keys must be actual registered tool names, not server keys. Unknown keys are detected at startup: a warning in local/development, a fatal `RuntimeError` in production (via `ProductionConfigValidator.validate_unknown_tool_safety_tiers()`).
| `allowed_root` | `""` | File path jail (empty = disabled) |
| `approval_github_allowed_repos` | `[]` | GitHub write allowlist (empty = deny all) |
| `gitops_push_blocked` | `False` | Block all GitHub writes globally |
| `gitops_force_push_blocked` | `True` | Block force push |
| `gitops_protected_branches` | `[main, master]` | Protected branches (high-risk approval) |

**Default `approval_risk_rules`:**
- `none`: (none by default)
- `medium`: write_file, edit_file, create_directory, move_file, github_create_branch, github_create_pull_request, github_update_pull_request, github_create_issue, github_add_issue_comment
- `high`: delete_file, delete_directory, shell_run, github_push_files, github_create_or_update_file, github_delete_file, github_merge_pull_request

---

## ObservabilityConfig

 (`cfg.obs.*`)

Source: `config/agent.toml`

| Field | Default | Description |
|---|---|---|
| `otel_enabled` | `False` | Enable OpenTelemetry |
| `otel_endpoint` | `""` | OTLP HTTP endpoint (`""` = ConsoleSpanExporter) |
| `otel_service_name` | `"llm-agent"` | OTel service name |
| `audit_log_file` | `"/opt/llm/logs/audit.log"` | Audit log path (JSON-lines) |
| `structured_log` | `False` | Use JSON-lines format for `agent.log` |

## Related Documents

- `agent`
- `configuration`
- `config`

## Keywords

agent
configuration
config
settings
