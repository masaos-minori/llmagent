---
title: "Agent Configuration - ToolConfig and MemoryConfig"
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

Documents the structure and constraints of tool and memory configurations.

## Design Intent

### Tool Configuration

#### Safety

- `tool_definitions_strict`: Schema mismatch → `RuntimeError` at startup (recommended for production).
- `routing_drift_strict`: Detects routing drift → `RuntimeError` (aborts startup, recommended for production).
- `plan_blocked_tools`: Tools that are automatically blocked in plan mode.
- `masked_fields`: Argument keys to be masked in console output.

#### Execution Control

- `serial_tool_calls`: Serializes tool execution.
- `max_tool_turns`: Maximum number of tool call turns per message.
- `tool_cycle_detect_window`: Cycle detection window (number of rounds).
- `tool_error_max_consecutive`: Number of consecutive error rounds (termination condition for loops).
- `tool_error_retry_max`: Retry limit for a failed `(name, args)` pair.

#### Context Bloat Prevention

- `tool_result_max_llm_chars`: Maximum characters from tool execution results added to LLM context.
- `tool_results_turn_max_chars`: Cumulative maximum characters from tool execution results added to LLM context within one turn.

#### Caching

- `tool_cache_ttl`: TTL for tool execution result cache (seconds).
- `tool_cache_max_size`: LRU cache size.

#### Parallel Execution

- `tool_concurrency_limits`: Server key → Maximum number of concurrent calls.

`resource_scope_kind`/`resource_scope_keys` convention (used throughout the DAG scheduler by `build_execution_groups()`. When `serial_tool_calls=True`, the conflict graph itself is bypassed via `force_serial`).

Scopes are not defined by default in `config/agent.toml`; they are declared by each MCP server via `/v1/tools`. The `resource_scope_kind`/`resource_scope_keys` (Schema 2.0 contract, mandatory fields) and actual invocation arguments are resolved per call using `shared/resource_scope.py::resolve_resource_scopes()`. The resolution result is passed to `agent/tool_scheduler.py::build_execution_groups()` as `ToolSpec.resource_scopes` (a tuple of strings with `kind` prefix, e.g., `"filesystem:/a/b.txt"`) and grouped into conflict graphs on a per-call-id basis rather than per-tool-name basis.

| Tool type | `resource_scope_kind` (declaration) | `requires_serial` | Scheduling bucket |
|---|---|---|---|
| file WRITE_TOOLS / DELETE_TOOLS (`path` arg; `move_file` uses `source`/`destination`) | `"filesystem"` | `False` | resource-scope conflict group (conflicting calls are grouped into a connected component in the conflict graph) → concurrent batch |
| git write tools (`git_add`/`git_commit`, etc.; `repo_path` arg) | `"git_repo"` | `False` | resource-scope conflict group |
| github write tools (`owner`/`repo` args) | `"github_repo"` | `False` | resource-scope conflict group |
| cicd `trigger_workflow` (`repo`/`workflow`/`ref` args) | `"cicd_workflow"` | `False` | resource-scope conflict group |
| mdq `index_paths`/`refresh_index`, rag `rag_delete_document` | `"mdq_store"` / `"rag_store"` (fixed) | `True` | serial_barrier (`requires_serial` takes precedence over scope) |
| `shell_run` | `"process"` (no scope key) | `True` | serial_barrier |
| Read / other unscoped | `""` | `False` | `parallel` → concurrent batch |

Write tools where the `resource_scope_kind` is declared but the actual scope value cannot be resolved from invocation arguments return `("global:write",)` as a fail-closed fallback (it does NOT fall back to tool name or empty tuple).

#### Other Fields

- `tool_definitions`: List of LLM tool schemas derived from `[[tool_definitions]]`.
- `system_prompts`: Dictionary of system prompt presets.
- `allowed_tools`: Session tool whitelist (empty = all allowed).

### Memory Configuration

#### Activation Modes

Determined by the combination of `use_memory_layer`, `memory_embed_enabled`, and the state of the embedding circuit:

| `use_memory_layer` | `memory_embed_enabled` | Circuit | Mode |
|---|---|---|---|
| `false` | any | any | `disabled` |
| `true` | `false` | any | `fts-only` |
| `true` | `true` | open | `degraded` |
| `true` | `true` | closed | `hybrid` |

#### Injection Parameters

- `memory_max_inject_semantic`: Number of semantic entries injected at session start.
- `memory_max_inject_episodic`: Number of episodic entries injected per user prompt.
- `memory_min_importance`: Minimum importance score required for injection.

#### Embedding Related

- `memory_embed_enabled`: Enables embedding + KNN for memory search.
- `memory_embed_timeout_sec`: Timeout for embedding HTTP calls.
- `memory_local_only`: Rejects non-loopback `embed_url` at startup.

The embedding dimension itself is not a config key — it is a fixed code-level
constant (`scripts/db/store_protocols.py::get_embedding_dims()`), used
identically by `MemoryStore` (`agent/factory.py`) and the RAG pipeline.

#### Search & Filtering

- `memory_fts_limit`: Upper limit of FTS5 candidates before re-ranking.
- `memory_rrf_k`: RRF fusion constant.
- `memory_recency_days`: Window for recency boost (days).
- `memory_retention_days`: Retention period (days).

#### Deduplication

- `memory_dedup_threshold`: L2 distance for deduplication link detection.

#### Content Limits

- `memory_max_content_chars`: Maximum characters stored per memory entry.

## Responsibility Boundary

- **Canonical Source**: `Tool`/`Memory` sections in `config/agent.toml`.
- **Validation**: `agent/services/config_validators.py`.
- **Dataclasses**: `ToolConfig` / `MemoryConfig` in `agent/config_dataclasses.py`.

## Key Constraints

- If `tool_definitions_strict=True`, any reachable server schema mismatch causes startup failure.
- If `routing_drift_strict=True`, routing drift causes startup failure.
- `allowed_tools=[]` (empty) means "all allowed" — explicit confirmation is required to prevent unintended behavior.
- `memory_embed_enabled=True` → `rag.embed_url` must not be empty (see Part 2).

## Operational Notes

- Unknown

## Known Limitations

- Unknown

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_08_01_configuration-loading-agent-config.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`

## Keywords

ToolConfig
MemoryConfig
