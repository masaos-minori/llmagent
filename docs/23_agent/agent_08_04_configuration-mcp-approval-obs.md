---
title: "Agent Configuration - MCPConfig, ApprovalConfig, ObservabilityConfig"
area: agent
tags:
  - agent
  - configuration
related:
  - agent_00_document-guide.md
  - agent_08_01_configuration-loading-agent-config.md
  - agent_08_02_configuration-llm-rag.md
  - agent_08_03_configuration-tools-memory.md
  - agent_09_01_data-layer-session-db.md
---

# Agent Configuration

- Operations → [agent_10_01_operations-and-observability-startup-and-health.md](agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

Documents the structure and constraints of MCP, Approval, and Observability configurations.

## Design Intent

### MCP Configuration

#### Separation of Ownership Responsibilities

- `config/agent.toml`: Only for the agent process's MCP lifecycle and transport settings
- `config/*_mcp_server.toml`: Application settings for each MCP server (allowlists/denylists, resource limits, audit paths, secret references)

#### Agent-side MCP Fields

- `startup_mode`: "none" / "persistent" / "subprocess"
- `transport`: TransportType.HTTP ("http")
- `url`: Base URL of the HTTP server
- `cmd`: Command to start a subprocess

#### Component Criticality Classification

`McpServerConfig.required: bool` (default `True`) records each MCP server's
ADR-004 Decision Group 3 required/non-required classification. A server may be
classified non-required only if it satisfies all of Decision Group 3 item 10's
criteria (safe-core-processing unaffected, no security-control bypass, failure
localizable, related tools reliably disablable, Fail-Closed rejection of calls,
disabled-state observability, other required components stay safe, any fallback
defined by an Accepted ADR) — undefined or unassessed criticality must not be
assumed non-required (Decision Group 3 item 12).

| Server (`config/agent.toml` key) | Classification | Rationale |
|---|---|---|
| `shell` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
| `git` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
| `web_search` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
| `file_delete` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
| `file_write` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
| `file_read` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
| `github` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
| `cicd` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
| `rag_pipeline` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |
| `mdq` | required | Not assessed as satisfying Decision Group 3 item 10; status quo default |

No server currently overrides `required` in `config/agent.toml`; a
non-required reclassification requires an explicit owner decision and an update to
this table, per ADR-004 Decision Group 3 item 13.

#### Process Isolation

Each MCP server is an independent process that only reads its own configuration file. → [ADR-002](../10_adr/ADR-002-config-isolation.md)

### Approval Configuration

#### Risk Rules

Per-tool base risk is set by `approval_risk_rules` in `config/agent.toml`; tools without an entry fall back to the risk derived from their `tool_safety_tiers` tier (Explicit in code — scripts/agent/tool_policy.py `_TIER_TO_RISK`). Categories:

- `none`: read-only tools and tools with no rule (tier-derived)
- `medium`: local file mutation tools that do not delete (write, edit, create directory, move), and lower-impact GitHub changes (branch, pull request create/update, issue create, issue comment)
- `high`: deletion tools, `shell_run`, GitHub content/merge changes (file create/update/delete, multi-file push, pull request merge), and git `git_checkout`/`git_pull`/`git_push`

`ProductionConfigValidator` rejects a configuration in which the git tools `git_checkout`/`git_pull`/`git_push` resolve to a risk below high (Explicit in code — scripts/agent/production_config_validator.py `_check_approval_risk_floor()`). The per-tool mapping is in `[approval_risk_rules]` of `config/agent.toml` and the [MCP ownership matrix](../22_mcp/mcp_01_tool_ownership_matrix.md).

#### Escalation

- `approval_protected_paths`: Path prefixes that escalate an operation to high risk (values in `config/agent.toml`)
- `approval_high_risk_branches`: Branch names treated as high-risk (values in `config/agent.toml`)

#### Auto-Approval

- `approval_shell_safe_prefixes`: Auto-approval prefixes for shell_run

#### Safety Tiers

- `tool_safety_tiers`: tool → READ_ONLY/WRITE_SAFE/WRITE_DANGEROUS/ADMIN

**CRITICAL**: The keys in tool_safety_tiers must be actual registered tool names, not server keys. Unknown keys are detected at startup and are fatal (config validation error), independent of any environment (Explicit in code — scripts/agent/production_config_validator.py `ProductionConfigValidator.validate()`, scripts/agent/config_builders.py `_run_production_validation()`).

#### Dry Run

- `approval_dry_run_tools`: Tools executed in advance with dry_run=True

#### GitHub Write Control

- `approval_github_allowed_repos`: Allowlist for GitHub writes (empty = deny all)
- `gitops_push_blocked`: Globally blocks all writes to GitHub

#### File Path Restrictions

- `allowed_root`: File path jail (empty = disabled)

### Observability Configuration

- `otel_enabled`: Enable OpenTelemetry
- `otel_endpoint`: OTLP HTTP endpoint ("" = ConsoleSpanExporter)
- `otel_service_name`: OTel service name
- `audit_log_file`: Audit log path (JSON-lines)
- `structured_log`: Use JSON-lines format in agent.log

### Diagnostics Configuration

- `encryption_key`: Fernet symmetric key for DiagnosticStore.save(encrypt=True) (empty string = encryption disabled)
- `retention_days`: Number of days to retain session_diagnostics rows (0 or less = purge disabled)
- `sensitive_fields`: Set of field names to be additionally redacted by _filter_sensitive_fields() (union with hardcoded defaults)

## Responsibility Boundary

- **Source of Truth**: MCP/Approval/Observability/Diagnostics sections in config/agent.toml
- **Validation**: agent/services/config_validators.py
- **Data Classes**: McpServerConfig / ApprovalConfig / ObservabilityConfig / DiagnosticsConfig in agent/config_dataclasses.py

## Key Constraints

- The keys in tool_safety_tiers must be actual registered tool names — unknown keys are fatal at startup
- `allowed_tools=[]` (empty) means "allow all" at runtime (`check_preflight()` skips the whitelist check); in production `ProductionConfigValidator` records it as a validation error, so startup exits (Explicit in code — `scripts/agent/tool_policy.py`, `scripts/agent/production_config_validator.py`)
- `approval_github_allowed_repos=[]` (empty) means "deny all"
- `/reload reports cfg.diagnostics.* changes under a distinct LIVE category; they take effect immediately on every DiagnosticStore save()/fetch() call without requiring a restart`

## Known Limitations

`/reload reports cfg.diagnostics.* changes under a distinct LIVE category; they take effect immediately on every DiagnosticStore save()/fetch() call without requiring a restart`

## Keywords

- MCPConfig
- ApprovalConfig
- ObservabilityConfig
- DiagnosticsConfig
