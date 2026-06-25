# Agent Configuration

- Operations → [05_agent_10_operations-and-observability.md](05_agent_10_operations-and-observability.md)

## Purpose

Document the complete `AgentConfig` structure, all 7 sub-configs with their fields,
configuration file layout, validation rules, `/reload` scope, and cross-field constraints.

---

## Configuration Loading

`build_agent_config()` (`agent/config.py:627`) calls `ConfigLoader.load_all()`
(`shared/config_loader.py`) which merges all config files into a dict, then constructs
the `AgentConfig` dataclass.

**Files loaded by `load_all()`:**

| File | Sub-config |
|---|---|
| `config/common.toml` | LLMConfig (http fields), RAGConfig, DbConfig |
| `config/llm.toml` | LLMConfig |
| `config/http.toml` | LLMConfig (http fields) |
| `config/context.toml` | LLMConfig (context fields) |
| `config/rag.toml` | RAGConfig |
| `config/tools.toml` | ToolConfig |
| `config/memory.toml` | MemoryConfig |
| `config/otel.toml` | ObservabilityConfig |
| `config/security.toml` | ApprovalConfig |
| `config/system_prompts.toml` | ToolConfig (system_prompts) |
| `config/mcp_servers.toml` | MCPConfig |
| `config/tools_definitions.toml` | ToolConfig (tool_definitions) |

For the canonical config ownership table (owning layer per file), see
[90_shared_03 §2a Config Ownership](90_shared_03_runtime_and_execution.md#2a-config-ownership).

`ctx.cfg` holds the config. `/reload` calls `ConfigLoader().load_all()` to
re-read all 12 base config files, then passes the merged dict to
`ConfigReloadService.apply_config_dict(new_cfg)` which updates `ctx.cfg`
fields and syncs live service instances.

The call chain is:
1. `ConfigLoader().load_all()` — re-reads all 12 files from `config/`
2. `ConfigReloadService.apply_config_dict(new_cfg)` — updates `ctx.cfg`
   fields and propagates changes to services
3. `ConfigReloadOutcome` — returned to the caller with `applied`,
   `needs_restart`, `skipped`, and `source_files` fields

### Config file ownership and hot-reload eligibility

`/reload` reads all 12 base config files — the same set loaded at startup.
`ConfigReloadService` classifies each changed key into one of four categories.

`config/common.toml` is the primary owner of `llm_url`, RAG defaults
(`top_k_search`, `embed_url`, `web_search_url`), and observability defaults
(`otel_endpoint`). These keys can also appear in other files; `common.toml`
provides project-wide defaults.

| File | Purpose | Classification |
|---|---|---|
| `config/common.toml` | LLM URL, RAG, observability defaults | Hot-reloadable |
| `config/llm.toml` | LLM model, temperature, max_tokens | Hot-reloadable |
| `config/http.toml` | HTTP client timeouts, retries | Hot-reloadable |
| `config/rag.toml` | RAG search settings | Hot-reloadable |
| `config/context.toml` | Context length, compression settings | Hot-reloadable |
| `config/tools.toml` | Tool execution, system prompt name | Hot-reloadable (most); `plugin_strict`, `plugin_dir` are startup-only |
| `config/memory.toml` | Memory layer settings | Hot-reloadable (most); `use_memory_layer` is startup-only |
| `config/otel.toml` | Observability / tracing | Hot-reloadable |
| `config/security.toml` | Approval and security defaults | Hot-reloadable (most); `auth_token`, `startup_mode` per server are deferred |
| `config/system_prompts.toml` | System prompt presets | Hot-reloadable |
| `config/mcp_servers.toml` | MCP server transport/URL config | HTTP URL: hot-reloadable; `auth_token`, `startup_mode`: deferred; new servers / transport change: restart-required |
| `config/tools_definitions.toml` | MCP tool name definitions | Hot-reloadable |

**Classification definitions:**

- **Hot-reloadable** — applied immediately to the running agent; no restart needed.
- **Deferred** — stored in `ctx.cfg` on `/reload`, but takes effect only on the
  next connection or subprocess restart. The running MCP connector won't see the
  new value until it reconnects. `/reload` output shows these as `[DEFER]`.
- **Restart-required** — the subsystem must be restarted for the change to apply.
  `/reload` output shows these as `[RESTART]`.
- **Startup-only** — read once at agent start; never touched by `/reload`.
  `/reload` emits `[STARTUP-ONLY]` only when the field value differs from the
  running config.

**Deferred settings** (`deferred` in `ConfigReloadOutcome`):
- `auth_token` per MCP server (stored in cfg; takes effect on next connection)
- `startup_mode` per MCP server (stored in cfg; takes effect on next subprocess start)

**Restart-required settings** (`needs_restart` in `ConfigReloadOutcome`):
- MCP server transport type changes (`stdio` ↔ `http`)
- New MCP servers added to `mcp_servers.toml`

**Startup-only settings** (not touched by `apply_config_dict()`):
- `use_memory_layer` — enables/disables the memory subsystem at boot
- `plugin_strict` — enables fail-fast on plugin import errors at boot

### Role of `common.toml`

`common.toml` owns project-wide infrastructure defaults: LLM endpoint URL (`llm_url`),
RAG defaults (`top_k_search`, `embed_url`), observability endpoint (`otel_endpoint`),
and SQLite paths (`rag_db_path`, `session_db_path`). SQLite path fields are
startup-only (read once by `SQLiteHelper`); the URL fields are hot-reloadable.
Other config files override `common.toml` values at load time.

### Reload execution pipeline

`ConfigReloadService` (`agent/services/config_reload.py`) applies the reloaded
config to live service instances:

| Service | Method called | Config fields propagated |
|---|---|---|
| `LLMClient` | `.apply_config()` | temperature, max_tokens, max_retries, retry_base_delay, SSE params |
| `HistoryManager` | `.apply_config()` | context_char_limit, context_compress_turns, context_token_limit, tokenize_url |
| `ToolExecutor` | `.apply_config()` | tool_cache_ttl |
| System prompt | direct write | system_prompt_tool → `ctx.conv.system_prompt_content` |

**`ConfigReloadOutcome` fields:**

| Field | Type | Description |
|---|---|---|
| `applied` | `list[str]` | Changes applied at runtime (hot-reloaded) |
| `needs_restart` | `list[str]` | Changes that require a full agent restart |
| `deferred` | `list[str]` | Changes stored in cfg but effective only on next connection |
| `skipped` | `list[str]` | Changes skipped (e.g. new MCP server added) |
| `source_files` | `list[str]` | Config files that were reloaded |
| `startup_only` | `list[str]` | Startup-only fields that differ from running config |

See `agent/services/config_reload.py` for the full field-level mapping.

---

## AgentConfig Structure

`AgentConfig` composes 7 domain sub-configs accessed as `cfg.llm.*`, `cfg.rag.*`, etc.,
plus two top-level scalar fields.

```python
@dataclass
class AgentConfig:
    llm:      LLMConfig
    rag:      RAGConfig
    tool:     ToolConfig
    memory:   MemoryConfig
    mcp:      MCPConfig
    approval: ApprovalConfig
    obs:      ObservabilityConfig
    workflow_mode:              str  = "auto"   # "auto" | "required" | "disabled"
    security_lockdown_enabled:  bool = False
```

`workflow_mode` controls workflow invocation behaviour: `"auto"` falls back with a warning when
workflow execution fails, `"required"` raises a hard error, `"disabled"` always uses the direct
LLM path. `security_lockdown_enabled` suppresses DENY-ALL approval warnings for intentional
lockdown deployments.

**Production default:** `config/common.toml` sets `workflow_mode = "required"`. Any environment
that copies `common.toml` (see `deploy.sh:58`) must have a valid workflow definition file
deployed, or the agent will fail at startup. For local/dev environments without `common.toml`
in the config search path, the dataclass default `"auto"` applies (warns and falls back).

Cross-field validation in `_validate_cross_field()`:
- `rag.use_semantic_cache=True` → `rag.embed_url` must be non-empty
- `memory.use_memory_layer=True` → `memory.memory_jsonl_dir` must be non-empty
- `memory.memory_embed_enabled=True` → `rag.embed_url` must be non-empty

---

## LLMConfig (`cfg.llm.*`)

Source: `config/llm.toml` + `config/http.toml` + `config/context.toml`

| Field | Default | Description |
|---|---|---|
| `llm_url` | `""` | LLM endpoint URL |
| `http_timeout` | `30.0` | HTTP timeout (seconds) |
| `llm_max_retries` | `3` | Retry limit for HTTP 429/503/connection errors |
| `llm_retry_base_delay` | `1.0` | Exponential backoff base (seconds) |
| `llm_temperature` | `0.2` | Generation temperature (0.0–2.0) |
| `llm_max_tokens` | `1024` | Max generation tokens |
| `title_llm_temperature` | `0.1` | Session title generation temperature |
| `title_llm_max_tokens` | `20` | Session title max tokens |
| `sse_heartbeat_timeout` | `30.0` | SSE idle timeout (0 = disabled) |
| `sse_malformed_retry` | `2` | Malformed SSE frame tolerance |
| `sse_reconnect_max` | `1` | Max SSE reconnects on retryable error |
| `llm_stream_retry_on_heartbeat_timeout` | `True` | Reconnect on HEARTBEAT_TIMEOUT |
| `llm_stream_retry_on_malformed_chunk` | `False` | Reconnect on MALFORMED_SSE_FRAME |
| `tokenize_url` | `""` | llamacpp `/tokenize` URL; `""` = chars//4 fallback |
| `context_token_limit` | `0` | Token-based compression threshold (0 = disabled) |
| `context_char_limit` | `8000` | Char-based compression threshold |
| `context_compress_turns` | `4` | Oldest N turn pairs to compress per cycle |
| `history_protect_turns` | `2` | Most recent N turn pairs protected from compression |
| `budget_warn_ratio` | `0.8` | Warn when history reaches this fraction of limit |

---

## RAGConfig (`cfg.rag.*`)

Source: `config/rag.toml`

| Field | Default | Description |
|---|---|---|
| `top_k_search` | `10` | Vector/FTS search result count |
| `top_k_rerank` | `15` | Cross-encoder candidate count |
| `max_chunks_per_doc` | `2` | Max chunks per document in results |
| `embed_url` | `http://127.0.0.1:8003/embedding` | Embedding API endpoint |
| `use_semantic_cache` | `False` | Enable semantic cache for RAG results |
| `semantic_cache_threshold` | `0.92` | Cosine similarity threshold for cache hit |
| `semantic_cache_max_size` | `100` | Max cache entries (FIFO eviction; oldest removed first) |
| `use_refiner` | `False` | Compress chunks via LLM after reranking |
| `refiner_max_tokens` | `512` | Refiner LLM max tokens |
| `refiner_timeout` | `30.0` | Refiner LLM timeout (seconds) |
| `refiner_max_chars_per_chunk` | `300` | Max chars per chunk passed to refiner |

---

## ToolConfig (`cfg.tool.*`)

Source: `config/tools.toml` + `config/system_prompts.toml` + `config/tools_definitions.toml`

| Field | Default | Description |
|---|---|---|
| `tool_cache_ttl` | `300.0` | Tool result cache TTL (seconds) |
| `tool_cache_max_size` | `200` | LRU cache size (0 = unlimited) |
| `serial_tool_calls` | `False` | Force sequential tool execution |
| `auto_inject_notes` | `True` | Inject all notes into system prompt at startup |
| `use_tool_summarize` | `False` | Summarize long tool results via LLM |
| `tool_summarize_threshold` | `3000` | Min chars to trigger summarization |
| `tool_definitions_strict` | `False` | `true`: schema mismatch in reachable servers → `RuntimeError` at startup. `false`: mismatch → WARNING only. When ALL servers are unreachable, strict mode skips validation (no abort). See [04_mcp_06 §Startup Validation Behavior](04_mcp_06_configuration_and_operations.md) for full behavior table. |
| `tool_dedup_max_repeats` | `3` | Same (name,args) repeat limit |
| `tool_cycle_detect_window` | `2` | Cycle detection window (rounds; 0=disabled) |
| `tool_error_max_consecutive` | `3` | Consecutive all-error rounds to break loop |
| `tool_error_retry_max` | `1` | Errored (name,args) retry limit |
| `tool_concurrency_limits` | `{}` | Server key → max concurrent calls |
| `masked_fields` | `["file_content"]` | Args keys to mask in console display |
| `plan_blocked_tools` | `[write_file, create_directory, ...]` | Auto-blocked in plan mode |
| `max_tool_turns` | `5` | Max tool call turns per message |
| `tool_result_max_llm_chars` | `8000` | Max tool result chars added to LLM context |
| `tool_results_turn_max_chars` | `50000` | Max total tool result chars per turn |
| `use_tool_dag` | `True` | Dependency-aware scheduling: independent reads run concurrently; writes serialized per resource scope. Disable for strict round-wide serialization legacy behavior. |
| `plugin_strict` | `False` | Raise on first plugin import error (fail-fast for CI/CD) |
| `plugin_tool_override` | `False` | Allow plugin tools to shadow MCP tools when names conflict |

**`use_tool_dag` resource_scope 規約:**

DAG モード (`use_tool_dag = true`) では、`_execute_with_dag()` がツールごとに `ToolSpec` を構築する際に以下のデフォルト値を適用する。

| Tool type | `resource_scope` default | `requires_serial` default | Scheduling bucket |
|---|---|---|---|
| WRITE_TOOLS / DELETE_TOOLS (config に `resource_scope` なし) | `{tool_name}` | `False` | `resource_groups[tool_name]` → concurrent batch |
| `shell_run` (SHELL_TOOLS) | `""` | `True` | serial_barrier (1呼び出しずつ) |
| Read / その他 | `""` | `False` | `parallel` → concurrent batch |

config (`tools_definitions.toml` または `agent.toml`) に `resource_scope` または `requires_serial` を明示した場合はそれが優先される。同一 `resource_scope` を持つ write ツールの複数呼び出しは同一グループ内で `asyncio.gather` により並行実行される。

| `tool_definitions` | `[]` | Tool definitions from `tools_definitions.toml` |
| `system_prompts` | `{}` | System prompt preset dict |
| `allowed_tools` | `[]` | Session tool whitelist (empty = all allowed) |

---

## MemoryConfig (`cfg.memory.*`)

Source: `config/memory.toml`

| Field | Default | Description |
|---|---|---|
| `use_memory_layer` | `False` | Enable persistent semantic memory |
| `memory_jsonl_dir` | `"/opt/llm/memory"` | JSONL source directory |
| `memory_max_inject_semantic` | `5` | Semantic entries injected at session start |
| `memory_max_inject_episodic` | `3` | Episodic entries injected per user prompt |
| `memory_min_importance` | `0.3` | Minimum importance score for injection |
| `memory_embed_enabled` | `False` | Enable embedding + KNN for memory retrieval |
| `memory_embed_dim` | `384` | Embedding dimension (must match vec0 schema) |
| `memory_dedup_threshold` | `0.3` | L2 distance for dedup link detection |
| `memory_max_content_chars` | `500` | Max content chars saved per memory entry |
| `memory_embed_timeout_sec` | `5.0` | Embedding HTTP call timeout |
| `memory_retention_days` | `90` | Retention period (days) |
| `memory_fts_limit` | `50` | FTS5 candidate limit before rescoring |
| `memory_rrf_k` | `60` | RRF fusion constant |
| `memory_recency_days` | `7.0` | Recency boost window (days) |

---

## MCPConfig (`cfg.mcp.*`)

Source: `config/mcp_servers.toml`

| Field | Default | Description |
|---|---|---|
| `mcp_servers` | `{}` | Dict of `McpServerConfig` by server key |
| `mcp_watchdog_interval` | `30.0` (PRODUCTION) / `0.0` (LOCAL) | Watchdog poll interval (seconds; 0=disabled); profile-aware default |
| `mcp_watchdog_max_restarts` | `3` | Max watchdog restart attempts |
| `github_server_url` | `http://127.0.0.1:8006` | GitHub MCP server URL |

See [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md) for `McpServerConfig` fields.

---

## ApprovalConfig (`cfg.approval.*`)

Source: `config/security.toml`

| Field | Default | Description |
|---|---|---|
| `approval_risk_rules` | (see below) | tool → none/medium/high |
| `approval_protected_paths` | `[/opt/, /etc/, /boot/, /usr/, /bin/, /sbin/]` | Escalate to high |
| `approval_high_risk_branches` | `[main, master]` | GitHub branch escalation |
| `approval_shell_safe_prefixes` | `[ls, cat, echo, git log, ...]` | shell_run auto-approve prefixes |
| `approval_resource_keys` | `{path_keys: [...], branch_keys: [...]}` | Arg keys for resource identification |
| `approval_dry_run_tools` | `[write_file, edit_file, delete_file, delete_directory, move_file]` | Pre-execute with dry_run=True |
| `tool_safety_tiers` | `{}` | tool → READ_ONLY/WRITE_SAFE/WRITE_DANGEROUS/ADMIN |
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

## ObservabilityConfig (`cfg.obs.*`)

Source: `config/otel.toml`

| Field | Default | Description |
|---|---|---|
| `otel_enabled` | `False` | Enable OpenTelemetry |
| `otel_endpoint` | `""` | OTLP HTTP endpoint (`""` = ConsoleSpanExporter) |
| `otel_service_name` | `"llm-agent"` | OTel service name |
| `audit_log_file` | `"/opt/llm/logs/audit.log"` | Audit log path (JSON-lines) |
| `structured_log` | `False` | Use JSON-lines format for `agent.log` |
