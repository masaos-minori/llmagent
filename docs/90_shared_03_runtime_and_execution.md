# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)

## 1. Purpose

Documents the runtime infrastructure and utilities in `shared/`: config loading, logging,
plugin registry, token counting, OTel tracing, git helper, formatters, ToolExecutor,
and McpServerConfig.

---

## 2. `ConfigLoader` (`shared/config_loader.py`)

```python
class ConfigLoader:
    def __init__(self, config_dir: Path | None = None)
    def load(self, *filenames: str) -> dict[str, Any]
    def load_all(self) -> dict[str, Any]

    @classmethod
    def restrict_to(cls, *filenames: str) -> None
```

**`load(*filenames)`**
- Loads and merges one or more TOML/JSON files in order
- Later files override earlier files
- Keys prefixed with `_` are excluded (documentation metadata)
- Raises `ConfigMissingError` (file not found), `ConfigParseError` (parse error), or `ConfigReadError` (I/O error) — all subclass `ValueError`
- If `restrict_to()` has been called, raises `ConfigPermissionError` when a filename is not in the allowed set

**`load_all()`**
- Loads only `agent.toml` (`_BASE_CONFIG_FILES = ("agent.toml",)`)
- Missing files are silently skipped (catches `ConfigMissingError` and continues)
- If `restrict_to()` has been called, raises `ConfigPermissionError` when `agent.toml` is not in the allowed set

**`restrict_to(*filenames)`** (class method)
- Call once at process startup to declare the only config files this process is permitted to load
- Any subsequent `load()` or `load_all()` call that touches a file outside this set raises `ConfigPermissionError`
- Not called by the agent process (unrestricted); called by MCP servers, crawler, ingester, chunk_splitter
- Tests do not call `restrict_to()`, so test processes are unrestricted

---

## 2a. プロセス分離方針 (Config Isolation Policy)

**各プロセスは自身の設定ファイルのみを読み込む。**

エージェント / 各 MCP サーバー / crawler / ingester / chunk_splitter はそれぞれ独立したプロセスとして動作する。設定ファイルは以下のルールに従う:

- 各プロセスは起動時に自身に対応する設定ファイル 1 つだけを `ConfigLoader().load("xxx.toml")` で読み込む
- 他プロセスの設定ファイルは読み込まない (`agent.toml` を含む)
- DB パス・外部サービス URL など複数プロセスが必要とする値は **共通ファイルを作らず、各プロセスの設定ファイルにそれぞれ記述する**
- `ConfigLoader.restrict_to(own_config_file)` をプロセス起動直後に呼ぶことでこのルールをランタイムでも強制する — 違反時は `ConfigPermissionError` が発生する

| プロセス | 設定ファイル | `restrict_to()` 呼び出し箇所 |
|---|---|---|
| agent | `config/agent.toml` | 呼ばない (制限なし) |
| rag-pipeline-mcp | `config/rag_pipeline_mcp_server.toml` | `MCPServer.run_http()` |
| cicd-mcp | `config/cicd_mcp_server.toml` | `MCPServer.run_http()` |
| file-delete-mcp | `config/file_delete_mcp_server.toml` | `MCPServer.run_http()` |
| file-read-mcp | `config/file_read_mcp_server.toml` | `MCPServer.run_http()` |
| file-write-mcp | `config/file_write_mcp_server.toml` | `MCPServer.run_http()` |
| git-mcp | `config/git_mcp_server.toml` | `MCPServer.run_http()` |
| github-mcp | `config/github_mcp_server.toml` | `MCPServer.run_http()` |
| mdq-mcp | `config/mdq_mcp_server.toml` | `MCPServer.run_http()` |
| shell-mcp | `config/shell_mcp_server.toml` | `MCPServer.run_http()` |
| web-search-mcp | `config/web_search_mcp_server.toml` | `MCPServer.run_http()` |
| crawler | `config/crawler.toml` | `if __name__ == "__main__"` |
| ingester | `config/ingester.toml` | `if __name__ == "__main__"` |
| chunk_splitter | `config/chunk_splitter.toml` | `if __name__ == "__main__"` |
| eventbus | `config/eventbus.toml` | (独自ローダー) |

**`MCPServer.own_config_file` クラス変数:**
`MCPServer` サブクラスは `own_config_file = "xxx_mcp_server.toml"` を宣言する。`run_http()` がこの値を使って `ConfigLoader.restrict_to(own_config_file)` を uvicorn 起動前に呼び出す。

**Config loading flow:**
```
ConfigLoader().load("agent.toml")
  → read /opt/llm/config/agent.toml (TOML)
  → remove keys prefixed with "_"
  → return dict  (ConfigMissingError on missing, ConfigParseError on parse error)

ConfigLoader().load_all()
  → iterate _BASE_CONFIG_FILES = ("agent.toml",)
  → skip missing files silently
  → merge into single dict
  → return dict

ConfigLoader.restrict_to("crawler.toml")  # called at process startup
ConfigLoader().load("agent.toml")         # → ConfigPermissionError
ConfigLoader().load_all()                 # → ConfigPermissionError (agent.toml not allowed)
```

---

## 3. `Logger` (`shared/logger.py`)

```python
class Logger:
    def __init__(self, name: str, filepath: str, *, structured_log: bool = False)
    def info(self, msg: str, *args, **kwargs) -> None
    def warning(self, msg: str, *args, **kwargs) -> None
    def error(self, msg: str, *args, **kwargs) -> None
    def set_context(self, **kwargs) -> None
    def clear_context(self) -> None
```

- Configures `FileHandler` + `StreamHandler` automatically (`propagate=False` prevents duplication)
- `structured_log=True` → JSON Lines format for log file
- Context injection: `set_context(turn_id="T001", session_id=42)` adds fields to all subsequent log lines
- File write errors → WARNING logged via `shared.logger.fallback` logger (visible on stderr), then falls back to StreamHandler only; no exception raised
- Log messages must be in **English only** (no Japanese)

---

## 4. `plugin_registry` (`shared/plugin_registry.py`)

```python
def load_plugins(
    plugin_dir: str | Path,
    *,
    known_tools: frozenset[str] = frozenset(),
    override_policy: str = "reject",
    strict_mode: bool = False,
) -> PluginLoadResult
def register_tool(name: str) -> Callable          # decorator
def get_tool(name: str) -> Callable | None
def register_command(name: str, prefix: bool = False) -> Callable
def get_command(name: str) -> tuple[Callable, bool] | None
def iter_commands() -> dict[str, tuple[Callable, bool]]
def iter_tools() -> dict[str, Callable[..., Any]]
def register_pipeline_stage(when: "post") -> Callable
def get_pipeline_post_stages() -> list[Callable]
async def run_pipeline_stages(hits, query, *, strict=False) -> list[Any]
```

**Plugin loading flow:**
```
plugin_registry.load_plugins(plugin_dir, known_tools=..., override_policy="reject", strict_mode=False)
  → glob plugins/*.py in alphabetical order
  → import each file
  → @register_* decorators run at import time
  → errors: logged as WARNING, plugin skipped (fail-open); strict_mode=True raises on first error
  → after all loaded: tool conflict validation removes conflicting tools from known MCP set
  → missing dir: returns 0 (no error)
```

**Priority:** `@register_tool` handlers are checked by `ToolExecutor.execute()` **before** cache and MCP routing.
`@register_command` handlers are dispatched by `CommandRegistry` **after** built-in commands.

**Return types:**

```python
@dataclass(frozen=True)
class PluginFailure:
    path: str          # plugin .py filename
    error: str         # exception message

@dataclass(frozen=True)
class PluginLoadResult:
    loaded_count: int
    failed: tuple[PluginFailure, ...]
    tool_conflicts_shadowed: int
    tool_conflicts_allowed: int
    command_shadows: int

class PluginLoadError(RuntimeError):
    pass

def get_last_load_result() -> PluginLoadResult | None
```

- `get_last_load_result()` returns the most recent `PluginLoadResult`, or `None` before first load.
- `PluginLoadError` is raised only when `strict_mode=True` and there are failures or MCP conflicts.
- `PluginFailure.error` contains the full exception message from the failed plugin.

**Test isolation:** A reset function clears all registries and must be called
in a `pytest.fixture(autouse=True)` in any test file that registers commands, tools,
or pipeline stages. Non-test code must never call this function.

---

## 5. `token_counter` (`shared/token_counter.py`)

```python
async def get_token_count(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
) -> tuple[int, bool]   # (token_count, is_exact)
```

**Priority:**
1. `POST {tokenize_url}/tokenize` → exact count (`is_exact=True`)
2. Category-aware character-to-token estimate (text: 4.0, tool_calls: 2.5, system: 3.5) → estimate (`is_exact=False`)

- Connection errors fall back silently; a `_WarnOnce` instance suppresses repeated warnings per process lifetime
- Category-aware estimation replaces the legacy `chars // 4` heuristic for better accuracy with multilingual text and structured tool payloads
- Token estimation returns `(total_tokens, breakdown: dict[str, int])` with per-category counts

---

## 6. `otel_tracer` (`shared/otel_tracer.py`)

```python
def build_tracer(
    enabled: bool,
    service_name: str = "llm-agent",
    otlp_endpoint: str = "",
) -> TracerProtocol
```

- `enabled=False` → returns NoOp stub (no OTel initialization)
- `enabled=True`, `otlp_endpoint=""` → `ConsoleSpanExporter` (writes to stdout/log)
- `enabled=True`, `otlp_endpoint` set → OTLP HTTP exporter
- Uses a **private** `TracerProvider` — does not touch the global OTel provider

---

## 7. `git_helper` (`shared/git_helper.py`)

```python
def get_repo_info(path: str = ".") -> RepoInfoResult
# RepoInfoResult(success: bool, data: dict[str, str] | None, failure_reason: FailureReason | None)
# Returns: {"branch": str, "commit": str (8-char), "message": str, "author": str}
# Returns None on any error (GitPython not installed, not a git repo, etc.)
```

- `ImportError` caught separately (when GitPython is not installed)
- Git operations catch `git.exc.GitError`, `OSError`, `AttributeError`, `ValueError` specifically
- The `except Exception` catch-all has been removed; each error type is logged at DEBUG level with its cause

- `"origin"` field is NOT in the return dict
- `"commit"` is `HEAD.hexsha[:8]` (8 characters only)

---

## 8. `formatters` (`shared/formatters.py`)

```python
def truncate(text: str, max_chars: int) -> str
def fmt_kvlog(op: str, **kwargs) -> str   # key=value log string; first param named "op"
def fmt_size(size: int) -> str           # "1.5 KB", "2.3 MB", etc.
def fmt_md_link(text: str, url: str) -> str   # "[text](url)"
MAX_SNIPPET_CHARS: int                   # max chars for snippet display
```

---

## 9. `ToolExecutor` and Surrounding Concepts (`shared/tool_executor.py`)

**Responsibility:** Core tool dispatch engine — resolves tool → server, handles caching, concurrency limits, health gating, and transport communication.

**`ToolCallResult` dataclass (result contract):**
```python
@dataclass
class ToolCallResult:
    output: str          # Tool output string (truncated if > MCP_MAX_RESPONSE_BYTES)
    is_error: bool       # True if the tool call failed
    request_id: str      # X-Request-Id from the MCP server response
    server_key: str      # Server key used for routing (e.g. "file_read", "shell")
```

**Execution flow:**
```
ToolExecutor.execute(tool_name, args) -> ToolCallResult
  1. plugin_registry.get_tool(tool_name) → plugin takes priority
  2. ToolRouteResolver.resolve(tool_name) → server_key
  3. McpServerHealthRegistry.is_unavailable(server_key) → block if UNAVAILABLE
  4. TTL + LRU cache check (is_error=False results only)
  5. Execute tool call (tool_name, args)
       → Semaphore acquire (if concurrency_limits set for server_key)
       → HttpTransport.call()
  6. Cache store (is_error=False only; TTL from config)
  7. Return ToolCallResult
```

**Cache behavior:**
- Only `is_error=False` results are cached
- TTL + LRU eviction (configurable via `tool_cache_ttl_sec`, `tool_cache_maxsize`)
- Cache key: `(tool_name, serialized_args)`
- Side-effect tools bypass cache entirely

**Health gate:**
- `McpServerHealthRegistry.is_unavailable(server_key)` blocks dispatch when UNAVAILABLE
- Consecutive transport failures → DEGRADED → UNAVAILABLE state transitions
- Successful response → resets to HEALTHY

**Concurrency behavior:**
- `concurrency_limits` dict maps server_key → max concurrent calls
- Semaphore-based throttling in the tool execution layer
- When `execute_all_tool_calls()` detects any side-effect tool, all calls in that round are serialized

**Side-effect detection:**
```python
_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
is_side_effect(tool_name: str) -> bool
```

When `execute_all_tool_calls()` detects any side-effect tool, all calls in that round
are serialized regardless of `serial_tool_calls` setting.

**Routing:** Two-layer cascade — (1) live `/v1/tools` discovery, (2) `ToolRegistry` from `tool_constants.py`. Unknown tools fail immediately with `ValueError`. See [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md) for full routing details.

---

## 10. `LLMClient` (`shared/llm_client.py`)

**Responsibility:** HTTP client for LLM API communication with retry logic, SSE streaming, and error handling.

**Main API:**
```python
class LLMClient:
    def __init__(
        http: AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
    )

    async def call(url: str, history: list[LLMMessage], tool_defs: list[dict[str, Any]]) -> LLMResponse      # Non-streaming
    async def stream(url: str, history: list[LLMMessage], tool_defs: list[dict[str, Any]]) -> LLMResponse  # Streaming
    def build_payload(history: list[LLMMessage], tool_defs: list[dict[str, Any]], stream: bool = False) -> dict[str, Any]  # Payload construction
```

**Error behavior:**
- HTTP errors → `LLMTransportError` with `LLMErrorKind` classification
- SSE heartbeat timeout → retry (configurable via `llm_stream_retry_on_heartbeat_timeout`)
- SSE malformed chunk → retry (configurable via `llm_stream_retry_on_malformed_chunk`)
- Max retries exhausted → raises `LLMTransportError`

**Retry:** Exponential backoff starting at `retry_base_delay`, capped at `max_retries`.

**Statistics (instance-level):** `stat_retries`, `stat_reconnects`, `stat_heartbeat_timeouts`, `stat_partial_completions`, `stat_parse_errors`

**Configuration:** `apply_config()` hot-reloads temperature, max_tokens, and other fields from config dict.

**Full details:** See [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md) for streaming protocol details and SSE parser internals.

---

## 11. `McpServerConfig` / `McpServerHealthRegistry`

Both defined in `shared/mcp_config.py`. Full field reference in
[04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration_and_operations.md) and
[05_agent_08_configuration.md](05_agent_08_configuration.md).

**Summary:**
- `McpServerConfig`: per-server transport settings (transport, url, cmd, startup_mode, tool_names, auth_token, etc.) — validated by `__post_init__` (URL scheme, timeout ranges, tool_names uniqueness, env types). The `key` field is set by `_build_single_server()` from the TOML section name and is excluded from `==` comparison.
- `McpServerHealthState`: `HEALTHY` / `DEGRADED` / `UNAVAILABLE`
- `McpServerHealthRegistry`: tracks consecutive failures; `UNAVAILABLE` blocks dispatch; `record_degraded(key, reason)` / `get_degraded_reason(key)` track reachable-but-degraded servers without incrementing failure count

> **Note:** `McpServerConfig.transport` uses `TransportType` enum (not plain `str`).

`build_discovery_map(server_tool_lists)` in `shared/route_resolver.py` now returns `tuple[dict[str, str], dict[str, list[str]]]`: `(route_map, duplicates)` where `duplicates` maps each tool name claimed by more than one server to the full list of claiming server keys.

---

## 12. Execution Flow Summary

**Config loading:**
```
build_agent_config()
  → ConfigLoader().load_all()     [12 files incl. agent.toml — see §2a Config Ownership for full table]
```

**Plugin loading:**
```
Plugin registry initialization
  → plugin_registry.load_plugins(plugin_dir)
  → imports plugins/*.py alphabetically
  → @register_* decorators populate global registry
```

**Tool execution:**
```
ToolExecutor.execute(tool_name, args)
  → plugin priority → health gate → cache → raw MCP call
```

---

## 13. Import Boundaries and Design Notes

- `shared/` must NOT import from `agent/`, `mcp/`, `rag/`, `db/`
- `LLMClient` details are in this document (§10) and [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md)
- `ToolExecutor` details are in this document (§9), [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md), and [05_agent_06_tool-execution-and-approval.md](05_agent_06_tool-execution-and-approval.md)

---

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
