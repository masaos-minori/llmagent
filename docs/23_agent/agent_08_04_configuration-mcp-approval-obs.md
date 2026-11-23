---
title: "Agent Configuration - MCPConfig, ApprovalConfig, ObservabilityConfig"
area: agent
class: Reference
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

`role` is a display-only label: it is surfaced by the MCP status command and status service, and is never consulted by tool routing or approval (`scripts/shared/mcp_config.py` — confirmed display-only; field semantics are canonical in [mcp_06_02](../22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md)).

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

<!-- AUTO-GENERATED: generate_reference_table.py component-mandatoriness-reference -->
Generated from `registry/component_mandatoriness.yaml`. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type mandatoriness` to refresh.

| Server (`config/agent.toml` key) | Classification | Rationale |
|---|---|---|
| `cicd` | required | Classified required by repository owner instruction 2026-11-10 (ADR-004 Group 7 applicability note, option B); item 10 criteria apply only to a non-mandatory classification |
| `file_delete` | required | Classified required by repository owner instruction 2026-11-10 (ADR-004 Group 7 applicability note, option B); item 10 criteria apply only to a non-mandatory classification |
| `file_read` | required | Classified required by repository owner instruction 2026-11-10 (ADR-004 Group 7 applicability note, option B); item 10 criteria apply only to a non-mandatory classification |
| `file_write` | required | Classified required by repository owner instruction 2026-11-10 (ADR-004 Group 7 applicability note, option B); item 10 criteria apply only to a non-mandatory classification |
| `git` | required | Classified required by repository owner instruction 2026-11-10 (ADR-004 Group 7 applicability note, option B); item 10 criteria apply only to a non-mandatory classification |
| `github` | required | Classified required by repository owner instruction 2026-11-10 (ADR-004 Group 7 applicability note, option B); item 10 criteria apply only to a non-mandatory classification |
| `mdq` | required | Classified required by repository owner instruction 2026-11-10 (ADR-004 Group 7 applicability note, option B); item 10 criteria apply only to a non-mandatory classification |
| `rag_pipeline` | required | Classified required by repository owner instruction 2026-11-10 (ADR-004 Group 7 applicability note, option B); item 10 criteria apply only to a non-mandatory classification |
| `shell` | required | Classified required by repository owner instruction 2026-11-10 (ADR-004 Group 7 applicability note, option B); item 10 criteria apply only to a non-mandatory classification |
| `web_search` | required | Classified required by repository owner instruction 2026-11-10 (ADR-004 Group 7 applicability note, option B); item 10 criteria apply only to a non-mandatory classification |
<!-- END AUTO-GENERATED -->

Subprocess servers must stay required (ADR-004 Exceptions; `McpServerConfig` rejects `required = false` with `startup_mode = "subprocess"`). A non-required reclassification requires an explicit owner decision and an update to this table, per ADR-004 Decision Group 3 item 13. No server is classified non-required in `registry/component_mandatoriness.yaml` as of 2026-11-10, so ADR-004 Decision Group 7 and INV-09 currently describe behavior no configuration triggers and are declared inapplicable until the first non-required classification (the removal trigger; see the ADR-004 Group 7 applicability note).

#### Process Isolation

Each MCP server is an independent process that only reads its own configuration file. → [ADR-002](../10_adr/adr_02_01_002_platform-config-isolation.md)

### Approval Configuration

#### Risk Rules

Per-tool base risk comes from the tool's declared `agent_safety_tier` mapped through `_TIER_TO_RISK` (Explicit in code — scripts/agent/tool_policy.py). The removed per-tool config maps (`approval_risk_rules`, `tool_safety_tiers`) no longer exist; naming one in `config/agent.toml` is rejected as an unknown key. Categories under the shipped declared tiers:

- `none`: tools whose declared tier maps to none (`READ_ONLY` and `WRITE_SAFE` tiers) — the local file write/edit/create-directory/move tools, `git_add`, `git_commit`, and the lower-impact GitHub changes (branch create, pull request create/update, issue create, issue comment). A tier-derived `none` is never raised by escalation.
- `medium`: tools declaring `WRITE_DANGEROUS` — the local file and directory deletion tools, the git write tools (`git_checkout`/`git_pull`/`git_push`), and the GitHub content/merge changes (file create/update/delete, multi-file push, pull request merge). A protected path or high-risk branch escalates them to `high` (see `mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`).
- `high`: tools declaring `ADMIN` (for example `shell_run`), and any tool absent from the registry (fail-safe). `shell_run` matching the read-only safe-shape rule resolves to `none` via the special override instead.

`ProductionConfigValidator` rejects a configuration where the git write tools `git_checkout`/`git_pull`/`git_push` declare a tier whose mapped risk is `none` (Explicit in code — scripts/agent/production_config_validator.py `_check_approval_risk_floor()`); the escalation from `medium` to `high` via `approval_protected_paths` remains a runtime decision.

The evaluation order itself is canonical in [agent_06_02](agent_06_02_tool-execution-and-approval-approval.md).

#### Escalation, Auto-Approval and Dry Run

- `approval_protected_paths` and `approval_high_risk_branches` escalate an operation to high risk (values: `config/agent.toml`).
- Protected-path escalation only ever sees paths inside `allowed_root`: a path outside the jail is denied at the pre-check stage before risk classification runs (see the Protected-path scope note in [agent_06_02](agent_06_02_tool-execution-and-approval-approval.md)). The list does not discriminate between paths inside the jail.
- `approval_shell_safe_prefixes` defines auto-approval prefixes for `shell_run`.
- Tools declaring `preview_capability="dry_run"` are executed in advance with `dry_run=True` (Explicit in code — `agent/tool_approval.py`).

#### Safety Tiers

The safety tier (`READ_ONLY` / `WRITE_SAFE` / `WRITE_DANGEROUS` / `ADMIN`) is no longer a config map: each tool's producer declares it as `agent_safety_tier` in its tool definition, and the value set is closed and enforced at registration (Explicit in code — `scripts/shared/tool_metadata.py`). The removed `tool_safety_tiers` key in `config/agent.toml` is rejected as an unknown key by the production config validator, independent of any environment (Explicit in code — `scripts/agent/production_config_validator.py`).

#### GitHub Write Control and File Path Restrictions

- `approval_github_allowed_repos`: allowlist for GitHub writes; empty = deny all.
- `gitops_push_blocked`: globally blocks all writes to GitHub.
- `approval_medium_preview_fallback`: boolean, default `true`. When a MEDIUM-risk dry-run preview fails, `true` shows the static preview and still prompts; `false` denies the call. HIGH risk ignores it and always denies on a failed preview.
- `allowed_root`: file path jail; required key, an empty value fails config load, and the path jail is never skipped.

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

- A config naming a removed per-tool map (`tool_safety_tiers`, `approval_risk_rules`, `approval_resource_keys`, `approval_dry_run_tools`) is rejected at load as an unknown key (see Risk Rules and Safety Tiers).
- `allowed_tools=[]` is valid and does not deny (base visibility applies) under `discovered`; under `explicit_allowlist` it denies every tool at runtime, including after a config reload. It is no longer recorded as a production-validator error at load (Explicit in code — `scripts/shared/runtime_tool_registry.py` `apply_policy`).
- `approval_github_allowed_repos=[]` means "deny all".
- `cfg.diagnostics.*` changes are reported by `/reload` under the `[LIVE]` category and take effect on the next `DiagnosticStore` save()/fetch() without a restart.

## Known Limitations

Not applicable.

## Keywords

- MCPConfig
- ApprovalConfig
- ObservabilityConfig
- DiagnosticsConfig
