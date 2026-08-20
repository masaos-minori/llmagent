# Shared Types and Protocols - Tool and Execution DTOs (Part 1)

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 6. `LLMUsage` / `LLMResponse` (`shared/llm_types.py`)

`LLMUsage` (for token counting: `prompt_tokens`, `completion_tokens`), `LLMResponse` (wraps message, `finish_reason`, usage) — provides token counting + response wrapping. Decoupled from `llm_client.py` so callers can import DTOs without importing the full `LLMClient`. (Explicit in code)

Import: `from shared.llm_types import LLMUsage, LLMResponse`

---

## 6a. `ToolCallResult` / `TransportErrorInfo` (`shared/transport_dto.py`)

`ToolCallResult` is the standard result contract for all tool executions (transport, cache) — includes output/error metadata, transport information, and audit info. The `source` field distinguishes between caller types (`"mcp"`/`"cache"`). (Explicit in code: `scripts/shared/transport_dto.py`)

`TransportErrorInfo` is used as structured error information for audit logs.

Import: `from shared.transport_dto import ToolCallResult, TransportErrorInfo`

---

## 7. `ActionResult` (`shared/action_result.py`)

`ActionType` enum (`continue`/`call_tool`/`retrieve_more_context`/`ask_user`/`fail`/`retry`) and frozen dataclass (`reason`, `required_context`, `payload`, `errors`, `confidence`) — a generic machine-decidable schema for agent action routing. (Explicit in code)

---

## 7a. `ToolSpec` (`shared/tool_spec.py`)

Execution metadata (`call_id`, `name`, `args`, `resource_scopes` (tuple of kind-prefixed scope strings), `requires_serial`, `is_write`) — used for DAG scheduling. `resource_scopes` are resolved per call via `shared/resource_scope.py::resolve_resource_scopes()`. Actual scheduling logic resides in `agent/tool_scheduler.py`. (Explicit in code: `scripts/agent/tool_scheduler.py`)

Import: `from shared.tool_spec import ToolSpec`

---

## 7b. `CacheEntry` / `ToolResultCache` (`shared/tool_cache.py`)

`CacheEntry` (output, is_error, cached_at) — an LRU+TTL cache utility. Currently not used by `ToolExecutor`; kept for potential future reuse without stampede protection. (Explicit in code)

---

## 7c. `RuntimeTool` (`shared/runtime_tool.py`)

Represents normalized tool execution metadata in a single type (15 fields: routing, LLM schema, scheduler metadata, side-effect detection, safety tier, approval requirement, argument validation relaxation flags). `AgentSafetyTier` uses four values (`READ_ONLY`/`WRITE_SAFE`/`WRITE_DANGEROUS`/`ADMIN`) which are defined locally as `Literal` types within this module to avoid circular imports due to `shared-is-leaf` constraints (not imported from `agent.tool_enums`). (Explicit in code)

`build_runtime_tool()` applies safe defaults to unspecified annotation fields. `allow_extra_fields` is a per-tool flag read during the preparation phase by `agent/tool_preparation.py` (`prepare_tool_calls()`/`_prepare_one()`, executed before approval) and passed to `agent/tool_arg_validator.py`'s `validate_tool_arguments()`. (Explicit in code)

**Since the `web_search-mcp` `browser_fetch` tool adopted `config_dependent: True`, `RuntimeTool` / `build_runtime_tool()` is being used with real data for the first time.**

Import: `from shared.runtime_tool import RuntimeTool, build_runtime_tool, AgentSafetyTier`

---

## 7d. `RuntimeToolRegistry` (`shared/runtime_tool_registry.py`)

An in-memory registry holding `{name: RuntimeTool}`. `resolve()` returns `None` for unregistered names, while `get()` raises `KeyError` — designed to distinguish between "registered but missing annotations" and "non-existent in registry". (Explicit in code)

`classify_operation_type()` returns `Literal["read", "write"]` — avoids importing `agent.tool_enums` due to `shared-is-leaf` constraints. (Explicit in code)

`apply_policy()` accepts a plain `tier_map: Mapping[str, AgentSafetyTier]` and `allowed_tools: Sequence[str] = ()` (also due to `shared-is-leaf` constraints). (Explicit in code)

`is_side_effect()` is not a replacement for `shared.tool_executor_helpers.is_side_effect()` (which is based on the `_SIDE_EFFECT_TOOLS` frozenset); instead, it is intentionally implemented in parallel, referencing the registered `RuntimeTool.is_write`. (Explicit in code)

**MCP Discovery (`McpToolDiscoveryService`) populates the registry with real data, which is then connected via `ToolExecutor.set_runtime_registry()`.**

Import: `from shared.runtime_tool_registry import RuntimeToolRegistry`

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_02_01_types_and_protocols-core-types.md`
- `90_shared_02_03_types_and_protocols-reference.md`
- `90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`

---

## 7c. `ToolDefinition` (`shared/tool_registry.py`)

Immutable tool definition — each tool belongs to exactly one MCP server. (Explicit in code: `scripts/shared/tool_registry.py` docstring)

**Boundary Conditions:** `description` and `input_schema` are reserved fields for future use; they are currently not set by default registry initialization functions and are not read by any caller. The authoritative tool schema for LLMs is the `TOOL_LIST` from each server's own `tools.py`, not from this `ToolRegistry`. (Explicit in code)

`ToolRegistry` only handles tool ownership and routing. Live `/v1/tools` responses are used solely for startup drift validation, not for runtime routing decisions. (Explicit in code)

Import: `from shared.tool_registry import ToolDefinition, ToolRegistry, get_registry`

---

## 8. `ArtifactEvent` / `RetryEvent` (`shared/events.py`)

`ArtifactEvent` (event_type, repo, branch, commit, path, pr_number, session_id, timestamp) — issued when repository artifacts are created/updated. (Explicit in code: `scripts/shared/events.py` module docstring)

> **Note:** `ArtifactEvent` is a pure data structure (`TypedDict`). No event bus, subscription mechanism, or delivery system exists. It exists solely as a type annotation for potential future artifact event emission. Do not assume that instantiating an `ArtifactEvent` triggers any action.

`RetryEvent` (event_type, workflow_id, task_id, attempt_number, max_attempts, error_type, backoff_sec, session_id, timestamp) — issued during retries in the workflow stage.

---

## 9. `ShellPolicy` (`shared/protocols/shell.py`)

An immutable `frozen=True` dataclass — has no dependencies on FastAPI, MCP, or agents (depends only on `shared` $\rightarrow$ external). Used by `mcp_servers/shell/service.py` (`ShellService`) as its configuration object. (Explicit in code: `scripts/shared/protocols/shell.py`)

**Failure Intent:** Validates the following in `__post_init__` and raises `ValueError` if violated: `kill_policy` must be one of `{"sigterm_then_sigkill", "sigkill_only"}`, `sandbox_backend` must be one of `{"firejail", "none"}`, `timeout_sec >= 1`, `max_output_kb >= 1`, `max_memory_mb >= 1`, and `kill_grace_sec >= 0`. (Explicit in code: `scripts/shared/protocols/shell.py`)

Purpose: To decouple shell execution policy from MCP server implementations.

Import: `from shared.protocols.shell import ShellPolicy`
