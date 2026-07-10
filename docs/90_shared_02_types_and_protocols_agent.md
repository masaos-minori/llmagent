---
title: "Shared Types and Protocols - Agent and Tool Types"
category: shared
tags:
  - shared
  - type
  - protocol
  - dto
  - shellpolicy
  - dbconfig
  - toolconstants
  - calltoolrequest
  - calltoolresponse
  - protocolsdiffer
  - toolspec
  - cacheentry
  - toolresultcache
  - pluginfailure
  - pluginloadresult
  - tooldefinition
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_overview.md
  - 90_shared_02_types_and_protocols_core.md
source:
  - 90_shared_02_types_and_protocols_core.md
---

# Shared Types and Protocols - Agent and Tool Types

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)

---

## 9. `ShellPolicy` (`shared/protocols/shell.py`)

- Pure `dataclass` — no FastAPI, MCP, or agent dependencies
- Used by `mcp/shell/service.py` as its configuration object
- Fields: see `shared/protocols/shell.py` source directly
- Purpose: decouple shell execution policy from MCP server implementation

---

## 9a. `DbConfig` (`db/config.py`)

```python
@dataclass
class DbConfig:
    rag_db_path: str
    session_db_path: str
    workflow_db_path: str = "/opt/llm/db/workflow.sqlite"
    sqlite_vec_so: str = ""       # empty = vec extension not required
    sqlite_timeout: int = 30
    sqlite_busy_timeout_ms: int = 30000
    embedding_dims: int = 384
```

- Validated in `__post_init__`: parent directories must exist; timeout/embedding_dims >= 1
- Built by `build_db_config()` which reads `agent.toml` via `ConfigLoader().load("agent.toml")`
- Used by `SQLiteHelper`, `maintenance.py`, and session factory code

---

## 10. Tool Constants (`shared/tool_constants.py`)

All constants are `frozenset[str]`. Used by `ToolRegistry` for seed data and by `ToolExecutor` for side-effect classification.

| Constant | Tool names |
|---|---|
| `READ_TOOLS` | `list_directory`, `list_directory_with_sizes`, `directory_tree`, `read_text_file`, `read_media_file`, `read_multiple_files`, `search_files`, `grep_files`, `get_file_info` (9 tools) |
| `WRITE_TOOLS` | `write_file`, `edit_file`, `create_directory`, `move_file` (4 tools) |
| `DELETE_TOOLS` | `delete_file`, `delete_directory` (2 tools) |
| `RAG_TOOLS` | `rag_run_pipeline`, `rag_debug_pipeline` |
| `CICD_TOOLS` | `trigger_workflow`, `get_workflow_runs`, `get_workflow_status`, `get_workflow_logs` |
| `MDQ_TOOLS` | `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`, `fts_consistency_check`, `fts_rebuild` (9 tools) |
| `GIT_TOOLS` | `git_status`, `git_log`, `git_diff`, `git_branch`, `git_show`, `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push` |
| `SHELL_TOOLS` | `shell_run` |
| `WEB_SEARCH_TOOLS` | `search_web` |

Referenced also by `shared/tool_executor.py` and `agent/tool_runner.py`.

---

## 11. `CallToolRequest` / `CallToolResponse` Reference

Defined in `mcp/models.py` (NOT in `shared/`):

```python
class CallToolRequest(BaseModel):
    name: str
    args: dict = {}

class CallToolResponse(BaseModel):
    result: str
    is_error: bool
```

These are Pydantic models used only within MCP servers. `shared/` layer code does not
import from `mcp/`. Do not confuse with `ToolCallResult` dataclass in `shared/tool_executor.py`.

---

## 12. How `Protocol`, `TypedDict`, `dataclass`, and DTO Differ

| Kind | Examples | Mutability | `isinstance()` | Usage |
|---|---|---|---|---|
| `TypedDict` | `LLMMessage`, `ArtifactEvent` | Mutable dict | No (unless `@runtime_checkable`) | Data transport; duck-typed |
| `Protocol` | `RagConfig` | Depends on impl | Yes (if `@runtime_checkable`) | Structural contract; any object satisfying fields works |
| frozen `dataclass` | `LLMUsage`, `LLMResponse`, `ActionResult` | Immutable | Yes | Value objects; hashable |
| `dataclass` | `ShellPolicy`, `DbConfig` | Mutable | Yes | Configuration objects |
| Pydantic model | `CallToolRequest`, `CallToolResponse` | Mutable | Yes | MCP HTTP request/response validation |

**AI guidance:** When a function accepts `RagConfig`, any object with the required fields
(including `SimpleNamespace`) satisfies the protocol. Do not assume it must be `AgentConfig`.

---

## 7a. `ToolSpec` (`shared/tool_spec.py`)

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

- Used in DAG mode (`use_tool_dag = true`) — ToolSpec is constructed for each tool call
- Import: `from shared.tool_spec import ToolSpec`

---

## 7b. `CacheEntry` / `ToolResultCache` (`shared/tool_cache.py`)

```python
@dataclass(frozen=True)
class CacheEntry:
    """LRU cache entry storing a successful tool call result."""
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
- Only `is_error=False` results are cached
- Cache key: `(tool_name, serialized_args via json_utils.dumps)`
- Import: `from shared.tool_cache import ToolResultCache`

---

## 7c. `PluginFailure` / `PluginLoadResult` (`shared/plugin_result.py`)

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
    command_shadows_rejected: int

class PluginLoadError(RuntimeError):
    pass
```

- `PluginFailure` — individual plugin load failure detail
- `PluginLoadResult` — aggregated result from `load_plugins()` call
- `PluginLoadError` — raised only when `strict_mode=True` and there are failures or MCP conflicts
- Import: `from shared.plugin_result import PluginFailure, PluginLoadResult, PluginLoadError`

---

## 7d. `ToolDefinition` (`shared/tool_registry.py`)

```python
@dataclass(frozen=True)
class ToolDefinition:
    """Immutable tool definition owned by a single server."""
    name: str
    server_key: str
    description: str = ""
    input_schema: dict[str, object] = field(default_factory=dict)
```

- Immutable tool definition — one tool belongs to exactly one MCP server
- Populated at import time from `tool_constants.py` frozensets
- Import: `from shared.tool_registry import ToolDefinition, ToolRegistry, get_registry`

---

## Related Documents

- [90_shared_00_document-guide.md](90_shared_00_document-guide.md)
- [90_shared_01_overview.md](90_shared_01_overview.md)
- [90_shared_02_types_and_protocols_core.md](90_shared_02_types_and_protocols_core.md)

## Keywords

type
protocol
dto
shellpolicy
dbconfig
toolconstants
calltoolrequest
calltoolresponse
protocolsdiffer
toolspec
cacheentry
toolresultcache
pluginfailure
pluginloadresult
tooldefinition
