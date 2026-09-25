---
title: "Shared Runtime and Execution Infrastructure — Tool Executor and Infrastructure"
area: shared
tags:
  - shared
  - tool-executor
  - infrastructure
related:
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md
  - 90_shared_03_04_runtime_and_execution-caching-and-reference.md
---
# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)

## 4. `ToolExecutor` (`shared/tool_executor.py`, `shared/tool_executor_helpers.py`)

`ToolExecutor` inherits from `ToolTransportInvoker` and accepts an HTTP client, `server_configs`, and optional parameters via its constructor. `apply_config()` enables hot-reloading. The `execute()` method follows this sequence: concurrency protection $\rightarrow$ health check gate $\rightarrow$ transport resolution $\rightarrow$ per-server semaphore execution. `clear_cache()` and `get_error_counters()` manage state. Failures are not cached.

Helper functions: `is_side_effect()` identifies tools belonging to `WRITE_TOOLS`/`DELETE_TOOLS`/`shell_run`/`GIT_WRITE_TOOLS`/`GITHUB_WRITE_TOOLS`/`GITHUB_DANGEROUS_TOOLS` (deprecated — no longer used after TTL cache removal). Parallel/serial determination for tool call batches is delegated by `agent/tool_runner.py::_execute_with_dag()` to `agent/tool_scheduler.py::build_execution_groups()`, which references the `is_write` flag registered in `RuntimeToolRegistry` (via `PreparedToolCall.spec`) — this is a separate path from `is_side_effect()` (see [90_shared_03_03](90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md)). `format_transport_error()` generates `TransportErrorInfo`. `tool_hash_key()` returns an MD5 hash used for failure tracking rather than as a cache key.

---

## 4a. `ToolRegistry` / `route_resolver` / `tool_routing_validation` (Tool Ownership and Routing)

**Separation of Concerns (Explicit in code — module docstring):**
- `shared/runtime_tool_registry.py`: **Routing Authority** (the sole source of truth). Constructed via `McpToolDiscoveryService` through live `/v1/tools` discovery and connected via `ToolExecutor.set_runtime_registry()`.
- `shared/tool_registry.py`: **Input for Drift Detection** (not used for routing). Populated at import time by `frozenset` groups from `tool_constants.py`.
- `shared/route_resolver.py`: `ToolRouteResolver` — resolves `tool_name` $\rightarrow$ `server_key`. **Refers exclusively to `RuntimeToolRegistry` for resolution; unknown tool names result in an immediate `ValueError`.**
- `shared/tool_routing_validation.py`: Validates consistency between configuration, live `/v1/tools` responses, and the registry (dedicated to drift detection; not used for runtime routing).

### `ToolRegistry` (`shared/tool_registry.py`)

`ToolRegistry` registers `ToolDefinition` objects and handles server resolution for tool names, retrieving all tools by server, and validating consistency between config and live tool lists. `get_registry()` returns a global singleton that auto-registers tools from `tool_constants` upon first call.

`ToolDefinition.description` and `input_schema` are currently reserved fields and are unused. The authoritative tool schema for LLMs is the `TOOL_LIST` defined in each server's `tools.py`. Default registration maps `READ_TOOLS`/`WRITE_TOOLS`/`DELETE_TOOLS`/`RAG_TOOLS`/`CICD_TOOLS`/`MDQ_TOOLS`/`GIT_TOOLS`/`SHELL_TOOLS`/`GITHUB_TOOLS`/`WEB_SEARCH_TOOLS` from `tool_constants.py` to their corresponding `server_key`.

### `ToolRouteResolver` (`shared/route_resolver.py`)

Resolves `tool_name` $\rightarrow$ `server_key` using `RuntimeToolRegistry` as sole authority; raises `ValueError` for unresolved names.

**Current behavior:**
- `runtime_registry` takes priority in `resolve()` when set.

### Validation functions (`shared/tool_routing_validation.py`)

`validate_routing_against_config`/`live`/`all` return an empty dictionary if no drift is detected. `check_tool_safety_tiers`/`check_unknown_tool_safety_tiers` short-circuit when `tool_safety_tiers` is empty or unset (an opt-in feature).

## 4b. `LifecycleProtocol` (`shared/tool_lifecycle.py`)

```python
@runtime_checkable
class LifecycleProtocol(Protocol):
    async def ensure_ready(self, server_key: str) -> None
```
- The minimum protocol for lifecycle managers injected into `ToolExecutor`. Implementations reside in the MCP side (see MCP documentation for details).

---

## 5. `token_counter` (`shared/token_counter.py`)

Calls `POST {tokenize_url}/tokenize` for exact counts (`is_exact=True`); otherwise, it falls back to category-based character-to-token estimation (text: 4.0, tool_calls: 2.5, system: 3.5), returning an estimated count (`is_exact=False`). Connection errors fail silently to the fallback.

Category-based estimation replaces the legacy `chars // 4` heuristic, improving accuracy for multilingual text and structured tool payloads. Token estimation returns `(total_tokens, breakdown: dict[str, int])` including category-specific counts.

---

## 6. `otel_tracer` (`shared/otel_tracer.py`)

`build_tracer` returns a `NoOp` stub when `enabled=False`; a `ConsoleSpanExporter` when `otlp_endpoint` is empty; or an `OTLP HTTP` exporter when an endpoint is set. It uses a private `TracerProvider` and does not affect the global OTel provider.

---

## 7. `git_helper` (`shared/git_helper.py`)

`get_repo_info` returns `RepoInfoResult(success, data dict with branch/commit(8-char)/message/author, failure_reason)`. Returns `None` on any error. `ImportError` is caught separately; `GitPython`/`GitError`/`OSError`/`AttributeError` are caught individually and raised as `ValueError`.

---

## 8. `formatters` (`shared/formatters.py`)

`truncate(text, max_chars)` truncates text; `fmt_kvlog(op, **kwargs)` formats key=value log strings; `fmt_size(size)` formats human-readable sizes; `fmt_md_link(text, url)` formats Markdown links; `MAX_SNIPPET_CHARS` is a constant for snippet display limits.
