# Agent Configuration

- Operations → [05_agent_10_operations-and-observability.md](05_agent_10_operations-and-observability.md)

## Purpose

Document the complete `AgentConfig` structure, all 7 sub-configs with their fields,
configuration file layout, validation rules, `/reload` scope, and cross-field constraints.

---

## Configuration Loading

`build_agent_config()` (`agent/config_builders.py`) calls `ConfigLoader.load_all()`
(`shared/config_loader.py`) which merges all config files into a dict, then constructs
the `AgentConfig` dataclass.

**Files loaded by `load_all()`:**

| File | Sub-config |
|---|---|
| `config/agent.toml` | All sub-configs (LLMConfig, RAGConfig, DbConfig, ToolConfig, MemoryConfig, ObservabilityConfig, ApprovalConfig, MCPConfig) |

Historical note: Earlier versions loaded 12 separate files (`common.toml`, `llm.toml`, `http.toml`, `context.toml`, `rag.toml`, `tools.toml`, `memory.toml`, `otel.toml`, `security.toml`, `system_prompts.toml`, `tools_definitions.toml`, plus per-server `*_mcp_server.toml`). These were consolidated into `agent.toml`; the split files no longer exist.

For the canonical config ownership table (owning layer per file), see
[90_shared_03 §2a Config Ownership](90_shared_03_runtime_and_execution.md#2a-config-ownership).

`ctx.cfg` holds the config. `/reload` calls `ConfigLoader().load_all()` to
re-read all base config files, then passes the merged dict to
`ConfigReloadService.apply_config_dict(new_cfg)` which updates `ctx.cfg`
fields and syncs live service instances.

The call chain is:
1. `ConfigLoader().load_all()` — re-reads all files from `config/`
2. `ConfigReloadService.apply_config_dict(new_cfg)` — updates `ctx.cfg`
   fields and propagates changes to services
3. `ConfigReloadOutcome` — returned to the caller with `applied`,
   `needs_restart`, `skipped`, and `source_files` fields

### Config file ownership and hot-reload eligibility

`/reload` reads all base config files — the same set loaded at startup.
`ConfigReloadService` classifies each changed key into one of four categories.

All configuration keys are defined in `config/agent.toml`. There is no separate `common.toml` or other split file providing defaults.

| File | Purpose | Classification |
|---|---|---|
| `config/agent.toml` | All sub-configs | Hot-reloadable (most); `use_memory_layer`, `plugin_strict` are startup-only |
| `config/*_mcp_server.toml` | MCP server transport/URL config (via `[mcp_servers.<key>]`) | Restart-required: every field (`transport`, `url`, `startup_mode`, `healthcheck_mode`, `call_timeout_sec`, `startup_timeout_sec`, `tool_names`, `auth_token`, `role`, `cmd`, `env`), plus server add/remove/rename |

**Classification definitions:**

- **Hot-reloadable** — applied immediately to the running agent; no restart needed.
- **Restart-required** — the subsystem must be restarted for the change to apply.
  `/reload` output shows these as `[RESTART]`.
- **Startup-only** — read once at agent start; never touched by `/reload`.
  `/reload` emits `[STARTUP-ONLY]` only when the field value differs from the
  running config.

**Restart-required settings** (`needs_restart` in `ConfigReloadOutcome`):
- Any `McpServerConfig` field change, new servers, removed servers, and
  renames (remove-old + add-new). Example entries:
  `mcp/<server>.url`, `mcp/<server>.auth_token`, `mcp/<server>.startup_mode`,
  `mcp/<server>.cmd`, `mcp/<server>.env`.

**Startup-only settings** (not touched by `apply_config_dict()`):
- `use_memory_layer` — enables/disables the memory subsystem at boot
- `plugin_strict` — enables fail-fast on plugin import errors at boot

**Removed keys** (rejected at config load, `ConfigLoadError`; verified 2026-07-09 — see
`build_agent_config()`'s `_FORBIDDEN_KEYS`): `workflow_mode`, `workflow_require_approval`,
`use_tool_summarize`, `tool_summarize_threshold`. These are no longer valid config keys at
all — not startup-only settings that merely can't be hot-reloaded.

All configuration keys are defined in `config/agent.toml`. There is no separate `common.toml` or other split file providing defaults.

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
| `skipped` | `list[str]` | Changes intentionally ignored, not MCP server definitions — see `needs_restart` |
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
    security_lockdown_enabled:  bool = False
```

`security_lockdown_enabled` suppresses DENY-ALL approval warnings for intentional
lockdown deployments.

**`workflow_mode` and `workflow_require_approval` no longer exist** (verified 2026-07-09
against `scripts/agent/config_dataclasses.py::AgentConfig` — neither field is present).
Both keys are now rejected at config load: `build_agent_config()` raises `ConfigLoadError`
if either appears anywhere in the merged config
(`_FORBIDDEN_KEYS = {"workflow_mode", "workflow_require_approval", "use_tool_summarize",
"tool_summarize_threshold"}`). There is no "auto" / "disabled" degraded mode and no
workflow-level approval-gate toggle — see the next section.

**Current behavior:** the agent unconditionally requires a valid workflow definition.
`StartupOrchestrator._initialize()` calls `_check_workflow_definition()`
(`agent/startup.py:84`, wrapping `check_workflow_definition()` in `agent/repl_health.py`)
as a preflight check **before** `Orchestrator.__init__()`; if
`config/workflows/default.json` is missing, this raises `RuntimeError` with an actionable
message naming the expected path. `Orchestrator.__init__()` itself
(`agent/orchestrator.py:123-129`) then unconditionally calls `WorkflowLoader().load()` and
raises `RuntimeError` on any failure (`WorkflowLoadError` or otherwise) — there is no mode
that skips or degrades this. Neither check is caught by `StartupOrchestrator.run()`; the
failure propagates to the REPL and aborts startup. The failure occurs during agent boot,
not at the first turn. This is startup-only in the sense that it always runs once at boot —
not because it is a config toggle that merely can't be hot-reloaded.

Cross-field validation:
- `rag.use_semantic_cache=True` → `rag.embed_url` must be non-empty
- `memory.use_memory_layer=True` → `memory.memory_jsonl_dir` must be non-empty
- `memory.memory_embed_enabled=True` → `rag.embed_url` must be non-empty

---

## LLMConfig (`cfg.llm.*`)

Source: `config/agent.toml`

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

Source: `config/agent.toml`

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

Source: `config/agent.toml`

| Field | Default | Production Recommended | Description |
|---|---|---|---|
| `tool_cache_ttl` | `300.0` | `300.0` | Tool result cache TTL (seconds) |
| `tool_cache_max_size` | `200` | `200` | LRU cache size (0 = unlimited) |
| `serial_tool_calls` | `False` | `False` | Force sequential tool execution |
| `tool_definitions_strict` | `False` | `True` | `true`: schema mismatch in reachable servers → `RuntimeError` at startup. `false`: mismatch → WARNING only. When ALL servers are unreachable, strict mode skips validation (no abort). See [04_mcp_06 §Startup Validation Behavior](04_mcp_06_configuration_and_operations.md) for full behavior table. |
| `routing_drift_strict` | `False` | `True` | `true`: config/registry routing drift detected at startup → `RuntimeError` (startup aborted). `false`: drift → `[non-fatal]` WARNING only. Startup-only field; requires restart to take effect. |
| `tool_dedup_max_repeats` | `3` | `3` | Same (name,args) repeat limit |
| `tool_cycle_detect_window` | `2` | `2` | Cycle detection window (rounds; 0=disabled) |
| `tool_error_max_consecutive` | `3` | `3` | Consecutive all-error rounds to break loop |
| `tool_error_retry_max` | `1` | `1` | Errored (name,args) retry limit |
| `tool_concurrency_limits` | `{}` | `{}` | Server key → max concurrent calls |
| `masked_fields` | `["file_content"]` | `["file_content"]` | Args keys to mask in console display |
| `plan_blocked_tools` | `[write_file, create_directory, ...]` | `[write_file, create_directory, ...]` | Auto-blocked in plan mode |
| `max_tool_turns` | `5` | `5` | Max tool call turns per message |
| `tool_result_max_llm_chars` | `8000` | `8000` | Max tool result chars added to LLM context |
| `tool_results_turn_max_chars` | `50000` | `50000` | Maximum cumulative tool result characters added to LLM context in a single turn. Protects against excessive per-turn context growth from multiple tool outputs. When exceeded, omitted results are replaced with TURN_LIMIT_HINT. |
| `use_tool_dag` | `True` | `True` | Dependency-aware scheduling: independent reads run concurrently; writes serialized per resource scope. Setting to `false` is legacy (non-production) behavior: all WRITE_TOOLS run before READ_TOOLS within a round, without resource-scoped parallelism. |
| `plugin_strict` | `False` | `True` | Raise on first plugin import error (fail-fast for CI/CD) |
| `plugin_tool_override` | `False` | `False` | Allow plugin tools to shadow MCP tools when names conflict |

**`use_tool_dag` resource_scope 規約:**

DAG モード (`use_tool_dag = true`) では、ツールごとに `ToolSpec` を構築する際に以下のデフォルト値を適用する。

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

Source: `config/agent.toml`

| Field | Default | Description |
|---|---|---|
| `use_memory_layer` | `False` | Enable persistent semantic memory |
| `memory_jsonl_dir` | `"/opt/llm/memory"` | JSONL source directory (canonical key; NOT `memory_jsonl_path`) |
| `memory_max_inject_semantic` | `5` | Semantic entries injected at session start |
| `memory_max_inject_episodic` | `3` | Episodic entries injected per user prompt |
| `memory_min_importance` | `0.3` | Minimum importance score for injection |
| `memory_embed_enabled` | `False` | Enable embedding + KNN for memory retrieval |
| `memory_embed_dim` | `384` | Embedding dimension (must match vec0 schema) |
| `memory_dedup_threshold` | `0.3` | L2 distance for dedup link detection |
| `memory_max_content_chars` | `500` | Max content chars saved per memory entry |
| `memory_embed_timeout_sec` | `5.0` | Embedding HTTP call timeout |
| `memory_retention_days` | `90` | Retention period (days) |
| `memory_local_only` | `False` | Reject non-loopback `embed_url` at startup |
| `memory_fts_limit` | `50` | FTS5 candidate limit before rescoring |
| `memory_rrf_k` | `60` | RRF fusion constant |
| `memory_recency_days` | `7.0` | Recency boost window (days) |

**Activation mode**: set by the combination of `use_memory_layer`, `memory_embed_enabled`, and embedding circuit state:

| `use_memory_layer` | `memory_embed_enabled` | Circuit | Mode |
|---|---|---|---|
| `false` | any | any | `disabled` |
| `true` | `false` | any | `fts-only` |
| `true` | `true` | open | `degraded` |
| `true` | `true` | closed | `hybrid` |

---

## MCPConfig (`cfg.mcp.*`)

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

## ApprovalConfig (`cfg.approval.*`)

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

## ObservabilityConfig (`cfg.obs.*`)

Source: `config/agent.toml`

| Field | Default | Description |
|---|---|---|
| `otel_enabled` | `False` | Enable OpenTelemetry |
| `otel_endpoint` | `""` | OTLP HTTP endpoint (`""` = ConsoleSpanExporter) |
| `otel_service_name` | `"llm-agent"` | OTel service name |
| `audit_log_file` | `"/opt/llm/logs/audit.log"` | Audit log path (JSON-lines) |
| `structured_log` | `False` | Use JSON-lines format for `agent.log` |
