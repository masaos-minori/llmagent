---
title: "Shared Runtime - Config, Logging, Plugins, Tokens, OTel, Git"
category: shared
tags:
  - shared
  - runtime
  - configloader
  - logger
  - pluginregistry
  - tokencounter
  - otel
  - tracer
  - githelper
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_overview.md
source:
  - 90_shared_03_runtime_and_execution_infra.md
---

# Shared Runtime - Config, Logging, Plugins, Tokens, OTel, Git

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

## Related Documents

- [90_shared_00_document-guide.md](90_shared_00_document-guide.md)
- [90_shared_01_overview.md](90_shared_01_overview.md)
- [90_shared_03_runtime_and_execution_executor.md](90_shared_03_runtime_and_execution_executor.md)
- [90_shared_03_runtime_and_execution_llm.md](90_shared_03_runtime_and_execution_llm.md)
- [90_shared_03_runtime_and_execution_other.md](90_shared_03_runtime_and_execution_other.md)

## Keywords

runtime
configloader
logger
pluginregistry
tokencounter
otel
tracer
githelper
