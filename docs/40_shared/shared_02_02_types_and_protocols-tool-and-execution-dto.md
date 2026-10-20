---
title: "Shared Types and Protocols - Tool and Execution DTOs"
area: shared
tags:
  - shared
  - types
  - dto
related:
  - shared_02_01_types_and_protocols-core-types.md
  - shared_02_03_types_and_protocols-reference.md
  - shared_00_document-guide.md
  - shared_03_04_runtime_and_execution-caching-and-reference.md
---
# Shared Types and Protocols - Tool and Execution DTOs

- Overview → [shared_00_document-guide.md](shared_00_document-guide.md)

## 6. `LLMUsage` / `LLMResponse` (`shared/llm_types.py`)

`LLMUsage` (token counting) and `LLMResponse` (message, finish reason, usage wrapper). Decoupled from `llm_client.py` so callers can import DTOs without importing the full `LLMClient`.

---

## 6a. `ToolCallResult` / `TransportErrorInfo` (`shared/transport_dto.py`)

`ToolCallResult` is the standard result contract for all tool executions (transport) — includes output/error metadata, transport information, and audit info. The `source` field is `"mcp"` for MCP calls and empty on error paths.

`TransportErrorInfo` is used as structured error information for audit logs.

---

## 7. `ActionResult` (`shared/action_result.py`)

A generic machine-decidable schema (an `ActionType` enum plus a frozen dataclass) for agent action routing.

---

## 7a. `ToolSpec` (`shared/tool_spec.py`)

A frozen dataclass of DAG scheduling metadata: the call identity, arguments, kind-prefixed `resource_scopes` for conflict detection (resolved per call by `shared/resource_scope.py::resolve_resource_scopes()`), `requires_serial` (forces serialization regardless of parallel mode) and an `is_write` classification. `agent/tool_runner.py` builds one per approved tool call; scheduling logic resides in `agent/tool_scheduler.py`.

---

## 7c. `RuntimeTool` (`shared/runtime_tool.py`)

Represents normalized tool execution metadata (routing, LLM schema, scheduler metadata, side-effect detection, safety tier, approval requirement, argument validation relaxation) in a single type. `AgentSafetyTier` is defined locally as `Literal` types within this module to avoid circular imports due to `shared-is-leaf` constraints (not imported from `agent.tool_enums`).

`build_runtime_tool()` applies safe defaults to unspecified annotation fields. `allow_extra_fields` is a per-tool flag read during the preparation phase (before approval) and passed to argument validation.

---

## 7d. `RuntimeToolRegistry` (`shared/runtime_tool_registry.py`)

An in-memory registry holding `{name: RuntimeTool}`. `resolve()` returns `None` for unregistered names, while `get()` raises `KeyError` — designed to distinguish between "registered but missing annotations" and "non-existent in registry".

`apply_policy()` accepts plain mappings and sequences rather than agent-layer types (also due to `shared-is-leaf` constraints).

**MCP Discovery (`McpToolDiscoveryService`) populates the registry with real data, which is then connected via `ToolExecutor.set_runtime_registry()`.**

---

## 7e. `ToolDefinition` (`shared/tool_registry.py`)

Immutable tool definition — each tool belongs to exactly one MCP server.

**Boundary Conditions:** `description` and `input_schema` are reserved fields; they are not set by default registry initialization functions and are not read by any caller. The authoritative tool schema for LLMs is the `TOOL_LIST` from each server's own `tools.py`, not from this `ToolRegistry`.

`ToolRegistry` only handles tool ownership and routing. Live `/v1/tools` responses are used solely for startup drift validation, not for runtime routing decisions.

---

## 8. `ArtifactEvent` / `RetryEvent` (`shared/events.py`)

`ArtifactEvent` describes repository artifact creation/updates.

> **Note:** `ArtifactEvent` is a pure data structure (`TypedDict`). No event bus, subscription mechanism, or delivery system exists. It exists solely as a type annotation. Do not assume that instantiating an `ArtifactEvent` triggers any action.

`RetryEvent` describes retries in the workflow stage.

---

## 9. `ShellPolicy` (`shared/protocols/shell.py`)

An immutable `frozen=True` dataclass — has no dependencies on FastAPI, MCP, or agents (depends only on `shared` → external). Used by `mcp_servers/shell/service.py` (`ShellService`) as its configuration object.

**Failure Intent:** `__post_init__` raises `ValueError` for an unknown `kill_policy` or `sandbox_backend` and for out-of-range timeout, output, memory or grace limits, so an invalid policy cannot be constructed.

Purpose: To decouple shell execution policy from MCP server implementations.

## Keywords

- shared
- types
- dto
