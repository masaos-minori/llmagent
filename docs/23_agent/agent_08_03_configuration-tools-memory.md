---
title: "Agent Configuration - ToolConfig and MemoryConfig"
area: agent
tags:
  - agent
  - configuration
related:
  - agent_00_document-guide.md
  - agent_08_01_configuration-loading-agent-config.md
  - agent_08_02_configuration-llm-rag.md
  - agent_08_04_configuration-mcp-approval-obs.md
  - agent_10_01_operations-and-observability-startup-and-health.md
---

# Agent Configuration

- Operations → [agent_10_01_operations-and-observability-startup-and-health.md](agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

Documents the structure and constraints of tool and memory configurations.

## Design Intent

### Tool Configuration

#### Safety

- `tool_definitions_strict`: a schema mismatch aborts startup with `RuntimeError`. Required to be `true` in production: `ProductionConfigValidator` treats an absent or `false` value as an error.
- `routing_drift_strict`: detected routing drift aborts startup with `RuntimeError`. Required to be `true` in production, like `tool_definitions_strict`.
- `plan_blocked_tools` blocks additional tools in plan mode, on top of every tool outside the `READ_ONLY` safety tier.
- `masked_fields` lists argument keys masked in console output.
- `allowed_tools` is the session tool whitelist; an empty value means "all allowed" at runtime and is rejected by the production validator.

#### Execution Control and Context Bloat

Loop limits (`max_tool_turns`, cycle-detection window, consecutive-error and per-`(name, args)` retry limits) and context-bloat caps (`tool_result_max_llm_chars` per result, `tool_results_turn_max_chars` per turn) are plain bounds defined by `ToolConfig`. `serial_tool_calls = true` serializes all tool execution and bypasses the conflict graph (`force_serial`).

#### Parallel Execution

`tool_concurrency_limits` maps a server key to its maximum concurrent calls. A `0` (or negative) value means "unlimited": no per-server semaphore is created, the same as the unconfigured default.

Scopes are not defined in `config/agent.toml`; each MCP server declares `resource_scope_kind`/`resource_scope_keys` (Schema 2.0 contract, mandatory fields) via `/v1/tools`, and the scope is resolved per call from the actual invocation arguments (Explicit in code — `shared/resource_scope.py::resolve_resource_scopes()`, `agent/tool_scheduler.py::build_execution_groups()`). Conflict grouping is per call id, not per tool name. Scheduling classes:

- Write tools with a resolvable scope (filesystem, git repo, GitHub repo, CI/CD workflow): calls whose scopes conflict are grouped into one connected component and run in order; non-conflicting groups run as a concurrent batch.
- Tools with `requires_serial = True` (index/store mutation tools and `shell_run`): serial barrier; `requires_serial` takes precedence over scope.
- Read and other unscoped tools: `parallel`, concurrent batch.

A write tool that declares a scope kind but whose scope value cannot be resolved from the arguments returns `("global:write",)` as a fail-closed fallback; it does NOT fall back to the tool name or an empty tuple. The per-tool declarations are canonical in the MCP documents (see [mcp_03_01](../22_mcp/mcp_03_01_dispatch-and-routing.md)).

### Memory Configuration

#### Activation Modes

Determined by the combination of `use_memory_layer`, `memory_embed_enabled`, and the state of the embedding circuit:

| `use_memory_layer` | `memory_embed_enabled` | Circuit | Mode |
|---|---|---|---|
| `false` | any | any | `disabled` |
| `true` | `false` | any | `fts-only` |
| `true` | `true` | open | `degraded` |
| `true` | `true` | closed | `hybrid` |

#### Embedding, Retention and Limits

- `memory_local_only` rejects a non-loopback `embed_url` at startup.
- `memory_embed_enabled` enables embedding and KNN for memory search (startup-only).
- `memory_retention_days` is only the default for `/memory prune`; memories are never deleted automatically.
- `memory_max_pinned` caps pinned memories.
- `memory_max_content_chars` is a per-entry storage limit.
- The embedding dimension is not a config key: it is a fixed code-level constant (`scripts/db/store_protocols.py::get_embedding_dims()`) used identically by `MemoryStore` and the RAG pipeline.

Injection counts, minimum importance, FTS candidate limit, RRF constant, recency window and the deduplication threshold are plain parameters defined by `MemoryConfig`.

## Responsibility Boundary

- **Canonical Source**: `Tool`/`Memory` sections in `config/agent.toml`.
- **Validation**: `agent/services/config_validators.py`.
- **Schema**: `ToolConfig` / `MemoryConfig` in `agent/config_dataclasses.py`.

## Key Constraints

- Under `tool_definitions_strict=True`, any reachable server schema mismatch causes startup failure; under `routing_drift_strict=True`, routing drift does.
- `allowed_tools=[]` (empty) means "all allowed" at runtime (`check_preflight()` skips the whitelist check); in production `ProductionConfigValidator` records it as a validation error, so an explicit allowlist is required (Explicit in code — `scripts/agent/tool_policy.py`, `scripts/agent/production_config_validator.py`).
- `memory_embed_enabled=True` → `rag.embed_url` must not be empty.

## Keywords

- ToolConfig
- MemoryConfig
