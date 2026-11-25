---
title: "Agent Configuration - Loading and AgentConfig Structure"
area: agent
tags:
  - agent
  - configuration
  - config-loading
related:
  - agent_00_document-guide.md
  - agent_08_02_configuration-llm-rag.md
  - agent_08_03_configuration-tools-memory.md
  - agent_08_04_configuration-mcp-approval-obs.md
  - agent_10_01_operations-and-observability-startup-and-health.md
---

# Agent Configuration

- Operations → [agent_10_01_operations-and-observability-startup-and-health.md](agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

Documents the `AgentConfig` structure, configuration file ownership, the classification of hot-reloads, and the per-key reference for the keys `config/agent.toml` defines.

## Design Intent

### Configuration Loading

`build_agent_config()` merges all configuration files through `ConfigLoader.load_all()` and then constructs the `AgentConfig` dataclass. Loading and assembly (including production validation) are separated from per-section construction, so the loader owns no per-section key reading (Explicit in code — `scripts/agent/config_builders.py`, `scripts/agent/config_section_builders.py`).

**Canonical Configuration File:** `config/agent.toml` (LLM/RAG/DB/Tools/Memory/Observability/Approval/MCP Lifecycle/Diagnostics)

**Fail-closed behavior:** When `agent.toml` is missing, `ConfigLoader.load_all()` raises `ConfigMissingError` (inherits `ValueError`), which `load_config()` re-raises as `ConfigLoadError` (inherits `RuntimeError`). Execution aborts before the security profile is resolved, so production config validation never runs on incomplete configuration.

### Configuration File Ownership

| File | Responsibility | Hot-Reloadable |
|---|---|---|
| `config/agent.toml` | Agent process settings | Mostly possible; `use_memory_layer`/`memory_embed_enabled` are startup-only; `diagnostics.*` is not applied by `/reload` but takes effect without restart on every `DiagnosticStore` save/fetch and is reported as `[LIVE]` |
| `config/*_mcp_server.toml` | MCP server specific settings | Requires restart (on add/remove/rename) |

### Settings Requiring Restart

- Changes to MCP server URL, authentication tokens, startup modes, commands, or environment variables.
- `use_memory_layer` — Enabling/disabling the memory subsystem (startup only).
- `memory_embed_enabled` — Enabling/disabling embedding generation and KNN search (startup only).
- `shutdown_deadline_seconds`, `shutdown_settle_seconds`, `shutdown_termination_confirm_seconds`, `shutdown_force_exit_on_second_sigint` — Read into `AgentConfig` at startup; no reload path re-arms a live shutdown budget.

### Hot-Reloadable Scope

The hot-reloadable set is exactly the `CONFIG_FIELD_REGISTRY` entries with `hot_reloadable=True`, the set
`registry_for` returns:

- LLM: `llm_url`, `llm_temperature`, `llm_max_tokens`, `llm_retry_base_delay`, `http_timeout`,
  `sse_heartbeat_timeout`, `sse_malformed_retry`, `sse_reconnect_max`,
  `llm_stream_retry_on_heartbeat_timeout`, `llm_stream_retry_on_malformed_chunk`
- Tool policy: `tool_policy_mode`, `allowed_tools`, `allowed_root`, `disabled_tools`,
  `plan_blocked_tools`, `serial_tool_calls`, `max_tool_turns`, `tool_result_max_llm_chars`
- Approval: `approval_github_allowed_repos`, `approval_high_risk_branches`,
  `approval_protected_paths`, `approval_shell_safe_prefixes`
- Memory: `memory_embed_url`, `memory_local_only`, `memory_retention_days`, `memory_max_pinned`

`masked_fields` is the one applied field outside the registry: it reaches the tool section through
`ConfigReloadRequest.masked_fields`.

- Startup-only: the entries `startup_only_for` returns — `context_char_limit`,
  `context_compress_turns`, `context_token_limit`, `use_memory_layer`, `memory_embed_enabled`,
  `approval_medium_preview_fallback`, `gitops_push_blocked`. `/reload` records a changed one as pending
  restart and applies nothing to the running process.
- MCP server definitions are never applied by `/reload`. An added, changed, or removed definition is
  recorded as pending and applied by the next restart of the owning process.
- `tokenize_url` is not a registry entry: `HistoryManager` reads it when the process builds it, so it
  stays restart-required and `/reload` reports nothing for it.
- System Prompt: prompt content is read from the single source (`registry/manifests/prompt_source.toml`) through the typed model; `ctx.conv.system_prompt_content` is the live copy, updated only in the reload commit phase

### Operational Impact of Changes

Check the `[OK]` / `[RESTART]` / `[STARTUP-ONLY]` / `[SKIP]` / `[LIVE]` categories reported after `/reload`; their meaning is defined in [agent_07_06](agent_07_06_cli-and-commands-hot-reload.md).

### Security-Related Settings

Changes to MCP server `auth_token`, `control_auth_token`, and to allowlists/denylists require a restart.

## Responsibility Boundary

- **Configuration Files**: `config/agent.toml` is the canonical source.
- **Field-level Mapping**: `agent/services/config_reload.py` is the canonical per-field classification.
- **Per-Key Reference**: this document owns the per-key reference. The code default is owned by the dataclass that declares it and the deployed value by `config/agent.toml`; the reference restates neither.

## Per-Key Reference (config/agent.toml)

Reference for every key `config/agent.toml` defines: the component that reads the key, the value type,
the unit the reading code applies, the default the owning dataclass declares, and the reload
classification.

Reading rules:

- The deployed value is not copied here. `config/agent.toml` is the canonical source for the current
  operational value (`skills/DESIGN.md` No concrete configuration values); this reference states only
  the code default.
- A unit is named only where the reading code establishes it. `n/a` means the value carries no unit. Where the reading code does not establish one, the Unit cell states that the unit is unverified rather than guessing it.
- Reload class reuses the categories defined in
  [agent_07_06](agent_07_06_cli-and-commands-hot-reload.md) and the classification
  `agent/services/config_reload.py` performs:
  - `[OK]` - `CONFIG_FIELD_REGISTRY` entry, applied by `/reload`.
  - `[STARTUP-ONLY]` - `CONFIG_FIELD_REGISTRY` entry with `hot_reloadable=False`; reported as
    startup-only.
  - `[RESTART]` - key is not a `CONFIG_FIELD_REGISTRY` entry, so `/reload` reports nothing for it and
    the running object keeps the value read at build time.
  - `[LIVE]` - `diagnostics.*`, effective on the next `DiagnosticStore` call without `/reload`.
- `masked_fields` is not a registry entry; it reaches the tool section through
  `ConfigReloadRequest.masked_fields`, so it is reported as applied.
- A key read by another process is scoped to that process's own configuration file. The RAG Pipeline MCP
  process reads the database paths, the SQLite extension path, and the two SQLite timeouts from
  `config/rag_pipeline_mcp_server.toml`; the rows below describe the Agent process.

### Explicit Values Equal Code Defaults

The default declared by the dataclass that owns a key is the single source of that key's value when the
key is absent from `config/agent.toml`. A value written in the file MUST equal that default: the file and
the code cannot disagree, and a difference is accepted only as an explicit, commented operational override
recorded in the file itself. Stating a value that equals the default records the deployed posture without
creating a second source, so this reference holds the code default and never the deployed value. Auditing
the policy means comparing each key the file states with the Code default column below.

### Database and retention

| Key name | Reading component | Value type | Unit | Code default | Reload class |
|---|---|---|---|---|---|
| `rag_db_path` | SQLiteHelper | string | path | `(no default: required)` | [RESTART] |
| `session_db_path` | rotate_session_db() | string | path | `(no default: required)` | [RESTART] |
| `workflow_db_path` | rotate_workflow_db() | string | path | `'/opt/llm/db/workflow.sqlite'` | [RESTART] |
| `sqlite_vec_so` | SQLiteHelper | string | path | `''` | [RESTART] |
| `sqlite_timeout` | SQLiteHelper | integer | seconds | `30` | [RESTART] |
| `sqlite_busy_timeout_ms` | apply_connection_pragmas() | integer | milliseconds | `30000` | [RESTART] |
| `sqlite_wal_checkpoint_mode` | checkpoint_wal() | string | mode name | `'TRUNCATE'` | [RESTART] |
| `sqlite_retention_max_sessions` | _delete_sessions_beyond_limit() | integer | session rows | `100` | [RESTART] |
| `sqlite_retention_max_age_days` | _delete_sessions_by_age() | integer | days | `90` | [RESTART] |
| `sqlite_archive_dir` | rotate_session_db() | string | path | `''` | [RESTART] |
| `sqlite_corrupt_archive_max_files` | purge_corrupt_archives() | integer | artifact files | `10` | [RESTART] |
| `sqlite_corrupt_archive_max_age_days` | purge_corrupt_archives() | integer | days | `30` | [RESTART] |
| `sqlite_archive_max_files` | _sweep_rotation_archives() | integer | artifact files | `14` | [RESTART] |
| `sqlite_archive_max_age_days` | _sweep_rotation_archives() | integer | days | `30` | [RESTART] |
| `sqlite_drill_artifact_max_files` | _sweep_drill_artifacts() | integer | artifact files | `14` | [RESTART] |
| `sqlite_drill_artifact_max_age_days` | _sweep_drill_artifacts() | integer | days | `30` | [RESTART] |
| `sqlite_quarantine_max_files` | _sweep_quarantine_dirs() | integer | artifact entries | `10` | [RESTART] |
| `sqlite_quarantine_max_age_days` | _sweep_quarantine_dirs() | integer | days | `90` | [RESTART] |
| `pending_timeout_minutes` | WorkflowEngine | integer | minutes | `10` | [RESTART] |

### LLM and context

| Key name | Reading component | Value type | Unit | Code default | Reload class |
|---|---|---|---|---|---|
| `llm_url` | LLMClient | string | URL | `''` | [OK] |
| `llm_retry_base_delay` | LLMClient | float | seconds | `1.0` | [OK] |
| `http_timeout` | LLMClient | float | seconds | `30.0` | [OK] |
| `context_char_limit` | HistoryManager | integer | characters | `8000` | [STARTUP-ONLY] |
| `context_compress_turns` | HistoryManager | integer | turns | `4` | [STARTUP-ONLY] |
| `context_token_limit` | HistoryManager | integer | tokens | `0` | [STARTUP-ONLY] |
| `tokenize_url` | HistoryManager | string | URL | `''` | [RESTART] |
| `history_protect_turns` | HistoryManager | integer | turns | `2` | [RESTART] |
| `llm_max_tokens` | LLMClient | integer | tokens | `1024` | [OK] |
| `llm_temperature` | LLMClient | float | n/a | `0.2` | [OK] |
| `sse_heartbeat_timeout` | RobustSSEParser | float | seconds | `30.0` | [OK] |
| `sse_malformed_retry` | RobustSSEParser | integer | attempts | `2` | [OK] |
| `sse_reconnect_max` | LLMClient | integer | attempts | `1` | [OK] |
| `llm_stream_retry_on_heartbeat_timeout` | LLMClient | boolean | n/a | `True` | [OK] |
| `llm_stream_retry_on_malformed_chunk` | LLMClient | boolean | n/a | `False` | [OK] |

### Tool execution and approval

| Key name | Reading component | Value type | Unit | Code default | Reload class |
|---|---|---|---|---|---|
| `max_tool_turns` | llm_turn_runner.run() | integer | turns | `5` | [OK] |
| `serial_tool_calls` | execute_all_tool_calls() | boolean | n/a | `False` | [OK] |
| `tool_dedup_max_repeats` | ToolLoopGuard | integer | identical calls | `3` | [RESTART] |
| `tool_cycle_detect_window` | ToolLoopGuard | integer | consecutive calls | `2` | [RESTART] |
| `tool_error_max_consecutive` | ToolLoopGuard | integer | consecutive failures | `3` | [RESTART] |
| `tool_error_retry_max` | ToolLoopGuard | integer | retries | `1` | [RESTART] |
| `tool_concurrency_limits` | ToolTransportInvoker | mapping | concurrent calls | `{}` | [RESTART] |
| `tool_result_max_llm_chars` | execute_one_tool_call() | integer | characters | `8000` | [OK] |
| `tool_results_turn_max_chars` | _collect_tool_result_msgs() | integer | characters | `50000` | [RESTART] |
| `masked_fields` | mask_args() | string list | field name | `['content', 'old_text', 'new_text']` | [OK] |
| `plan_blocked_tools` | ToolPolicy | string list | tool name | `list(_DEFAULT_PLAN_BLOCKED_TOOLS))` | [OK] |
| `tool_policy_mode` | check_preflight() | string | mode name | `'explicit_allowlist'` | [OK] |
| `allowed_tools` | check_preflight() | string list | tool name | `[]` | [OK] |
| `allowed_root` | ToolPolicy | string | path prefix | `''` | [OK] |
| `approval_github_allowed_repos` | check_allowed_repo() | string list | repo name | `[]` | [OK] |
| `approval_high_risk_branches` | _escalate_for_github_branch() | string list | branch name | `['main', 'master']` | [OK] |
| `approval_protected_paths` | _escalate_for_path() | string list | path prefix | `list(_DEFAULT_PROTECTED_PATHS))` | [OK] |
| `approval_shell_safe_prefixes` | _special_case_risk() | string list | command prefix | `list(_DEFAULT_SHELL_SAFE_PREFIXES))` | [OK] |

### Memory

| Key name | Reading component | Value type | Unit | Code default | Reload class |
|---|---|---|---|---|---|
| `use_memory_layer` | memory service factory | boolean | n/a | `True` | [STARTUP-ONLY] |
| `memory_jsonl_dir` | retired by ADR-008; removal pending (SHARED-003) | string | path | `'/opt/llm/memory'` | [RESTART] |
| `memory_max_inject_semantic` | retired by ADR-008; removal pending (SHARED-003) | integer | entries | `5` | [RESTART] |
| `memory_max_inject_episodic` | InjectionPolicy | integer | entries | `3` | [RESTART] |
| `memory_min_importance` | retired by ADR-008; removal pending (SHARED-003) | float | heuristic score | `0.3` | [RESTART] |
| `memory_dedup_threshold` | `_link_duplicates()` | float | unverified: compared as L2 distance, while the per-type values are on a 0-1 scale | `0.3` | [RESTART] |
| `memory_embed_url` | embedding client | string | URL | `''` | [OK] |
| `memory_embed_enabled` | memory service factory | boolean | n/a | `True` | [STARTUP-ONLY] |
| `memory_local_only` | memory service factory | boolean | n/a | `False` | [OK] |
| `memory_embed_timeout_sec` | embedding client | float | seconds | `5.0` | [RESTART] |
| `memory_max_content_chars` | memory store | integer | characters | `500` | [RESTART] |
| `memory_retention_days` | retired by ADR-008; removal pending (SHARED-003) | integer | days | `90` | [OK] |
| `memory_max_pinned` | retired by ADR-008; removal pending (SHARED-003) | integer | entries | `10` | [OK] |

### Observability

| Key name | Reading component | Value type | Unit | Code default | Reload class |
|---|---|---|---|---|---|
| `otel_enabled` | build_tracer() | boolean | n/a | `False` | [RESTART] |
| `otel_endpoint` | build_tracer() | string | URL | `''` | [RESTART] |
| `otel_service_name` | build_tracer() | string | name | `'llm-agent'` | [RESTART] |

### Diagnostics

| Key name | Reading component | Value type | Unit | Code default | Reload class |
|---|---|---|---|---|---|
| `diagnostics.encryption_key` | DiagnosticStore | string | key | `''` | [LIVE] |
| `diagnostics.retention_days` | DiagnosticStore | integer | days | `30` | [LIVE] |

### MCP server definitions

| Key name | Reading component | Value type | Unit | Code default | Reload class |
|---|---|---|---|---|---|
| `mcp_servers.*.transport` | McpServerConfig | enum | n/a | `(no default: required)` | [RESTART] |
| `mcp_servers.*.url` | McpServerConfig | string | n/a | `(no default: required)` | [RESTART] |
| `mcp_servers.*.startup_mode` | McpServerConfig | enum | n/a | `StartupMode.NONE` | [RESTART] |
| `mcp_servers.*.auth_token` | McpServerConfig | string | n/a | `''` | [RESTART] |
| `mcp_servers.*.control_auth_token` | McpServerConfig | string | n/a | `''` | [RESTART] |
| `mcp_servers.*.role` | McpServerConfig | string | n/a | `''` | [RESTART] |
| `mcp_servers.*.cmd` | McpServerConfig | string list | n/a | `[]` | [RESTART] |

### Shutdown and termination

| Key name | Reading component | Value type | Unit | Code default | Reload class |
|---|---|---|---|---|---|
| `shutdown_deadline_seconds` | ShutdownBudget (built in `scripts/agent/repl.py`) | float | seconds | `45.0` | [RESTART] |
| `shutdown_settle_seconds` | ResourceShutdownCoordinator | float | seconds | `10.0` | [RESTART] |
| `shutdown_termination_confirm_seconds` | ProcessTerminator (injected by `scripts/agent/factory.py`) | float | seconds | `2.0` | [RESTART] |
| `shutdown_force_exit_on_second_sigint` | SignalHandler | boolean | n/a | `False` | [RESTART] |
ROWS: 81
## Keywords

- configuration loading
- config file ownership
- hot-reload eligibility
- per-key configuration reference

## Removed Key Migration Reference (auto-generated)

<!-- AUTO-GENERATED: generate_reference_table.py agent-config-migration-reference -->
Generated from `_REMOVED_KEY_REPLACEMENTS` in `scripts/agent/production_config_validator.py` — the same mapping the fatal unknown-key error reads. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --manifests` to refresh.

| Removed key (`config/agent.toml`) | Replacement (single source) |
|---|---|
| `approval_dry_run_tools` | the per-tool preview_capability field in config/tool_catalog.toml |
| `approval_resource_keys` | the per-tool resource_scope_keys field in config/tool_catalog.toml |
| `approval_risk_rules` | the declared agent_safety_tier (the single risk source; no config replacement key) |
| `tool_safety_tiers` | the per-tool agent_safety_tier field in config/tool_catalog.toml |
<!-- END AUTO-GENERATED -->
