---
title: "Shared Types and Protocols - Core Types"
area: shared
tags:
  - shared
  - types
  - protocols
related:
  - 90_shared_02_02_types_and_protocols-tool-and-execution-dto.md
  - 90_shared_02_03_types_and_protocols-reference.md
---
# Shared Types and Protocols - Core Types

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)

## 1. Purpose

Defines all common types, protocols, DTOs, and constants used across the `agent/`, `mcp_servers/`, `rag/`, and `db/` layers within `shared/`.

**Key Points:**
- `LLMMessage` and `RagConfig` are located in `shared/types.py`.
- `LLMUsage` and `LLMResponse` are located in `shared/llm_types.py` (decoupled so they can be imported without importing `LLMClient`).
- `ActionResult`, `ArtifactEvent`, and `ShellPolicy` are located in `shared/action_result.py`, `shared/events.py`, and `shared/protocols/shell.py`, respectively.
- Frozensets for tool constants are located in `shared/tool_constants.py`.

---

## 2. Overall Structure of Type Definitions

List of major common types (refer to code for details):

- `LLMMessage` (TypedDict) — `shared/types.py` — Used by all layers.
- `RagConfig` (Protocol) — `shared/types.py` — Used by `rag/`, `scripts/mcp_servers/rag_pipeline/`.
- `RagHit` / `RawHit` / `MergedHit` / `RankedHit` (dataclass / Union alias) — `shared/types.py` — Used by `rag/`, `agent/`, `shared/`.
- `LLMUsage` / `LLMResponse` (frozen dataclass) — `shared/llm_types.py` — Used by `agent/`, `shared/`.
- `ActionResult` (frozen dataclass) — `shared/action_result.py` — Used by `agent/`.
- `ArtifactEvent` (TypedDict) — `shared/events.py` — Used by `agent/`, `mcp_servers/github/`.
- `ShellPolicy` (dataclass) — `shared/protocols/shell.py` — Used by `mcp_servers/shell/`.
- `DbConfig` (dataclass) — `db/config.py` — Used by `db/`, `agent/`.
- `CallToolRequest` / `CallToolResponse` (Pydantic) — `mcp_servers/models.py` — Dedicated to `mcp_servers/`.
- Tool frozensets — `shared/tool_constants.py` — Used by `shared/`, `agent/`, `mcp_servers/`.
- `ToolCallResult` / `TransportErrorInfo` (frozen dataclass) — `shared/transport_dto.py`.
- `ToolSpec` (frozen dataclass) — `shared/tool_spec.py` — Used by `agent/` (DAG mode).
- `CacheEntry` (frozen dataclass) — `shared/tool_cache.py` — Standalone utility, not currently used anywhere.
- `ToolDefinition` (frozen dataclass) — `shared/tool_registry.py` — Used by `shared/`, `mcp_servers/`.

---

## 3. `LLMMessage` (`shared/types.py`)

A `TypedDict` containing field categories: `role` (required), `content`/`tool_calls` (conditional based on role), `importance`/`pinned` (compression), `_ephemeral`/`_skill_ephemeral`/`_memory_injected` (lifecycle), and `source` (validation). It inherits from `_LLMMessageRequired(TypedDict)` to isolate `role` as a required field. (Explicit in code)

Auxiliary `TypedDict`s for representing tool call deltas during streaming (`ToolCallFunctionDelta`, `ToolCallDelta`, `AccumulatedToolCall`, etc.) are also defined here. (Explicit in code: `scripts/shared/types.py`)

---

## 4. `RagConfig` (`shared/types.py`)

Covers semantic cache settings, search parameters (`top_k_search`, `rag_top_k`), re-ranking parameters (`use_rerank`, `top_k_rerank`, `rag_min_score`, `use_rrf`, `rrf_k`), refinement settings (`max_tokens`, `max_chars_per_chunk`, `timeout`), and service URLs/authentication. Supports `@runtime_checkable` for `isinstance()` checks. Can be satisfied by a `SimpleNamespace` adapter. This is NOT a DTO for configuration files; use `mcp_servers.rag_pipeline.rag_pipeline_models.RagPipelineConfig` (MCP TOML) or `rag.models_config.*` (ingestion TOML) instead. MCP adapters refer to `build_rag_cfg_adapter()`. (Explicit in code)

---

## 5. `RawHit`, `MergedHit`, `RankedHit`, `RagHit` (`shared/types.py`)

`RawHit` (base: `chunk_id`, `content`, `url`, `title`, `distance`, `bm25_score`) $\rightarrow$ `MergedHit` adds `rrf_score` $\rightarrow$ `RankedHit` adds `rerank_score | None`. These are defined as the canonical versions in `shared/types.py`, with fields added incrementally at each stage of the pipeline. (Explicit in code: `scripts/shared/types.py`)

**Implementation Note:** Both `MergedHit` and `RankedHit` retain `distance` and `bm25_score`. All fields have default values except `chunk_id` and `content`. Only `rerank_score` allows `None`.

**Import:** `from shared.types import RagHit, RawHit, MergedHit, RankedHit`. Do NOT re-export these names from `scripts/rag/types.py`; always import directly from `shared.types`.

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`
- `90_shared_02_03_types_and_protocols-reference.md`
