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
  - agent_10_01_operations-and-observability-startup-and-health.md
  - adr_02_01_002_platform-config-isolation.md
  - mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - mcp_01_tool_ownership_matrix.md
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

Each `[mcp_servers.*]` entry carries only transport and lifecycle settings: `startup_mode` (`none` / `persistent` / `subprocess`), the HTTP `transport` and base `url`, and the subprocess `cmd`.

#### Component Criticality Classification

`McpServerConfig.required: bool` (default `True`) records each MCP server's
ADR-004 Decision Group 3 required/non-required classification. A server may be
classified non-required only if it satisfies all of Decision Group 3 item 10's
criteria (safe-core-processing unaffected, no security-control bypass, failure
localizable, related tools reliably disablable, Fail-Closed rejection of calls,
disabled-state observability, other required components stay safe, any fallback
defined by an Accepted ADR) — undefined or unassessed criticality must not be
assumed non-required (Decision Group 3 item 12).

Approved classification of each MCP server (ADR-004 Decision Group 3 item 13); the `required` value in `config/agent.toml` must match it.

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

Subprocess servers must stay required (ADR-004 Exceptions; `McpServerConfig` rejects `required = false` with `startup_mode = "subprocess"`). A non-required reclassification requires an explicit owner decision and an update to this table, per ADR-004 Decision Group 3 item 13.

#### Process Isolation

Each MCP server is an independent process that only reads its own configuration file. → [ADR-002](../10_adr/adr_02_01_002_platform-config-isolation.md)

### Approval Configuration

#### Risk Rules

Per-tool base risk is set by `approval_risk_rules` in `config/agent.toml`; tools without an entry fall back to the risk derived from their `tool_safety_tiers` tier (Explicit in code — scripts/agent/tool_policy.py `_TIER_TO_RISK`). Categories:

- `none`: tools whose tier-derived level is none (`READ_ONLY` and `WRITE_SAFE` tiers) and that no rule raises. A tool with no rule takes its tier-derived level, which is not always `none`: for example `rag_delete_document` is `WRITE_DANGEROUS` and therefore `medium`, not `high`, unless a rule sets otherwise (see `mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`)
- `medium`: local file mutation tools that do not delete (write, edit, create directory, move), and lower-impact GitHub changes (branch, pull request create/update, issue create, issue comment)
- `high`: local file and directory deletion tools, `shell_run`, GitHub content/merge changes (file create/update/delete, multi-file push, pull request merge), and git `git_checkout`/`git_pull`/`git_push`

`ProductionConfigValidator` rejects a configuration in which the git tools `git_checkout`/`git_pull`/`git_push` resolve to a risk below high (Explicit in code — scripts/agent/production_config_validator.py `_check_approval_risk_floor()`). The per-tool mapping is in `[approval_risk_rules]` of `config/agent.toml` and the [MCP ownership matrix](../22_mcp/mcp_01_tool_ownership_matrix.md).

#### Escalation, Auto-Approval and Dry Run

- `approval_protected_paths` and `approval_high_risk_branches` escalate an operation to high risk (values: `config/agent.toml`).
- `approval_shell_safe_prefixes` defines auto-approval prefixes for `shell_run`.
- `approval_dry_run_tools` lists tools executed in advance with `dry_run=True`.

#### Safety Tiers

`tool_safety_tiers` maps tool to `READ_ONLY` / `WRITE_SAFE` / `WRITE_DANGEROUS` / `ADMIN`.

**CRITICAL**: The keys must be actual registered tool names, not server keys. Unknown keys are fatal at startup (config validation error), independent of any environment (Explicit in code — `scripts/agent/production_config_validator.py`).

#### GitHub Write Control and File Path Restrictions

- `approval_github_allowed_repos`: allowlist for GitHub writes; empty = deny all.
- `gitops_push_blocked`: globally blocks all writes to GitHub.
- `allowed_root`: file path jail; empty = disabled.

### Observability Configuration

OpenTelemetry, the audit log path (JSON-lines) and structured logging are configured in `config/agent.toml`. An empty `otel_endpoint` selects the console span exporter.

### Diagnostics Configuration

- `encryption_key`: Fernet symmetric key for DiagnosticStore.save(encrypt=True) (empty string = encryption disabled). Changing the key makes rows encrypted with the previous key unreadable; `fetch()` returns them as ciphertext with a warning (see agent_09_01).
- `retention_days`: retention of `session_diagnostics` rows; 0 or less disables the purge.
- `sensitive_fields`: field names redacted in addition to the hardcoded defaults (union).

## Responsibility Boundary

- **Source of Truth**: MCP/Approval/Observability/Diagnostics sections in config/agent.toml
- **Validation**: agent/services/config_validators.py
- **Schema**: McpServerConfig / ApprovalConfig / ObservabilityConfig / DiagnosticsConfig in agent/config_dataclasses.py

## Key Constraints

- Unknown `tool_safety_tiers` keys are fatal at startup (see Safety Tiers).
- `allowed_tools=[]` means "allow all" at runtime (`check_preflight()` skips the whitelist check); in production `ProductionConfigValidator` records it as a validation error, so startup exits (Explicit in code — `scripts/agent/production_config_validator.py`).
- `approval_github_allowed_repos=[]` means "deny all".
- `cfg.diagnostics.*` changes are reported by `/reload` under the `[LIVE]` category and take effect on the next `DiagnosticStore` save()/fetch() without a restart.

## Known Limitations

Not applicable.

## Keywords

- MCPConfig
- ApprovalConfig
- ObservabilityConfig
- DiagnosticsConfig
