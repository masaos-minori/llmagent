---
title: "ADR-002: Per-Process Configuration Ownership and Config Isolation"
area: governance
tags:
  - system
  - configuration
  - config-isolation
decision_scope:
  - system
related:
  - ADR-001-workflow-engine-mandatory.md
  - agent_08_01_configuration-loading-agent-config.md
  - mcp_06_02_configuration-file-inventory.md
  - shared_03_01_runtime_and_execution-config-and-logging.md
  - adr_02_config-isolation-supporting-sections.md
supersedes: []
superseded_by: null
---

# ADR-002: Per-Process Configuration Ownership and Config Isolation

## Keywords

configuration
config isolation
per-process ownership
secrets
environment variables

## Summary

This ADR canonicalizes the design in which the Agent, each MCP server, the RAG ingestion processes, and the EventBus own their own configuration files and read only the configuration files they are permitted to read. Creating a new shared configuration file is prohibited, and duplicated values are permitted as explicit dependency declarations of independent processes. Minimal exposure of Secrets and Prefix/Allowlist rules for environment variables prevent configuration leakage across process boundaries.

## Context

### Problem

When multiple processes (Agent, MCP servers, crawler, ingester, chunk_splitter, eventbus) read the same configuration file, configuration ownership becomes unclear, and excessive Secret exposure and configuration interdependence arise. In addition, creating a new shared configuration file complicates distributed configuration management and makes the impact scope of a configuration change impossible to grasp.

### Constraints

- Execution on a single host with multiple processes is assumed
- In the deployment environment, the existence of each process's configuration file must be confirmed before startup
- Security requirement: Secrets must be exposed only to the processes that need them
- Data integrity: each process's configuration must be managed independently
- Operational requirement: the impact scope and restart targets of a configuration change must be determinable per owning process

### Assumptions

- Target environment: a single host, multiple processes
- Expected scale: limited concurrency
- Trust boundary: privileges are granted only within each process
- External dependencies: none (configuration files are local files)
- Items to re-evaluate if the assumptions no longer hold: multi-host configuration, distributed execution, integration with an external configuration store

## Decision

### Decision Details

1. The Agent reads only `config/agent.toml`.
2. Each MCP server reads only `config/<key>_mcp_server.toml`.
3. The crawler reads only `config/crawler.toml`.
4. chunk_splitter reads only `config/chunk_splitter.toml`.
5. The ingester reads only `config/ingester.toml`.
6. The EventBus reads only `config/eventbus.toml`.
7. The Agent does not interpret MCP-server-internal configuration.
8. MCP servers do not reference `agent.toml`.
9. Using a shared Config Loader is permitted, but the permitted files are restricted per process, and reading a non-permitted file is a Runtime Error.
    *Note: EventBus is an exception — it loads its own config through the shared loader without `restrict_to()`; isolation is enforced by a local invariant instead (see CI-001).*
10. No new shared configuration file is created.
11. Duplication of values such as DB paths, URLs, and Timeouts across multiple configurations is permitted as explicit dependency declarations of independent processes.
12. Even when a key with the same name exists in multiple files, each is treated as a separate configuration contract.
13. Secrets are exposed only to the processes that need them. Environment variables also have a Prefix or an Allowlist.
14. The impact scope and restart targets of a configuration change are determined per owning process.
15. Configuration is not implicitly loaded at module import time.

### Scope

- **Target components**: `ConfigLoader`, `MCPServer`, `Orchestrator`
- **Target processes**: the Agent process, each MCP server process, the crawler process, the ingester process, the chunk_splitter process, the eventbus process
- **Target data**: configuration files, environment variables, Secrets
- **Target Environment Profile**: all environments (local/dev/production)
- **Target APIs or processing paths**: `ConfigLoader.restrict_to()`, `ConfigLoader.load()`, `MCPServer.run_http()`

### Out of Scope

- Details of individual configuration file schemas
- Detailed Prefix/Allowlist design for environment variables
- Details of how the EventBus integration loads its configuration
- Changes to runtime behavior
- Monitoring and metrics design (handled by a separate ADR)

## Rationale

### 1. Primary Reason for Adoption — Security

Minimal exposure of Secrets prevents configuration leakage across process boundaries. Because each process reads only its own configuration file, access to other processes' Secrets is physically blocked.

### 2. Second Reason for Adoption — Operability

The impact scope and restart targets of a configuration change can be made clear per owning process. Because there is no shared configuration file, a configuration change does not unexpectedly affect other processes.

### 3. Third Reason for Adoption — Data Integrity

Because each process's configuration is managed independently, data corruption from configuration conflicts or overwrites is prevented. Making it explicit that same-named keys can have different meanings prevents unintended sharing of configuration.

Do not use "the current code is implemented this way" as the sole reason for adoption.

## Alternatives Considered

This section is maintained in the companion document: [Alternatives Considered](adr_02_config-isolation-supporting-sections.md#alternatives-considered).

## Consequences

### Positive Consequences

- Minimal exposure of Secrets is ensured
- The impact scope of a configuration change becomes clear
- Each process's configuration is managed independently
- MCP servers do not depend on the Agent's configuration
- Configuration file ownership becomes clear

### Negative Consequences

- The same values must be written in multiple places
- The number of configuration files increases
- Dual paths are needed during the migration period
- Overhead of keeping configuration files consistent

### Operational Consequences

- The existence of each process's configuration file must be confirmed at startup
- A configuration change requires restarting the owning process
- Incident response requires investigating configuration files

### Security Consequences

- Trust boundary: privileges are granted only within each process
- Authentication and authorization: permission decisions based on configuration files
- Secret handling: follow the principle of minimal exposure
- Fail-Closed: abort startup when a configuration file is missing
- Audit Log: record configuration loading events

## Per-Process Required Files and Keys

| Process | Required Config File(s) | Required Keys | Empty-Allowed Keys |
|---|---|---|---|
| Agent | `config/agent.toml` | llm_url, http_timeout, llm_max_retries, llm_retry_base_delay, llm_temperature, llm_max_tokens, title_llm_temperature, title_llm_max_tokens, sse_heartbeat_timeout, sse_malformed_retry, sse_reconnect_max, llm_stream_retry_on_heartbeat_timeout, llm_stream_retry_on_malformed_chunk, tokenize_url, context_token_limit, context_char_limit, context_compress_turns, history_protect_turns, budget_warn_ratio, llm_compress_temperature, llm_compress_max_tokens, embed_url, use_refiner, refiner_max_tokens, refiner_timeout, refiner_max_chars_per_chunk, serial_tool_calls, tool_definitions_strict, routing_drift_strict, tool_dedup_max_repeats, tool_cycle_detect_window, tool_error_max_consecutive, tool_error_retry_max, tool_concurrency_limits, masked_fields, plan_blocked_tools, max_tool_turns, tool_result_max_llm_chars, tool_results_turn_max_chars, tool_definitions, system_prompts, allowed_tools, use_memory_layer, memory_jsonl_dir, memory_max_inject_semantic, memory_max_inject_episodic, memory_min_importance, memory_embed_enabled, memory_dedup_threshold, memory_max_content_chars, memory_embed_timeout_sec, memory_retention_days, memory_fts_limit, memory_rrf_k, memory_recency_days, memory_local_only, mcp_servers, security_profile, security_lockdown_enabled, approval_risk_rules, approval_protected_paths, approval_high_risk_branches, approval_shell_safe_prefixes, approval_resource_keys, approval_dry_run_tools, tool_safety_tiers, allowed_root, approval_github_allowed_repos, gitops_push_blocked, otel_enabled, otel_endpoint, otel_service_name, audit_log_file, structured_log, agent_memory_max_startup_snippets | llm_url, tokenize_url, embed_url, allowed_root, encryption_key, otel_endpoint, otel_service_name, audit_log_file, system_prompt_tool |
| MCP Server (each) | `config/<name>_mcp_server.toml` | mcp_servers, security_profile, security_lockdown_enabled, http_host, http_port, app_module, own_config_file | security_profile, security_lockdown_enabled, http_host, http_port |
| Crawler | `config/crawler.toml` | embed_url, use_refiner, refiner_max_tokens, refiner_timeout, refiner_max_chars_per_chunk, memory_embed_enabled, memory_dedup_threshold, memory_max_content_chars, memory_embed_timeout_sec, memory_retention_days, memory_fts_limit, memory_rrf_k, memory_recency_days, memory_local_only | embed_url, memory_embed_enabled, memory_dedup_threshold, memory_max_content_chars, memory_embed_timeout_sec, memory_retention_days, memory_fts_limit, memory_rrf_k, memory_recency_days, memory_local_only |
| Chunk Splitter | `config/chunk_splitter.toml` | embed_url, use_refiner, refiner_max_tokens, refiner_timeout, refiner_max_chars_per_chunk, memory_embed_enabled, memory_dedup_threshold, memory_max_content_chars, memory_embed_timeout_sec, memory_retention_days, memory_fts_limit, memory_rrf_k, memory_recency_days, memory_local_only | embed_url, memory_embed_enabled, memory_dedup_threshold, memory_max_content_chars, memory_embed_timeout_sec, memory_retention_days, memory_fts_limit, memory_rrf_k, memory_recency_days, memory_local_only |
| Ingester | `config/ingester.toml` | embed_url, use_refiner, refiner_max_tokens, refiner_timeout, refiner_max_chars_per_chunk, memory_embed_enabled, memory_dedup_threshold, memory_max_content_chars, memory_embed_timeout_sec, memory_retention_days, memory_fts_limit, memory_rrf_k, memory_recency_days, memory_local_only | embed_url, memory_embed_enabled, memory_dedup_threshold, memory_max_content_chars, memory_embed_timeout_sec, memory_retention_days, memory_fts_limit, memory_rrf_k, memory_recency_days, memory_local_only |
| EventBus | `config/eventbus.toml` (loaded through ConfigLoader without `restrict_to()`; see CI-001) | *N/A* | *N/A* |

## Invariants

- INV-01: Each process reads only its permitted configuration files.
- INV-02: Access to non-permitted configuration files is rejected.
- INV-03: An MCP server can start standalone without agent.toml.
- INV-04: The Agent can start without being given MCP-specific Secrets.

## Exceptions

None

### Note: The Restriction Is Unconditional

The `AGENT_RESTRICT_CONFIG` environment variable has been removed (legacy). Every process entry point always calls `ConfigLoader.restrict_to("agent.toml")`. Setting this environment variable is ignored, and reading a non-permitted file is always rejected.

## Failure Policy

### Fail-Fast Conditions

- A process's configuration file is missing
- A configuration file is invalid

### Fail-Open or Degraded Conditions

- In the local development environment, minor configuration-file validation errors are recorded as warnings

### Retry Policy

- Retry target: configuration file loading failures
- Retry count: bounded by `retry_policy.max_attempts`
- Backoff: fixed interval
- Errors not retried: configuration file syntax errors

### Fallback Policy

- Fallback targets: none
- Fallback destination: none
- Conditions that prohibit Fallback: a missing configuration file
- Where Fallback reasons are recorded: audit log

## Data Ownership and Persistence

- **System of Record**: each process's configuration files (TOML format)
- **Derived Data**: regenerable derived data (SHA256 checksums of configuration files)
- **Ownership**: each process (owner of its configuration files)
- **Persistence**: file system (`config/` directory)
- **Transaction Boundary**: per configuration-file load
- **Recovery Source**: configuration files (manual recovery)
- **Deletion Rule**: deleting a configuration file requires restarting the related processes

## Verification

This section is maintained in the companion document: [Verification](adr_02_config-isolation-supporting-sections.md#verification).

## Implementation Notes

Briefly describe how the current implementation realizes the Decision.

This chapter is not a basis for design decisions. List detailed APIs, Classes, and Functions in the Implementation References.

Do not record line numbers; reference by File Path and Symbol name.

## Known Deviations

Record any discrepancy between this ADR and the current implementation, configuration, tests, or documents.

### CI-001: EventBus does not apply ConfigLoader.restrict_to()

- **Resolved**: CI-001 — EventBus config isolation is enforced by a local invariant instead of `restrict_to()`
- **Type**: Design Deviation
- **Summary**: EventBus loads its config through the shared loader but does not call ConfigLoader.restrict_to(), so the loader's per-process permission check is not applied
- **Conflicting Source**: docs/10_adr/ADR-002-config-isolation.md:Decision #9, scripts/eventbus/config.py (load_config()), scripts/eventbus/app.py
- **Expected Design**: All processes MUST load config through ConfigLoader.restrict_to() to enforce process-level config ownership boundaries
- **Observed Implementation**: EventBus config.py loads its own config through the shared loader without calling restrict_to(); the permission check is replaced by the local invariant described under Recommended Action
- **Impact**: Without the local invariant, EventBus could read configs belonging to other processes
- **Recommended Action**: Resolved via a local invariant instead of `restrict_to()`: load_config()'s docstring states callers must pass get_config_path()'s return value, and a regression test in tests/eventbus/test_eventbus_config.py locks both call sites in app.py to that invariant. Agent-side, ConfigLoader.restrict_to("agent.toml") was added to AgentContext.__init__ (scripts/agent/context.py).
- **Owner**: Team
- **Status**: resolved
- **Resolution Target**: Before ADR-002 moves from Proposed to Accepted status

## Review Triggers

Re-evaluate this ADR when any of the following conditions occurs.

- The operational scale or concurrency changes significantly
- The deployment changes from a single host to multiple hosts or a distributed configuration
- Security or audit requirements change
- Performance targets or resource constraints change
- An external protocol or adopted library is changed or discontinued
- Failure history shows that the assumptions or the Failure Policy are no longer valid
- The reasons for rejecting an alternative no longer hold

Add review conditions specific to this ADR.

- The configuration file format changes significantly
- A new shared configuration file becomes necessary
- Persistent storage moves to something other than files

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: when there is a security impact
- Operations Reviewer: when operations, monitoring, or recovery are affected
- Data Owner: when data ownership, schema, or retention are affected

### Approval Record

- **Approved By**: Task-level approval decision (repository administrator; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related Documents

### Companion Document

- [ADR-002 Supporting Sections](adr_02_config-isolation-supporting-sections.md)

### Related ADRs

- ADR-001: Mandatory Workflow Engine

### Specifications

- [Configuration Loading](../23_agent/agent_08_01_configuration-loading-agent-config.md) — details of Agent configuration loading
- [MCP Configuration File Inventory](../22_mcp/mcp_06_02_configuration-file-inventory.md) — list of MCP configuration files

### Operations

- [Runtime and Execution - Config and Logging](../40_shared/shared_03_01_runtime_and_execution-config-and-logging.md) — runtime configuration and logging

### Known Issues

- None

### Implementation References

- `scripts/shared/config_loader.py` — `ConfigLoader.restrict_to()`, `ConfigLoader.load()`
- `scripts/mcp_servers/server.py` — `MCPServer.run_http()`
- `scripts/rag/ingestion/crawler.py` — configuration loading for the `crawler` process
- `scripts/rag/ingestion/chunk_splitter.py` — configuration loading for the `chunk_splitter` process
- `scripts/rag/ingestion/ingester.py` — configuration loading for the `ingester` process
- `config/agent.toml` — Agent configuration file
- `config/*_mcp_server.toml` — MCP server configuration files
- `config/crawler.toml` — crawler configuration file
- `config/chunk_splitter.toml` — chunk_splitter configuration file
- `config/ingester.toml` — ingester configuration file
- `config/eventbus.toml` — EventBus configuration file
- Tests — `tests/shared/test_config_loader.py`, `tests/agent/test_config_permission_cross_server.py`

## Impact of REQ-001

With REQ-001's fix (strict-default behavior), the config isolation boundary is now enforced at startup time rather than being silently bypassed when `agent.toml` is missing. This ensures that:

1. Config isolation violations are detected early (fail-closed).
2. No process can start with incomplete configuration.
3. The strict-default applies uniformly across all environments.

## Impact of REQ-005

REQ-005 adds a per-process required-file/required-key/empty-allowed-key table to this ADR, making explicit which keys each process requires vs. may legitimately omit. This supports operators in auditing configuration completeness without requiring them to read dataclass definitions directly.

## Completion Checklist

Confirm the following before changing the ADR to Accepted.

- [x] The problem to solve is clear
- [x] The Decision is narrowed to one primary design decision
- [x] The Decision is stated in clear terms such as mandatory, prohibited, canonical, or Fallback conditions
- [x] The reasons for adoption are explained from perspectives other than the current implementation
- [x] Substantive alternatives and the reasons for rejecting them are recorded
- [x] Positive Consequences are recorded
- [x] Negative Consequences are recorded
- [x] The impact on Security has been evaluated
- [x] The impact on Operations, Monitoring, and Recovery has been evaluated
- [x] Verifiable Invariants are defined
- [x] Exceptions or out-of-scope cases are clear
- [x] Each Invariant has a corresponding Verification
- [x] Automatable verification does not rely only on Manual Review
- [x] Migration, or the reason no migration is needed, is recorded
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [ ] Discrepancies with the current implementation are registered as Known Issues
- [ ] The Owner and required Reviewers are defined
- [ ] Review Triggers are recorded
- [ ] The ADR is registered in the ADR index and the Document Guides of related areas
