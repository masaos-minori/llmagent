---
title: "Shared Types and Protocols - Core Types"
area: shared
tags:
  - shared
  - types
  - protocols
related:
  - shared_02_02_types_and_protocols-tool-and-execution-dto.md
  - shared_02_03_types_and_protocols-reference.md
  - shared_00_document-guide.md
---
# Shared Types and Protocols - Core Types

- Overview → [shared_00_document-guide.md](shared_00_document-guide.md)

## 1. Purpose

Defines all common types, protocols, DTOs, and constants used across the `agent/`, `mcp_servers/`, `rag/`, and `db/` layers within `shared/`.

**Key Points:**
- Types live in `shared/` so that they can be imported by every layer without importing a heavier module: `LLMUsage`/`LLMResponse` are decoupled from `LLMClient` for this reason.
- `shared/` types do not depend on `agent/`, `mcp_servers/`, `rag/` or `db/` (see the import direction constraints in `shared_01_overview.md`).

---

## 2. Overall Structure of Type Definitions

Common types are grouped by who consumes them:

- Cross-layer message and search types: `LLMMessage`, `RagConfig`, and the hit types (`shared/types.py`); `LLMUsage`/`LLMResponse` (`shared/llm_types.py`).
- Agent action and tool metadata: `ActionResult`, `ToolSpec`, `ToolCallResult`/`TransportErrorInfo`, `ToolDefinition`.
- MCP-server-only types: `CallToolRequest`/`CallToolResponse` live in `mcp_servers/models.py`, not in `shared/`.
- `DbConfig` lives in `db/config.py`, not in `shared/`.

The symbol inventory is the code; this document records only responsibility and boundary decisions.

---

## 3. `LLMMessage` (`shared/types.py`)

A `TypedDict` containing field categories: `role` (required), `content`/`tool_calls` (conditional based on role), `importance`/`pinned` (compression), `_ephemeral`/`_memory_injected` (lifecycle), and `source` (validation). `role` is the only required field; all other fields are optional.

Auxiliary `TypedDict`s for streaming tool call deltas are also defined here.

---

## 4. `RagConfig` (`shared/types.py`)

A structural contract covering search, re-ranking and refinement parameters and service URLs/authentication. Supports `@runtime_checkable` for `isinstance()` checks. Can be satisfied by a `SimpleNamespace` adapter. This is NOT a DTO for configuration files; use `mcp_servers.rag_pipeline.rag_pipeline_models.RagPipelineConfig` (MCP TOML) or `rag.models_config.*` (ingestion TOML) instead. MCP adapters use `build_rag_cfg_adapter()`.

---

## 5. `RawHit`, `MergedHit`, `RankedHit`, `RagHit` (`shared/types.py`)

`RawHit` → `MergedHit` (adds `rrf_score`) → `RankedHit` (adds `rerank_score`, which alone may be `None`) are the canonical hit types, with fields added incrementally at each pipeline stage; later stages retain the earlier stages' score fields.

**Import:** `from shared.types import RagHit, RawHit, MergedHit, RankedHit`. Do NOT re-export these names from `scripts/rag/types.py`; always import directly from `shared.types`.

---

## Keywords

- shared
- types
- protocols
