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
```

**`load(*filenames)`**
- Loads and merges one or more TOML/JSON files in order
- Later files override earlier files
- Keys prefixed with `_` are excluded (documentation metadata)
- Raises `ConfigMissingError` (file not found), `ConfigParseError` (parse error), or `ConfigReadError` (I/O error) — all subclass `ValueError`

**`load_all()`**
- Merges a hardcoded list of 12 files: `common`, `llm`, `http`, `rag`, `context`, `tools`, `memory`, `otel`, `security`, `system_prompts`, `mcp_servers`, `tools_definitions`
- Missing files are silently skipped (catches `ValueError` and continues)
- **`common.toml` IS included** (at index 0, providing baseline infrastructure keys) — see [Config Ownership](#config-ownership) below for full ownership table

---

## 2a. Config Ownership

The following table documents which config files are loaded by `load_all()`, which are loaded separately, and which layer owns each file. This is the canonical reference — do not duplicate this information elsewhere; cross-reference this section instead.

| File | Loaded by `load_all()`? | Loaded Separately By | Owning Layer | Notes |
|---|---|---|---|---|
| `llm.toml` | Yes | — | shared | LLM API settings (temperature, max_tokens, model) |
| `http.toml` | Yes | — | shared | HTTP client settings (timeouts, proxy) |
| `rag.toml` | Yes | — | rag | RAG pipeline settings (chunking strategy, batch size) |
| `context.toml` | Yes | — | agent | Context window and prompt settings |
| `tools.toml` | Yes | — | mcp | Tool configuration (tool_names per server) |
| `memory.toml` | Yes | — | agent/memory | Memory layer settings (embedding enabled, retention) |
| `otel.toml` | Yes | — | shared | OpenTelemetry tracing (enabled, endpoint) |
| `security.toml` | Yes | — | shared | Security policy (tool approval, shell policy) |
| `system_prompts.toml` | Yes | — | agent | System prompt templates |
| `mcp_servers.toml` | Yes | — | mcp | MCP server definitions (transport, cmd, url) |
| `tools_definitions.toml` | Yes | — | mcp | Tool definition metadata |
| `common.toml` | **Yes** | — | shared/db | DB paths, embedding URL, sqlite-vec path, busy_timeout; loaded at index 0 so downstream files can override if needed |

**Ownership rule:** The "Owning Layer" column indicates which layer is primarily responsible for reading and using the config values from each file. A file may be read by multiple layers at runtime, but only one layer owns its semantic meaning.

**`common.toml` loading pattern:** `common.toml` is now part of `load_all()` (added at index 0). Callers no longer need to load it explicitly:
```python
ConfigLoader().load_all()   # now includes common.toml keys: rag_db_path, embed_url, etc.
```
Modules that also need `rag_pipeline.toml` (which is ingester-specific and NOT in `load_all()`) merge both:
```python
{**ConfigLoader().load_all(), **ConfigLoader().load("rag_pipeline.toml")}
```

**Config loading flow:**
```
ConfigLoader().load("agent.toml")
  → read /opt/llm/config/agent.toml (TOML or JSON)
  → remove keys prefixed with "_"
  → return dict  (ValueError on missing or parse error)

ConfigLoader().load_all()
  → iterate hardcoded 12-file list
  → skip missing files silently
  → merge all into single dict
  → return dict  (common.toml IS included at index 0)
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
  → after all loaded: _validate_tool_conflicts() removes conflicting tools from known MCP set
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

- Connection errors fall back silently; `_WarnOnce` instance (`_warned_unavailable`) suppresses repeated warnings per process lifetime
- Category-aware estimation replaces the legacy `chars // 4` heuristic for better accuracy with multilingual text and structured tool payloads
- `_estimate_tokens()` returns `(total_tokens, breakdown: dict[str, int])` with per-category counts

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
  5. _raw_execute(tool_name, args)
       → Semaphore acquire (if concurrency_limits set for server_key)
       → HttpTransport.call() or StdioTransport.call()
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
- Semaphore-based throttling in `_raw_execute()`
- When `execute_all_tool_calls()` detects any side-effect tool, all calls in that round are serialized

**Side-effect detection:**
```python
_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
is_side_effect(tool_name: str) -> bool
```

When `execute_all_tool_calls()` detects any side-effect tool, all calls in that round
are serialized regardless of `serial_tool_calls` setting.

**Routing:** Four-layer cascade — (1) live `/v1/tools` discovery, (2) `ToolRegistry` from `tool_constants.py`, (3) config `tool_names` fallback, (4) static frozenset emergency fallback. See [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md) for full routing details.

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

    async def call(messages, tool_calls=None) -> LLMResponse      # Non-streaming
    async def stream(messages, tool_calls=None) -> AsyncIterator[str]  # Streaming
    def build_payload(messages, tool_calls=None) -> dict         # Payload construction
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
- `McpServerConfig`: per-server transport settings (transport, url, cmd, startup_mode, tool_names, auth_token, etc.)
- `McpServerHealthState`: `HEALTHY` / `DEGRADED` / `UNAVAILABLE`
- `McpServerHealthRegistry`: tracks consecutive failures; `UNAVAILABLE` blocks dispatch

> **Note:** `McpServerConfig.transport` uses `TransportType` enum (not plain `str`). See [90_shared_90 TYPE-01](90_shared_90_inconsistencies_and_known_issues.md).

---

## 12. Execution Flow Summary

**Config loading:**
```
build_agent_config()
  → ConfigLoader().load_all()     [12 files incl. common.toml — see §2a Config Ownership for full table]
```

**Plugin loading:**
```
AgentREPL._init_plugin_registry()
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

## 14. AI Reference Guide

| Question | Answer |
|---|---|
| How to load config files | `ConfigLoader().load("filename.toml")` or `load_all()` |
| Config ownership table | **See §2a Config Ownership** — canonical reference for all 12 TOML files |
| Does `load_all()` include `common.toml`? | **Yes** — included at index 0 of `_BASE_CONFIG_FILES` (see §2a Config Ownership) |
| How to register a plugin tool | `@register_tool("name")` decorator in `plugins/*.py` |
| When does ToolExecutor use cache? | `is_error=False` results only; TTL + LRU |
| Is `git_helper.get_repo_info()` reliable? | Returns `RepoInfoResult`; check `.success` and `.failure_reason` (FailureReason enum) |
| How to get exact token count | `await get_token_count(history, tokenize_url, http)` |
