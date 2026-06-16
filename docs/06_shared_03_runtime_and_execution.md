# Shared Runtime and Execution Infrastructure

- Overview → [06_shared_01_overview.md](06_shared_01_overview.md)

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
- Raises `ValueError` on file-not-found or parse error

**`load_all()`**
- Merges a hardcoded list of 11 files: `llm`, `http`, `rag`, `context`, `tools`, `memory`, `otel`, `security`, `system_prompts`, `mcp_servers`, `tools_definitions`
- Missing files are silently skipped (catches `ValueError` and continues)
- **`common.toml` is NOT included** — this is a known architectural issue (see [06_shared_90 CONFIG-01](06_shared_90_inconsistencies_and_known_issues.md))

**Config loading flow:**
```
ConfigLoader().load("agent.toml")
  → read /opt/llm/config/agent.toml (TOML or JSON)
  → remove keys prefixed with "_"
  → return dict  (ValueError on missing or parse error)

ConfigLoader().load_all()
  → iterate hardcoded 11-file list
  → skip missing files silently
  → merge all into single dict
  → return dict  (common.toml NOT included)
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
- File write errors → silent fallback (StreamHandler only; no exception raised)
- Log messages must be in **English only** (no Japanese)

---

## 4. `plugin_registry` (`shared/plugin_registry.py`)

```python
def load_plugins(plugin_dir: str | Path) -> int
def register_tool(name: str) -> Callable          # decorator
def get_tool(name: str) -> Callable | None
def register_command(name: str, prefix: bool = False) -> Callable
def get_command(name: str) -> tuple[Callable, bool] | None
def iter_commands() -> dict[str, tuple[Callable, bool]]
def register_pipeline_stage(when: str = "post") -> Callable
def get_pipeline_post_stages() -> list[Callable]
```

**Plugin loading flow:**
```
plugin_registry.load_plugins(plugin_dir)
  → glob plugins/*.py in alphabetical order
  → import each file
  → @register_* decorators run at import time
  → errors: logged as WARNING, plugin skipped (fail-open)
  → missing dir: returns 0 (no error)
```

**Priority:** `@register_tool` handlers are checked by `ToolExecutor.execute()` **before** cache and MCP routing.
`@register_command` handlers are dispatched by `CommandRegistry` **after** built-in commands.

> **Known issue:** `load_plugins()` returns an `int` count but does not provide a machine-readable
> report of which plugins failed and why. See [06_shared_90 PLUGIN-01](06_shared_90_inconsistencies_and_known_issues.md).

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
2. `chars // 4` fallback → estimate (`is_exact=False`)

- Connection errors fall back silently; `_warned_unavailable` module-level flag prevents repeated warnings
- See [06_shared_90 GLOBAL-01](06_shared_90_inconsistencies_and_known_issues.md) for the global state concern

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
def get_repo_info(path: str = ".") -> dict | None
# Returns: {"branch": str, "commit": str (8-char), "message": str, "author": str}
# Returns None on any error (GitPython not installed, not a git repo, etc.)
```

> **Known issue:** Catches `except Exception` broadly and returns `None` without a reason code.
> See [06_shared_90 EXCEPT-01](06_shared_90_inconsistencies_and_known_issues.md).

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

**Note:** `06_spec_shared.md` documents the execution flow. Detailed class API is in
[04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md).
See [06_shared_90 UNDOC-02](06_shared_90_inconsistencies_and_known_issues.md) for undocumented details.

**`ToolCallResult` dataclass:**
```python
@dataclass
class ToolCallResult:
    output: str
    is_error: bool
    request_id: str
    server_key: str
```

**Execution flow:**
```
ToolExecutor.execute(tool_name, args) -> ToolCallResult
  1. plugin_registry.get_tool(tool_name) → plugin takes priority
  2. McpServerHealthRegistry.is_unavailable(server_key) → block if UNAVAILABLE
  3. TTL + LRU cache check (is_error=False results only)
  4. _raw_execute(tool_name, args)
       → Semaphore acquire (if concurrency_limits set)
       → HttpTransport.call() or StdioTransport.call()
  5. Cache store (is_error=False only)
  6. Return ToolCallResult
```

**Side-effect detection:**
```python
_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
is_side_effect(tool_name: str) -> bool
```

When `execute_all_tool_calls()` detects any side-effect tool, all calls in that round
are serialized regardless of `serial_tool_calls` setting.

---

## 10. `McpServerConfig` / `McpServerHealthRegistry`

Both defined in `shared/mcp_config.py`. Full field reference in
[04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration_and_operations.md) and
[05_agent_08_configuration.md](05_agent_08_configuration.md).

**Summary:**
- `McpServerConfig`: per-server transport settings (transport, url, cmd, startup_mode, tool_names, auth_token, etc.)
- `McpServerHealthState`: `HEALTHY` / `DEGRADED` / `UNAVAILABLE`
- `McpServerHealthRegistry`: tracks consecutive failures; `UNAVAILABLE` blocks dispatch

> **Known issue:** `McpServerConfig.transport` is typed as `str` rather than `Literal["http", "stdio"]`.
> See [06_shared_90 TYPE-01](06_shared_90_inconsistencies_and_known_issues.md).

---

## 11. Execution Flow Summary

**Config loading:**
```
build_agent_config()
  → ConfigLoader().load_all()     [11 files; common.toml excluded]
  → ConfigLoader().load("common.toml")   [loaded separately by db/ and rag/]
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

## 12. Import Boundaries and Design Notes

- `shared/` must NOT import from `agent/`, `mcp/`, `rag/`, `db/`
- `LLMClient` (`shared/llm_client.py`) is undocumented in current specs — see [06_shared_90 UNDOC-01](06_shared_90_inconsistencies_and_known_issues.md)
- `ToolExecutor` details beyond this document are covered in `04_mcp_03` and `05_agent_06`

---

## 13. AI Reference Guide

| Question | Answer |
|---|---|
| How to load config files | `ConfigLoader().load("filename.toml")` or `load_all()` |
| Does `load_all()` include `common.toml`? | **No** — loaded separately |
| How to register a plugin tool | `@register_tool("name")` decorator in `plugins/*.py` |
| When does ToolExecutor use cache? | `is_error=False` results only; TTL + LRU |
| Is `git_helper.get_repo_info()` reliable? | Returns `None` on any exception; no error reason |
| How to get exact token count | `await get_token_count(history, tokenize_url, http)` |
