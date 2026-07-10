---
title: "Shared Runtime and Execution - Plugin and Tool Runtime"
category: shared
tags:
  - shared
  - runtime
  - plugin-registry
  - token-counter
  - otel-tracer
  - git-helper
  - tool-executor
related:
  - 90_shared_00_document-guide.md
  - 90_shared_03_runtime_and_execution-config-and-logging.md
  - 90_shared_03_runtime_and_execution-llm-and-mcp-clients.md
  - 90_shared_03_runtime_and_execution-caching-and-reference.md
source:
  - 90_shared_03_runtime_and_execution-config-and-logging.md
---

# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_overview-purpose-and-scope.md](90_shared_01_overview-purpose-and-scope.md)

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

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_03_runtime_and_execution-config-and-logging.md`
- `90_shared_03_runtime_and_execution-llm-and-mcp-clients.md`
- `90_shared_03_runtime_and_execution-caching-and-reference.md`

## Keywords

plugin_registry
token_counter
otel_tracer
git_helper
formatters
ToolExecutor
