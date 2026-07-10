---
title: "Agent Configuration"
category: agent
tags:
  - agent
  - agent
  - configuration
  - config
  - settings
related:
  - 05_agent_00_document-guide.md
---

# Agent Configuration

ol.*`)

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

## MemoryConfig (`cfg.

memory.*`)

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

## MCPConfig (`cfg.mcp

## Related Documents

- `agent`
- `configuration`
- `config`

## Keywords

agent
configuration
config
settings
