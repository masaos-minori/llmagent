---
title: "Shared Runtime and Execution Infrastructure — Tool Executor and Infrastructure"
area: shared
tags:
  - shared
  - tool-executor
  - infrastructure
related:
  - shared_03_03_runtime_and_execution-llm-and-mcp-clients.md
  - shared_03_04_runtime_and_execution-caching-and-reference.md
  - shared_00_document-guide.md
---
# Shared Runtime and Execution Infrastructure

- Overview → [shared_00_document-guide.md](shared_00_document-guide.md)

## 4. `ToolExecutor` (`shared/tool_executor.py`, `shared/tool_executor_helpers.py`)

`ToolExecutor` inherits from `ToolTransportInvoker`; `apply_config()` enables hot-reloading. Execution follows this sequence: concurrency protection → health check gate → transport resolution → per-server semaphore execution.

Parallel/serial determination for tool call batches is delegated to `agent/tool_scheduler.py::build_execution_groups()`, which references the `is_write` flag registered in `RuntimeToolRegistry` (see [shared_03_03](shared_03_03_runtime_and_execution-llm-and-mcp-clients.md)). `tool_hash_key()` returns an MD5 hash used for failure tracking, not as a cache key.

---

## 4a. `ToolRegistry` / `route_resolver` / `tool_routing_validation` (Tool Ownership and Routing)

**Separation of Concerns:**
- `shared/runtime_tool_registry.py`: **Routing Authority** (the sole source of truth). Constructed via `McpToolDiscoveryService` through live `/v1/tools` discovery and connected via `ToolExecutor.set_runtime_registry()`.
- `shared/tool_registry.py`: **Input for Drift Detection** (not used for routing). Populated at import time by `frozenset` groups from `tool_constants.py`.
- `shared/route_resolver.py`: `ToolRouteResolver` — resolves `tool_name` → `server_key`. **Refers exclusively to `RuntimeToolRegistry` for resolution; unknown tool names result in an immediate `ValueError`.**
- `shared/tool_routing_validation.py`: Validates consistency between configuration, live `/v1/tools` responses, and the registry (dedicated to drift detection; not used for runtime routing).

### `ToolRegistry` (`shared/tool_registry.py`)

`ToolRegistry` registers `ToolDefinition` objects and handles server resolution for tool names, retrieving all tools by server, and validating consistency between config and live tool lists. `get_registry()` returns a global singleton that auto-registers tools from `tool_constants` upon first call.

`ToolDefinition.description` and `input_schema` are currently reserved fields and are unused. The authoritative tool schema for LLMs is the `TOOL_LIST` defined in each server's `tools.py`. Default registration maps the `tool_constants.py` category frozensets to their corresponding `server_key`.

### `ToolRouteResolver` (`shared/route_resolver.py`)

Resolves `tool_name` → `server_key` using `RuntimeToolRegistry` as sole authority; raises `ValueError` for unresolved names.

**Current behavior:**
- `resolve()` consults `runtime_registry` only; when it has no match, `ValueError` is raised (no fallback).

### Validation functions (`shared/tool_routing_validation.py`)

`validate_routing_against_config`/`live`/`all` return an empty dictionary if no drift is detected. `check_tool_safety_tiers`/`check_unknown_tool_safety_tiers` short-circuit when `tool_safety_tiers` is empty or unset (an opt-in feature).

## 4b. `LifecycleProtocol` (`shared/tool_lifecycle.py`)

`LifecycleProtocol` is the minimum protocol (`ensure_ready(server_key)`) for lifecycle managers injected into `ToolExecutor`. Implementations reside on the MCP side (see MCP documentation).

---

## 5. `token_counter` (`shared/token_counter.py`)

Calls `POST {tokenize_url}/tokenize` for exact counts (`is_exact=True`); otherwise, it falls back to category-based character-to-token estimation (per-category ratios defined in the token counter implementation), returning an estimated count (`is_exact=False`). Connection errors fail silently to the fallback.

Category-based estimation improves accuracy for multilingual text and structured tool payloads. Token estimation returns `(total_tokens, breakdown: dict[str, int])` including category-specific counts.

---

## 6. `otel_tracer` (`shared/otel_tracer.py`)

`build_tracer` returns a `NoOp` stub when `enabled=False`; a `ConsoleSpanExporter` when `otlp_endpoint` is empty; or an `OTLP HTTP` exporter when an endpoint is set. It uses a private `TracerProvider` and does not affect the global OTel provider.

---

## 7. `git_helper` (`shared/git_helper.py`)

`get_repo_info` never returns `None` and does not raise for repository errors: on failure it returns `RepoInfoResult(success=False, failure_reason=...)`, with a distinct `failure_reason` per failure class (missing GitPython, invalid repository, permission, git and OS errors).

---

## 8. `formatters` (`shared/formatters.py`)

Small pure text helpers (truncation, key=value log formatting, size and Markdown-link formatting) and the snippet display limit constant. See `shared/formatters.py`.

## Keywords

- shared
- tool-executor
- infrastructure
