---
title: "System Security Architecture and Trust Boundaries"
area: governance
tags:
  - security
  - architecture
  - trust-boundaries
  - threat-model
  - auth
  - audit
related:
  - security_02_high-risk-tool-common-policy.md
  - governance_01_documentation-policy.md
  - mcp_05_01_access-control-and-allowlists.md
  - mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - agent_06_01_tool-execution-and-approval-execution.md
  - rag_03_05_query_pipeline-augment-stages.md
  - mcp_06_13_pre-production-fail-open-checklist.md
  - mcp_06_14_mcp-authentication-setup.md
  - mcp_02_03_audit-logging-and-errors.md
  - shared_03_01_runtime_and_execution-config-and-logging.md
  - mcp_06_05_reading-audit-logs.md
  - agent_10_02_operations-and-observability-audit-and-otel.md
  - agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - rag_04_dto-models-types.md
  - rag_05_02-execution-guide.md
---

# System Security Architecture and Trust Boundaries

## Purpose / how to use this doc

This document is the canonical cross-cutting security architecture reference for the project. It synthesizes trust boundaries, protected assets, threat model, per-API authentication/authorization, secret lifecycle, log redaction, audit retention, production behavior (the only security profile), fail-open/closed behavior, and prompt-injection responsibility boundaries from existing scattered documentation. Other documents should cross-reference this document rather than duplicate its content.

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
- **Audit logs**: JSON-lines audit log files protected by filesystem permissions; no application-level retention or rotation is applied
- **Secrets**: API keys and tokens held in the process environment and referenced from config files as `${ENV:VAR_NAME}`; config files contain references, not secret values

## Threat model

The threat model covers the following threat vectors:

- **Untrusted LLM output**: LLM may generate malicious tool calls, paths, or arguments; mitigated by tool argument validation, path allowlists, command allowlists, and approval workflows
- **Untrusted RAG-ingested content**: Ingested web content may contain malicious payloads; mitigated by `sanitize_document()` in `rag_03_05`, size limits, and content-type validation
- **Untrusted tool arguments**: Tool arguments may contain path traversal, command injection, or SQL injection; mitigated by `validate_tool_arguments()` in `agent_06_01`, path resolution via `Path.resolve()`, and command allowlists
- **Path/symlink escape**: Attempts to escape `allowed_dirs`/`allowed_repo_paths`; mitigated by `Path.resolve()` before allowlist comparison
- **Command-allowlist bypass**: Attempts to execute unauthorized commands; mitigated by command allowlist enforcement in shell MCP and shell tool
- **Unauthorized repo/workflow access**: Attempts to access unauthorized GitHub repos or CI/CD workflows; mitigated by `allowed_repos` and workflow allowlists
- **Execution without approval**: High-risk tools executed without required approval; mitigated by approval workflow in `agent_06_01`/`agent_06_02`

## Per-externally-reachable-API authN/authZ table

| MCP Server | Transport | AuthN | AuthZ | Notes |
|---|---|---|---|---|
| file-read | HTTP | Bearer token (required) | `allowed_dirs` allowlist | Read-only; path allowlist enforced |
| file-write | HTTP | Bearer token (required) | `allowed_dirs` allowlist + approval | Write tools are `WRITE_SAFE` but carry a `medium` rule, so they require a `y/N` approval |
| file-delete | HTTP | Bearer token (required) | `allowed_dirs` allowlist + approval | Delete requires approval |
| shell | HTTP | Bearer token (required) | Command allowlist + approval | `command_allowlist` restricts executable commands |
| git | HTTP | Bearer token (required) | `allowed_repo_paths` + approval | `git_checkout`/`git_pull`/`git_push` require full-word `yes` approval; `git_add`/`git_commit` have no prompt by default; protected branches enforced |
| github | HTTP | Bearer token (required) | `allowed_repos` + `protected_branches` | `protected_branches` escalate to high risk |
| cicd | HTTP | Bearer token (required) | Workflow allowlist | Workflow execution restricted to allowlisted workflows |
| mdq | HTTP | None at HTTP layer (empty token skips auth by design; see `mcp_05_05_mdq-enforcement-and-lockdown.md`) | `allowed_dirs` allowlist (fail-closed) | Path traversal prevention via `Path.resolve()` |
| rag-pipeline | HTTP | Bearer token (required) | Tool safety tiers + approval | Search and list tools are `READ_ONLY`; `rag_delete_document` is `WRITE_DANGEROUS` and requires approval; no ingestion tool is exposed |

*Source: `mcp_05_01_access-control-and-allowlists.md`, `mcp_05_02_auth-profiles-and-sandboxing.md`*

## Secret lifecycle

Secret lifecycle management covers:

- **Provisioning**: Secrets are provisioned as environment variables; `config/agent.toml` and `config/*_mcp_server.toml` reference them with `${ENV:VAR_NAME}` (resolved by `resolve_env_ref()` in `scripts/shared/config_utils.py`, which raises `ValueError` when the variable is unset); no hardcoded secrets in code (Explicit in code — scripts/shared/config_utils.py)
- **Storage**: Secret values live only in the process environment (or the operator's secret management); config files committed to git hold only `${ENV:VAR_NAME}` references, so no secret values enter git history. File permissions on config files are not enforced by application code
- **Rotation**: Operator replaces the secret value in the environment (or secret source) and restarts affected services; no hot-reload for secrets (per `mcp_06_14_mcp-authentication-setup.md`)
- **Revocation**: Removing the secret from the environment and restarting services invalidates it immediately; no separate revocation list

*Source: `mcp_06_14_mcp-authentication-setup.md`*

## Log redaction rules

Log redaction follows these rules:

- **Secret redaction in log records**: every configured logger applies `_RedactionFilter`, which redacts any `Bearer <token>` match and any exact match against a registered secret value. `register_secret()` is called for every resolved MCP `auth_token`, so a token does not reach a log line even if a caller logs a raw header or config value. No other pattern-based redaction (for example generic API-key or password regexes) exists.
- **Session diagnostics payload**: list-valued sensitive fields (`artifacts`, `rag_stage_outcomes`, plus any fields configured in `[diagnostics]`) are replaced with `{_redacted: true, count: N}` by `DiagnosticStore`. This applies to `session_diagnostics` rows, not to MCP audit records.
- **Preserved**: Non-sensitive fields and operational metadata.

*Source: `shared_03_01_runtime_and_execution-config-and-logging.md`* (Explicit in code — `scripts/shared/logger.py`, `scripts/agent/diagnostic_store.py`)

## Audit retention

Audit retention policy:

- **Audit log files**: JSON-lines files at the `audit_log_file` path. No application-level retention, rotation, or cleanup exists; rotation and removal are left to the operator (no logrotate configuration is provided by the repository). (Explicit in code — `scripts/mcp_servers/audit.py`, `scripts/eventbus/audit.py`)
- **Session diagnostics (separate from audit log files)**: `retention_days` in the `[diagnostics]` section of `config/agent.toml` governs `session_diagnostics` rows only. Rows older than `retention_days` are purged lazily on each `DiagnosticStore.save()`; `retention_days <= 0` disables the purge. (Explicit in code — `scripts/agent/config_dataclasses.py`)

*Source: `mcp_06_05_reading-audit-logs.md`, `agent_10_02_operations-and-observability-audit-and-otel.md`*

## Production behavior (single security profile)

`SecurityProfile` has a single `PRODUCTION` member, so every environment runs the
production behavior unconditionally. Event Bus and every MCP server bind to loopback
(`127.0.0.1`/`::1`) only, with no override possible.

| Aspect | Behavior |
|---|---|
| Bind address | Loopback-only, no override |
| Bearer token | The agent-side `auth_token` must be non-empty for every enabled HTTP MCP server (enforced at startup); mdq-mcp does not verify it at the HTTP layer (see `mcp_05_05_mdq-enforcement-and-lockdown.md`) |
| Tool safety tiers | Fatal on unknown keys |
| `approval_github_allowed_repos` | Empty = deny all (fail-closed) |
| `gitops_push_blocked` | `true` recommended |
| Audit log redaction | Enforced |
| Approval dry-run | Enforced per `approval_dry_run_tools` |

*Source: `mcp_06_13_pre-production-fail-open-checklist.md`, `mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` Audit during startup*

## Fail-open-vs-fail-closed behavior

Fail-open vs fail-closed behavior by component. There is a single security profile (`PRODUCTION`), so no per-environment column applies:

| Component | Behavior | Notes |
|---|---|---|
| Tool safety tier missing or unknown | Fail-closed (fatal at startup) | `tool_safety_tiers` entries must match registered tools exactly |
| `approval_github_allowed_repos` empty | Fail-closed (deny all GitHub mutation tools) | Pre-flight check in `agent/tool_policy.py` |
| `allowed_dirs` empty | Fail-closed (allow none) | |
| `allowed_repos` (github-mcp) empty | Fail-closed (denies all writes; no fail-open mode exists) | See `mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` Fail-Open vs Fail-Closed Summary |
| MCP server bind address | Loopback-only binding is unconditional | No override key exists |
| MCP tool approval | Safety-tier default, overridable per tool by `approval_risk_rules` | Tier mapping and prompt behavior: `agent_06_02_tool-execution-and-approval-approval.md` |
| Shell command allowlist | Empty = none allowed | Fail-closed by default |

*Source: `mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` Summary of Fail-Open vs Fail-Closed*

## Prompt-injection responsibility boundaries

Prompt injection responsibility is distributed across layers:

| Boundary Crossing | Responsible Layer | Mechanism |
|---|---|---|
| User input → Agent | Agent | Message structure validation when appended to history (disallowed keys are stripped); user-input content is not filtered for injection patterns |
| Agent → LLM | Agent | System prompt construction; no user input in system prompt |
| LLM output → Tool args | Agent | `validate_tool_arguments()` in `agent_06_01`; schema validation |
| Tool args → MCP server | MCP | Path allowlist, command allowlist, schema validation |
| RAG ingestion → Vector store | RAG ingestion | `sanitize_document()` in `rag_03_05` removes scripts, iframes, suspicious patterns |
| RAG query → LLM | Agent | Retrieved chunks passed as context; `was_sanitized` flag in `rag_04_dto-models-types.md` |

*Source: `rag_03_05_query_pipeline-augment-stages.md` (`sanitize_document()`), `rag_04_dto-models-types.md` (`was_sanitized`, `patterns_detected`)*

## Failure modes and operational readiness

### Failure mode categories

| Category | Impact | Recovery |
|---|---|---|
| MCP server unavailable | Capability unavailable | Automatic retry (subprocess), manual restart (persistent) |
| MCP server degraded | Capability degraded | Operator intervention required |
| Workflow schema missing | Agent startup fails | Run `bash deploy/init_db.sh` |
| Workflow definition invalid | Agent startup fails | Fix JSON per validation error |
| Embedding service unreachable at startup | Startup aborts with FATAL | Restore embed-llm, then restart the Agent |
| Embedding service down at runtime | Affected searches fall back to FTS; the memory layer becomes degraded when its circuit opens | Restart embed-llm service |
| Memory layer circuit open | Memory degraded | Wait for cooldown, then verify |
| Database corruption | Data loss risk | Restore from backup |
| Network partition | Multiple capabilities affected | Verify network connectivity |

### MCP failure behavior

| Startup Mode | Health Check | Failure Response | Recovery |
|---|---|---|---|
| `none` | None | Server treated as unavailable | Manual configuration change |
| `persistent` | `/health` endpoint | 503 on degraded; no automatic recovery by the agent | Operator restarts external server |
| `subprocess` | On-demand check at tool dispatch (`ensure_ready()`); no background watchdog | Start/restart on the next tool dispatch; a failed start triggers a cooldown during which dispatch is rejected | Wait for cooldown, or restart manually; use external process monitoring for liveness |

Fail-fast vs fail-open at MCP startup failure: `production` raises `RuntimeError` (aborts startup, no REPL started).

*Source: `shared/mcp_health.py`, `agent/factory.py`*

### Workflow deployment failures

Full failure-scenario table (missing definition, invalid JSON, checksum mismatch, schema incomplete/version mismatch, stage execution failure) and remediation commands: [Workflow Deployment Runbook](../23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook).

### RAG failure behavior

| Scenario | Degraded State | Recovery |
|---|---|---|
| Embedding API down (HTTP 503) at runtime | Affected searches fall back to FTS; memory circuit open means degraded | Restart embed-llm |
| Embedding dimension mismatch | Chunk skipped, WARNING logged | Verify the embedding model's output matches `scripts/db/store_protocols.py::get_embedding_dims()` (a fixed code-level constant, not a config key) |
| Vector store corruption | RAG unavailable | Restore from backup |
| FTS index desync (`fts_gap != 0`) | Search results incomplete | Run `/session rag-consistency` to inspect (`scripts/db/rag_consistency.py` is a library module, not a CLI entry point) |
| Orphan vector rows (`orphan_vec_count > 0`) | Search returns stale results | Run `ingester.py --force` |
| Crawler timeout | URL skipped, WARNING logged | Retry crawler execution |

When embedding is unavailable: existing documents remain searchable via FTS, new documents cannot be indexed, `memory_embed_enabled` remains `true` but embeddings are not generated, and the system logs a WARNING on each failed embedding attempt.

*Source: [rag_05_02-execution-guide.md](../21_rag/rag_05_02-execution-guide.md#105-rag-consistency-check-dbrag_consistencypy)*

### Memory layer failure behavior

| Mode | Condition | Behavior |
|---|---|---|
| disabled | `use_memory_layer=false` | No memory operations |
| fts-only | `memory_embed_enabled=false` or no embedding client (configuration only; never entered because of a health-check failure) | FTS search only, no embeddings |
| degraded | `circuit_open=True` | Circuit breaker open, skip embedding |
| hybrid | Normal operation | Full embedding + vector search |

Degraded conditions: `circuit_open=True` after more than `failure_threshold` consecutive failures; `half_open_cooldown_sec` elapsed since last UNAVAILABLE state; one request allowed through HALF_OPEN state to test recovery.

### Capability readiness model

| State | Meaning | HTTP Status |
|---|---|---|
| healthy | All dependencies operational | 200 |
| degraded | Some dependencies failing | 503 |
| unavailable | Critical dependency missing | 503 |
| unknown | Cannot determine status | N/A |

| Capability | Required Services | Degraded/Unavailable When |
|---|---|---|
| Repository Operations | git-mcp (+ optional github-mcp) | git-mcp degraded / unavailable |
| File Operations | file-read, file-write, file-delete | file-read / file-write / file-delete degraded / unavailable |
| Code Search | mdq-mcp | mdq-mcp degraded / unavailable |
| Web Search | web-search-mcp | web-search-mcp degraded / unavailable |
| CI/CD | cicd-mcp | cicd-mcp degraded / unavailable |
| Shell Execution | shell-mcp | shell-mcp degraded / unavailable |
| Document Retrieval | rag-pipeline-mcp (+ embed-llm) | embed-llm down / rag-pipeline-mcp unavailable |
| GitHub Operations | github-mcp | github-mcp degraded / unavailable |
| Memory Search | Agent memory store (embed-llm optional) | embed-llm unreachable at startup: FATAL; down at runtime: per-search FTS fallback, degraded when the circuit opens |

*Source: `agent/startup.py`*

### Operator-facing examples

```
[Retry exhausted] tool=<tool_name> status=<last retryable HTTP status> after <attempts> attempts
```
```
[FATAL] Session schema missing. Run: bash deploy/init_db.sh to initialize the database.
```

## EventBus Authentication and Authorization

The EventBus API enforces authentication and authorization as a fail-closed security boundary.

### Authentication

All EventBus routes require Bearer-token authentication. Requests without a valid
`Authorization: Bearer <token>` header receive HTTP 401 Unauthorized.

See [ADR-013-eventbus-authentication-authorization](../10_adr/ADR-013-eventbus-authentication-authorization.md)
for the authentication mechanism decision and configuration details.

### Authorization

Roles control access to EventBus routes:

| Role | Access |
|------|--------|
| Publisher | POST `/publish` |
| Consumer | GET `/subscribe`, POST `/events/{event_id}/ack`, POST `/nack` |
| Operator | GET `/dlq`, POST `/dlq/{event_id}/requeue`, GET `/replay` |
| Monitoring | GET `/health` |
| Admin | `/admin/*` routes |

A consumer's authenticated identity is bound to allowed `consumer_id`s and topics —
a caller cannot act as another consumer or access unauthorized topics.

DLQ administration (`/dlq`, `/dlq/{event_id}/requeue`) and privileged replay
(`/replay`) require operator permission.

See [ADR-013-eventbus-authentication-authorization](../10_adr/ADR-013-eventbus-authentication-authorization.md)
for the authorization model decision and role definitions.

### Loopback-only Binding

**Note**: The EventBus process already enforces loopback-only binding via
`EventBusConfig.__post_init__` and `_LoopbackVerifyingServer` (Explicit in code).
It is independent of the authentication/authorization controls described above and
acts as defense-in-depth.

## Keywords

- security
- architecture
- trust-boundaries
- threat-model
- auth
- audit
- prompt-injection
- failure-modes
- readiness
- degradation
- operational
