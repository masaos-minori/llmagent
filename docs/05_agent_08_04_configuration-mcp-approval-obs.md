---
title: "Agent Configuration - MCPConfig, ApprovalConfig, ObservabilityConfig"
area: agent
tags:
  - agent
  - configuration
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_08_01_configuration-loading-agent-config.md
---

# Agent Configuration

- Operations → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

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

No server currently overrides `required` in `config/agent.toml`; a future
non-required reclassification requires an explicit owner decision and an update to
this table, per ADR-004 Decision Group 3 item 13.

#### Process Isolation

Each MCP server is an independent process that only reads its own configuration file. → [ADR-002](../adr/ADR-002-config-isolation.md)

### Approval Configuration

#### Risk Rules

- `none`: None by default
- `medium`: write_file, edit_file, create_directory, move_file, github_* operations
- `high`: delete_file, delete_directory, shell_run, github_push_files, github_merge_pull_request

#### Escalation

- `approval_protected_paths`: Escalate to high (/opt/, /etc/, /boot/, /usr/, /bin/, /sbin/)
- `approval_high_risk_branches`: main, master

#### Auto-Approval

- `approval_shell_safe_prefixes`: Auto-approval prefixes for shell_run

#### Safety Tiers

- `tool_safety_tiers`: tool → READ_ONLY/WRITE_SAFE/WRITE_DANGEROUS/ADMIN

**CRITICAL**: The keys in tool_safety_tiers must be actual registered tool names, not server keys. Unknown keys are detected at startup: warning in local/dev environments, fatal RuntimeError in production.

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

- The keys in tool_safety_tiers must be actual registered tool names — unknown keys are fatal in production
- `allowed_tools=[]` (empty) means "allow all"
- `approval_github_allowed_repos=[]` (empty) means "deny all"
- `/reload reports cfg.diagnostics.* changes under a distinct LIVE category; they take effect immediately on every DiagnosticStore save()/fetch() call without requiring a restart`

## Operational Notes

Unknown

## Known Limitations

`/reload reports cfg.diagnostics.* changes under a distinct LIVE category; they take effect immediately on every DiagnosticStore save()/fetch() call without requiring a restart`

## Related Docs

- [05_agent_00_document-guide.md](05_agent_00_document-guide.md)
- [05_agent_08_01_configuration-loading-agent-config.md](05_agent_08_01_configuration-loading-agent-config.md)
- [05_agent_08_02_configuration-llm-rag.md](05_agent_08_02_configuration-llm-rag.md)
- [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)
- [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)
- System security architecture / Trust boundaries / Threat modeling / AuthN/AuthZ / Auditing / Local vs Production / Fail-open/Fail-closed / Prompt injection responsibility boundaries
- High-risk MCP tool common policy (path/repo allowlists, traversal prevention, approval-risk tier mapping)

### Keywords

MCPConfig
ApprovalConfig
ObservabilityConfig
DiagnosticsConfig
