---
title: "Shared Runtime and Execution - Caching and Reference"
category: shared
tags:
  - shared
  - runtime
  - retry-handler
  - tool-cache
  - tool-spec
  - plugin-invoker
  - ai-reference
related:
  - 90_shared_00_document-guide.md
  - 90_shared_03_runtime_and_execution-config-and-logging.md
  - 90_shared_03_runtime_and_execution-plugin-and-tool-runtime.md
  - 90_shared_03_runtime_and_execution-llm-and-mcp-clients.md
source:
  - 90_shared_03_runtime_and_execution-config-and-logging.md
---

# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_overview-purpose-and-scope.md](90_shared_01_overview-purpose-and-scope.md)

## 14. `LlmRetryHandler` (`shared/llm_retry.py`)

```python
class LlmRetryHandler:
    @staticmethod
    async def request_with_retry(
        http: httpx.AsyncClient,
        url: str,
        payload: dict[str, object],
        max_retries: int,
        retry_base_delay: float,
    ) -> httpx.Response
```

- Exponential-backoff retry for LLM HTTP POST requests
- Retries on 429 (rate limit) and 503 (service unavailable), plus `httpx.RequestError` (connection errors)
- Non-transient HTTP errors (4xx, 5xx other than 429/503) are re-raised immediately
- Delay formula: `retry_base_delay * (2**attempt)` where attempt is 0-indexed
- Raises the last exception when all attempts exhausted
- Import: `from shared.llm_retry import LlmRetryHandler`

---

## 15. `ToolResultCache` / `CacheEntry` (`shared/tool_cache.py`)

```python
@dataclass(frozen=True)
class CacheEntry:
    output: str
    is_error: bool
    cached_at: float

class ToolResultCache:
    def __init__(self, ttl: float, max_size: int = 0)
    def make_key(self, tool_name: str, args: dict[str, Any]) -> str
    def get_result(self, key: str) -> ToolCallResult | None
    def store_if_success(self, key: str, result: ToolCallResult) -> None
    def clear(self) -> None
```

- LRU cache for tool call results with TTL expiry and optional max-size eviction
- Only `is_error=False` results are cached (`store_if_success` skips error results)
- Cache key format: `{tool_name}:{json_dumps(args)}` (uses `shared.json_utils.dumps`)
- TTL check: `time.time() - cached_at >= ttl` → evict and return None
- LRU eviction: when `max_size > 0` and cache exceeds limit, `popitem(last=False)` removes oldest entry
- Import: `from shared.tool_cache import ToolResultCache`

---

## 16. `ToolSpec` (`shared/tool_spec.py`)

```python
@dataclass(frozen=True)
class ToolSpec:
    """Execution metadata for a single approved tool call."""
    call_id: str           # LLM-assigned tool call id (from tool_calls[].id)
    name: str              # Tool function name
    args: dict[str, object] = field(default_factory=dict)
    resource_scope: str = ""   # Resource path/branch string for conflict detection
    requires_serial: bool = False  # True when the tool must not run concurrently
    is_write: bool = False       # True when the tool has write/delete side effects
```

- Used in DAG scheduling (unconditional) — the DAG execution layer constructs ToolSpec for each tool call
- `resource_scope` enables conflict detection between parallel tool calls on the same resource
- `requires_serial` forces serialization even in parallel execution mode
- `is_write` is used by `is_side_effect()` to classify write/delete tools
- Import: `from shared.tool_spec import ToolSpec`

---

## 17. `PluginToolInvoker` (`shared/plugin_tool_invoker.py`)

```python
class PluginToolInvoker:
    async def try_execute(self, tool_name: str, args: dict[str, Any]) -> ToolCallResult | None
```

- Executes plugin tools registered via `plugin_registry.register_tool()`
- Returns `None` if no plugin tool is registered for the given name
- Converts plugin exceptions to `ToolCallResult(is_error=True)` to keep errors local (never propagates)
- Performs defensive runtime validation of return value contract: must be exactly 2-element tuple `(str, bool)`
- Raises `TypeError` if output is not str or is_error is not bool
- Import: `from shared.plugin_tool_invoker import PluginToolInvoker`

---

## 18. `McpServerHealthState` / `McpServerHealthRegistry` (`shared/mcp_health.py`)

```python
class McpServerHealthState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"   # failing but not yet unavailable
    UNAVAILABLE = "unavailable"
    HALF_OPEN = "half_open"

class McpServerHealthRegistry:
    def __init__(self, failure_threshold: int = 3, half_open_cooldown_sec: float = 30.0)
    def record_failure(self, server_key: str) -> McpServerHealthState
    def record_success(self, server_key: str) -> None
    def get_state(self, server_key: str) -> McpServerHealthState
    def is_unavailable(self, server_key: str) -> bool
```

- Tracks per-server health states for ToolExecutor dispatch gating
- State transitions:
  - HEALTHY → DEGRADED (first failure)
  - DEGRADED → UNAVAILABLE (failure_threshold consecutive failures, default 3)
  - UNAVAILABLE → HALF_OPEN (after half_open_cooldown_sec, default 30s, trial probe)
  - HALF_OPEN → UNAVAILABLE (failure during trial probe, cooldown resets)
  - HALF_OPEN → HEALTHY (success during trial probe)
  - Any state → HEALTHY (successful response resets everything)
- `is_unavailable()` also handles the UNAVAILABLE → HALF_OPEN transition on cooldown expiry
- Import: `from shared.mcp_health import McpServerHealthState, McpServerHealthRegistry`

---

## 19. `LlmPayloadHandler` (`shared/llm_payload.py`)

```python
class LlmPayloadHandler:
    def build_payload(self, history: list[LLMMessage], tool_defs: list[dict[str, Any]], stream: bool = False) -> dict[str, Any]
    def parse_response(self, response: httpx.Response) -> LLMResponse
```

- Builds LLM request payloads from history + tool definitions
- Parses HTTP responses into LLMResponse DTOs
- Import: `from shared.llm_payload import LlmPayloadHandler`

---

## 20. `LlmHotConfigHandler` (`shared/llm_hot_config.py`)

```python
class LlmHotConfigHandler:
    """Hot-reloadable config fields for LLMClient."""
```

- Manages hot-reloadable configuration fields for LLMClient (temperature, max_tokens, etc.)
- Import: `from shared.llm_hot_config import LlmHotConfigHandler`

---

## 21. AI Reference Guide

| Question | Answer |
|---|---|
| How to load config files | `ConfigLoader().load("filename.toml")` or `load_all()` |
| Config ownership table | **See §2a Config Ownership** — canonical reference for all 12 TOML files |
| Does `load_all()` include `agent.toml`? | **Yes** — included at index 0 of `_BASE_CONFIG_FILES` (see §2a Config Ownership) |
| How to register a plugin tool | `@register_tool("name")` decorator in `plugins/*.py` |
| When does ToolExecutor use cache? | `is_error=False` results only; TTL + LRU |
| Is `git_helper.get_repo_info()` reliable? | Returns `RepoInfoResult`; check `.success` and `.failure_reason` (FailureReason enum) |
| How to get exact token count | `await get_token_count(history, tokenize_url, http)` |
| How does LLM retry work? | Exponential backoff: `retry_base_delay * (2**attempt)` on 429/503 + connection errors |
| ToolExecutor cache key format? | `{tool_name}:{json_dumps(args)}` (uses `shared.json_utils.dumps`) |
| Health gate state transitions? | HEALTHY → DEGRADED → UNAVAILABLE → HALF_OPEN → HEALTHY/UNAVAILABLE (see §18) |

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_03_runtime_and_execution-config-and-logging.md`
- `90_shared_03_runtime_and_execution-plugin-and-tool-runtime.md`
- `90_shared_03_runtime_and_execution-llm-and-mcp-clients.md`

## Keywords

LlmRetryHandler
ToolResultCache
CacheEntry
ToolSpec
PluginToolInvoker
McpServerHealthState
LlmPayloadHandler
LlmHotConfigHandler
