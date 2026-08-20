---
title: "System Security Architecture and Trust Boundaries"
category: security
tags:
  - security
  - architecture
  - trust-boundaries
  - threat-model
  - auth
  - audit
related:
  - 00_security_02_high-risk-tool-common-policy.md
  - 00_governance_01_documentation-governance.md
  - 00_governance_02_canonical-source-rule.md
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - 05_agent_06_01_tool-execution-and-approval-execution.md
  - 03_rag_03_05_query_pipeline-augment-stages.md
  - 04_mcp_06_16_pre-production-fail-open-checklist.md
  - 04_mcp_06_17_local-to-production-auth-migration.md
  - 04_mcp_02_03_audit-logging-and-errors.md
  - 04_mcp_06_07_reading-audit-logs.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 03_rag_03_05_query_pipeline-augment-stages.md
  - 03_rag_04_02_dto-models_result.md
  - 05_failure_modes_and_operational_readiness.md
source:
  - 00_security_01_architecture-and-trust-boundaries.md
---

# System Security Architecture and Trust Boundaries

## Purpose / how to use this doc

This document is the canonical cross-cutting security architecture reference for the project. It synthesizes trust boundaries, protected assets, threat model, per-API authentication/authorization, secret lifecycle, log redaction, audit retention, local-vs-production behavior, fail-open/closed behavior, and prompt-injection responsibility boundaries from existing scattered documentation. Other documents should cross-reference this document rather than duplicate its content.

## Trust-boundary diagram

```
Agent -> LLM -> MCP -> target resource
      \-> RAG ingestion path -> vector store
```

Two primary boundary crossings exist:

1. **Agent → MCP**: The Agent invokes MCP tools via the MCP protocol. This boundary crosses from the Agent process (which handles LLM interaction, approval workflows, and session state) to MCP server processes (which execute tools against external resources). The boundary enforces tool-level approval, path allowlist validation, and command allowlist checks.

2. **RAG ingestion path → vector store**: During ingestion, external content (web pages, documents) is fetched, processed, and embedded. The boundary crosses from the ingestion pipeline (which handles untrusted external content) into the vector store (which stores embeddings for retrieval). This boundary enforces content sanitization, size limits, and embedding model consistency.

## Protected assets

The following assets are protected by the security architecture:

- **Filesystem under `allowed_dirs`**: MCP file servers restrict operations to configured allowlist directories
- **Git repositories**: Git MCP server restricts operations to `allowed_repo_paths`
- **GitHub repositories**: GitHub MCP server restricts to `allowed_repos`
- **CI/CD workflows**: CI/CD MCP server restricts to allowed workflows/repos
- **DB files**: SQLite databases (agent, RAG, EventBus) protected by filesystem permissions and SQLite-level constraints
- **Audit logs**: JSON-lines audit log files protected by filesystem permissions and retention policies
- **Secrets**: API keys, tokens, encryption keys stored in config files with filesystem permissions

## Threat model

The threat model covers the following threat vectors:

- **Untrusted LLM output**: LLM may generate malicious tool calls, paths, or arguments; mitigated by tool argument validation, path allowlists, command allowlists, and approval workflows
- **Untrusted RAG-ingested content**: Ingested web content may contain malicious payloads; mitigated by `sanitize_document()` in `03_rag_03_05`, size limits, and content-type validation
- **Untrusted tool arguments**: Tool arguments may contain path traversal, command injection, or SQL injection; mitigated by `validate_tool_arguments()` in `05_agent_06_01`, path resolution via `Path.resolve()`, and command allowlists
- **Path/symlink escape**: Attempts to escape `allowed_dirs`/`allowed_repo_paths`; mitigated by `Path.resolve()` before allowlist comparison
- **Command-allowlist bypass**: Attempts to execute unauthorized commands; mitigated by command allowlist enforcement in shell MCP and shell tool
- **Unauthorized repo/workflow access**: Attempts to access unauthorized GitHub repos or CI/CD workflows; mitigated by `allowed_repos` and workflow allowlists
- **Execution without approval**: High-risk tools executed without required approval; mitigated by approval workflow in `05_agent_06_01`/`05_agent_06_02`

## Per-externally-reachable-API authN/authZ table

| MCP Server | Transport | AuthN | AuthZ | Notes |
|---|---|---|---|---|
| file-read | HTTP/stdio | Bearer token (optional) | `allowed_dirs` allowlist | Read-only; path allowlist enforced |
| file-write | HTTP/stdio | Bearer token (optional) | `allowed_dirs` allowlist + approval | Write requires approval for `WRITE_DANGEROUS` tools |
| file-delete | HTTP/stdio | Bearer token (optional) | `allowed_dirs` allowlist + approval | Delete requires approval |
| shell | HTTP/stdio | Bearer token (optional) | Command allowlist + approval | `command_allowlist` restricts executable commands |
| git | HTTP/stdio | Bearer token (optional) | `allowed_repo_paths` + approval | Git write tools require approval; protected branches enforced |
| github | HTTP | Bearer token (required) | `allowed_repos` + `protected_branches` | `protected_branches` escalate to high risk |
| cicd | HTTP | Bearer token (optional) | Workflow allowlist | Workflow execution restricted to allowlisted workflows |
| mdq | HTTP | Bearer token (optional) | `allowed_dirs` equivalent | Path traversal prevention via `Path.resolve()` |
| rag-pipeline | HTTP | Bearer token (optional) | Query/ingest separation | Ingestion requires separate config; query is read-only |

*Source: `04_mcp_05_01_access-control-and-allowlists.md`, `04_mcp_05_02_auth-profiles-and-sandboxing.md`*

## Secret lifecycle

Secret lifecycle management covers:

- **Provisioning**: Secrets provisioned via config files (`config/agent.toml`, `config/*_mcp_server.toml`) and environment variables; no hardcoded secrets in code
- **Storage**: Secrets stored in config files with filesystem permissions (0600); no secrets in git history
- **Rotation**: Operator replaces secret value in config and restarts affected services; no hot-reload for secrets (per `04_mcp_06_17_local-to-production-auth-migration.md`)
- **Revocation**: Removing secret from config and restarting services invalidates it immediately; no separate revocation list

*Source: `04_mcp_06_17_local-to-production-auth-migration.md`*

## Log redaction rules

Audit log redaction follows these rules:

- **Redacted fields**: `artifacts`, `rag_stage_outcomes` (list contents replaced with `{_redacted: true, count: N}`)
- **Pattern-based redaction**: API keys, secrets, tokens, passwords, bearer tokens detected via regex in `04_mcp_02_03_audit-logging-and-errors.md` and redacted
- **Preserved**: Non-sensitive fields, error messages without secrets, operational metadata

*Source: `04_mcp_02_03_audit-logging-and-errors.md`*

## Audit retention

Audit retention policy:

- **Retention period**: Configured via `retention_days` in `config/agent.toml` `[diagnostics]` section (default 30 days)
- **Purge mechanism**: Lazy purge on each `DiagnosticStore.save()` — deletes rows older than `retention_days` from `session_diagnostics` table
- **Disabled purge**: `retention_days <= 0` disables automatic purge
- **Audit log files**: JSON-lines files at `audit_log_file` path rotated by external logrotate; no application-level rotation

*Source: `04_mcp_06_07_reading-audit-logs.md`, `05_agent_10_02_operations-and-observability-audit-and-otel.md`*

## Local-vs-production behavior

Behavior differences between local development and production:

| Aspect | Local (`security_profile=local`) | Production (`security_profile=production`) |
|---|---|---|
| `allow_public_bind` | Default `false`; can be overridden | Must be `false` or explicit `true` with token |
| Bearer token | Optional (defaults to empty) | Required for public bind; enforced at startup |
| Tool safety tiers | Warning on unknown keys | Fatal on unknown keys |
| `approval_github_allowed_repos` | Empty = allow all (dev) | Empty = deny all (fail-closed) |
| `gitops_push_blocked` | `false` (dev) | `true` recommended (prod) |
| Audit log redaction | Enabled | Enforced |
| Approval dry-run | Enabled for configured tools | Enforced per `approval_dry_run_tools` |

*Source: `04_mcp_06_16_pre-production-fail-open-checklist.md`, `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` §Audit during startup*

## Fail-open-vs-fail-closed behavior

Fail-open vs fail-closed behavior by component:

| Component | Default | Production | Notes |
|---|---|---|---|
| Tool safety tier unknown | Fail-open (warn) | Fail-closed (fatal) | `tool_safety_tiers` unknown key |
| `approval_github_allowed_repos` empty | Allow all | Deny all | Fail-closed in production |
| `allowed_dirs` empty | Allow none (fail-closed) | Allow none | Consistent |
| `allowed_repos` empty | Allow none | Allow none | Consistent |
| `allow_public_bind` | `false` (fail-closed) | `false` enforced | `true` requires token |
| MCP tool approval | `medium` default | Per `approval_risk_rules` | Configurable per tool |
| Shell command allowlist | Empty = none allowed | Configured explicitly | Fail-closed by default |

*Source: `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` §Summary of Fail-Open vs Fail-Closed, cross-referenced with `05_failure_modes_and_operational_readiness.md`*

## Prompt-injection responsibility boundaries

Prompt injection responsibility is distributed across layers:

| Boundary Crossing | Responsible Layer | Mechanism |
|---|---|---|
| User input → Agent | Agent | Input sanitization in `05_agent_06_01`; tool argument validation |
| Agent → LLM | Agent | System prompt construction; no user input in system prompt |
| LLM output → Tool args | Agent | `validate_tool_arguments()` in `05_agent_06_01`; schema validation |
| Tool args → MCP server | MCP | Path allowlist, command allowlist, schema validation |
| RAG ingestion → Vector store | RAG ingestion | `sanitize_document()` in `03_rag_03_05` removes scripts, iframes, suspicious patterns |
| RAG query → LLM | Agent | Retrieved chunks passed as context; `was_sanitized` flag in `03_rag_04_02` |

*Source: `03_rag_03_05_query_pipeline-augment-stages.md` (`sanitize_document()`), `03_rag_04_02_dto-models_result.md` (`was_sanitized`, `patterns_detected`)*

## Related Documents

- `00_security_02_high-risk-tool-common-policy.md`
- `00_governance_01_documentation-governance.md`
- `00_governance_02_canonical-source-rule.md`
- `04_mcp_05_01_access-control-and-allowlists.md`
- `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
- `05_agent_06_01_tool-execution-and-approval-execution.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `04_mcp_06_16_pre-production-fail-open-checklist.md`
- `04_mcp_06_17_local-to-production-auth-migration.md`
- `04_mcp_02_03_audit-logging-and-errors.md`
- `04_mcp_06_07_reading-audit-logs.md`
- `05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_04_02_dto-models_result.md`
- `05_failure_modes_and_operational_readiness.md`

## Keywords

security, architecture, trust-boundaries, threat-model, auth, audit, prompt-injection