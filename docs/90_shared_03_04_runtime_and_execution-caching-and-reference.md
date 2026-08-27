# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)

## 14. `LlmRetryHandler` (`shared/llm_retry.py`)

Exponential backoff retry for HTTP POST requests to LLM endpoints. Retries on 429 (rate limit), 503 (service unavailable), and `httpx.RequestError` (connection error). Non-transient HTTP errors (4xx/5xx other than 429/503) are raised immediately. Delay formula: `retry_base_delay * (2**attempt)` where `attempt` starts at 0. The last exception is raised when all retries are exhausted.

---

## 15. `ToolResultCache` / `CacheEntry` (`shared/tool_cache.py`)

A frozen dataclass `CacheEntry` with `output` (str), `is_error` (bool), and `cached_at` (float). A standalone utility for tool results. No longer used by `ToolExecutor` after TTL cache removal (see REQ-002). Key format: `{tool_name}:{json_dumps(args)}` using `shared.json_utils.dumps`. `store_if_success()` stores only results where `is_error=False`.

---

## 16. `ToolSpec` (`shared/tool_spec.py`)

A frozen dataclass for DAG scheduling metadata. Fields include: `call_id` (LLM-assigned tool call id from `tool_calls[].id`), `name` (tool function name), `args` (dict[str, object]), `resource_scopes` (tuple[str, ...] of kind-prefixed resource-scope strings, e.g., `"filesystem:/a/b.txt"`, for conflict detection — resolved per call by `shared/resource_scope.py::resolve_resource_scopes()`), `requires_serial` (forces serialization regardless of parallel mode), and `is_write` (write/delete classification). `agent/tool_runner.py::_execute_with_dag()` builds a call-id-keyed `ToolSpec` for each approved tool call via `RuntimeToolRegistry.tool_spec_for_call()`.

---

## 17. `McpServerHealthState` / `McpServerHealthRegistry` (`shared/mcp_health.py`)

An enum for MCP server health states: `HEALTHY` (normal operation), `DEGRADED` (failing but not yet unavailable), `UNAVAILABLE` (circuit breaker open), `HALF_OPEN` (experimental probe after cooldown), and `UNKNOWN` (unregistered keys return `HEALTHY` default; `UNKNOWN` is never observed in practice).

Per-server health tracking for `ToolExecutor` dispatch gating. Constructor accepts `failure_threshold` (default 3 consecutive failures $\rightarrow$ `UNAVAILABLE`) and `half_open_cooldown_sec` (default 30s). Methods: `record_failure()` transitions `HEALTHY` $\rightarrow$ `DEGRADED` $\rightarrow$ `UNAVAILABLE`; `record_degraded()` records watchdog reachability probes (does not override `UNAVAILABLE`/`HALF_OPEN`); `record_restart_exhausted()` tags degraded reason as `'restart_limit_reached'`; `record_success()` resets state to `HEALTHY` and clears failure counts/degraded reasons; `get_state()` returns current state; `is_unavailable()` handles `UNAVAILABLE` $\rightarrow$ `HALF_OPEN` transition upon cooldown expiry.

**State Transitions:** `HEALTHY` $\rightarrow$ `DEGRADED` on first failure; `DEGRADED` $\rightarrow$ `UNAVAILABLE` on `failure_threshold` consecutive failures (default 3); `UNAVAILABLE` $\rightarrow$ `HALF_OPEN` after `half_open_cooldown_sec` (default 30s, experimental probe); `HALF_OPEN` $\rightarrow$ `UNAVAILABLE` on probe failure (cooldown resets); `HALF_OPEN` $\rightarrow$ `HEALTHY` on probe success; any state $\rightarrow$ `HEALTHY` on successful response.

**Implementation Notes:** `get_state()` returns `HEALTHY` default for unregistered keys (`UNKNOWN` is never observed). `record_degraded()` does not override `UNVAILABLE`/`HALF_OPEN` states (intentional guard against breaking circuit breaker/trial windows). `record_restart_exhausted()` does not change state (assumes `record_failure()` already set `UNAVAILABLE`) but tags the degraded reason. `record_success()` resets `_failure_counts`, `_unavailable_since`, and `_degraded_reasons` (prevents immediate re-`UNAVAILABLE` due to stale counts).

---

## 18. `LlmPayloadHandler` (`shared/llm_payload.py`)

All methods are `@staticmethod`. `build_payload()` takes `history` (list[LLMMessage]), `tool_defs` (list[dict]), `temperature` (float, required), `max_tokens` (int, required), and `stream` (bool, default False) — it returns a payload with `messages`/`tools`/`tool_choice="auto"`/`temperature`/`max_tokens`, and adds `"stream": True` when `stream=True`. `parse_response()` accepts raw parsed JSON dict (not `httpx.Response`), validates `choices`/`message` structure, raises `ValueError` on invalid input, and delegates usage parsing to `LlmSseHelpers.parse_usage()`. `parse_non_stream_response()` is a third method (not in old docs): it decodes bytes via `orjson.loads()`, raises `ValueError` if not a dict, then delegates to `parse_response()`.

The `on_usage` parameter is a `Callable[[int, int], None] | None`, called from `LlmSseHelpers.parse_usage()` as `on_usage(prompt_tokens, completion_tokens)`. The only production caller is `scripts/agent/factory.py`'s `_on_llm_usage`.

---

## 19. `LlmHotConfigHandler` (`shared/llm_hot_config.py`)

Manages hot-reloadable config fields for `LLMClient`. `HOT_CONFIG_FIELDS` is a tuple of `(instance_attr_name, kwarg_name)` pairs covering 9 fields: `temperature`, `max_tokens`, `max_retries`, `retry_base_delay`, `sse_heartbeat_timeout`, `sse_malformed_retry`, `sse_reconnect_max`, `stream_retry_on_heartbeat_timeout`, and `stream_retry_on_malformed_chunk`. `apply_one()` sets a single field via `setattr`. `apply_config()` accepts keyword-only arguments and applies only non-`None` values (partial update; unspecified items remain unchanged).

---

## 20. AI Reference Guide

| Question | Answer |
|---|---|
| How to load configuration files? | `ConfigLoader().load("filename.toml")` or `load_all()` |
| Where is the configuration ownership table? | **See [section 2a Configuration Ownership]** — Official reference for process isolation policies and per-process config files |
| Does `load_all()` include `agent.toml`? | **Yes (it is the only one)** — `_BASE_CONFIG_FILES = ("agent.toml",)` contains only one entry; other configs (`crawler.toml`, etc.) are loaded individually by their respective processes (See [section 2a Configuration Ownership]) |
| When does `ToolExecutor` use its cache? | Removed (see REQ-002). ToolExecutor no longer caches results. |
| Is `git_helper.get_repo_info()` reliable? | Returns `RepoInfoResult`; verify `.success` and `.failure_reason` (FailureReason enum) |
| How to get accurate token counts? | `await get_token_count(history, tokenize_url, http)` |
| How do LLM retries work? | Exponential backoff: `retry_base_delay * (2**attempt)` for 429/503 and connection errors |
| What is the `ToolExecutor` cache key format? | `{tool_name}:{json_dumps(args)}` (using `shared.json_utils.dumps`) |
| What are the health gate state transitions? | HEALTHY $\rightarrow$ DEGRADED $\rightarrow$ UNAVAILABLE $\rightarrow$ HALF_OPEN $\rightarrow$ HEALTHY/UNAVAILABLE (section 17) |
