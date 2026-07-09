# Shared Types and Protocols

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)

## 1. Purpose

Defines all common types, protocols, DTOs, and constants in `shared/` that are used
across `agent/`, `mcp/`, `rag/`, and `db/` layers.

**Key points:**
- `LLMMessage`, `RagConfig` are in `shared/types.py`
- `LLMUsage`, `LLMResponse` are in `shared/llm_types.py` (separated to allow import without `LLMClient`)
- `ActionResult`, `ArtifactEvent`, `ShellPolicy` are in `shared/action_result.py`, `shared/events.py`, `shared/protocols/shell.py`
- Tool constant frozensets are in `shared/tool_constants.py`

---

## 2. Overall Type Definition Structure

| Type | Kind | File | Layer usage |
|---|---|---|---|
| `LLMMessage` | TypedDict | `shared/types.py` | All layers |
| `RagConfig` | Protocol | `shared/types.py` | `rag/`, `scripts/mcp/rag_pipeline/` |
| `RagHit` / `RawHit` / `MergedHit` / `RankedHit` | dataclass / Union alias | `shared/types.py` | `rag/`, `agent/`, `shared/` |
| `LLMUsage` | frozen dataclass | `shared/llm_types.py` | `agent/`, `shared/` |
| `LLMResponse` | frozen dataclass | `shared/llm_types.py` | `agent/`, `shared/` |
| `ActionResult` | frozen dataclass | `shared/action_result.py` | `agent/` |
| `ArtifactEvent` | TypedDict | `shared/events.py` | `agent/`, `mcp/github/` |
| `ShellPolicy` | dataclass | `shared/protocols/shell.py` | `mcp/shell/` |
| `DbConfig` | dataclass | `db/config.py` | `db/`, `agent/` |
| `CallToolRequest` / `CallToolResponse` | Pydantic models | `mcp/models.py` | `mcp/` only |
| Tool frozensets | `frozenset[str]` | `shared/tool_constants.py` | `shared/`, `agent/`, `mcp/` |
| `ToolCallResult` | frozen dataclass | `shared/transport_dto.py` | `agent/`, `mcp/`, `shared/` |
| `TransportErrorInfo` | frozen dataclass | `shared/transport_dto.py` | `agent/`, `shared/` (audit logs) |
| `ToolSpec` | frozen dataclass | `shared/tool_spec.py` | `agent/` (DAG mode) |
| `CacheEntry` | frozen dataclass | `shared/tool_cache.py` | `shared/` (ToolExecutor cache) |
| `PluginFailure` | frozen dataclass | `shared/plugin_result.py` | `shared/`, `agent/` |
| `PluginLoadResult` | frozen dataclass | `shared/plugin_result.py` | `shared/`, `agent/` |
| `ToolDefinition` | frozen dataclass | `shared/tool_registry.py` | `shared/`, `mcp/` |

---

## 3. `LLMMessage` (`shared/types.py`)

```python
class LLMMessage(TypedDict, total=False):
    role: Literal["user", "assistant", "tool", "system"]  # always required in practice
    content: str | None   # None when message contains only tool_calls
    tool_calls: list[dict]   # assistant role only
    tool_call_id: str        # tool role only
    name: str               # tool role only
    importance: float       # message importance score for compression prioritization
    pinned: bool            # preserve during history compression
```

- `total=False` means all fields are technically optional, but `role` is always required
- Canonical import: `from shared.types import LLMMessage` (used by 20+ modules across agent/, rag/, shared/)

---

## 4. `RagConfig` (`shared/types.py`)

```python
@runtime_checkable
class RagConfig(Protocol):
    semantic_cache_max_size: int
    semantic_cache_threshold: float
    use_mqe: bool
    top_k_search: int
    use_rerank: bool
    rag_top_k: int
    max_chunks_per_doc: int
    top_k_rerank: int
    rag_min_score: float
    use_rrf: bool
    use_search: bool
    rag_service_url: str
    rag_auth_token: str
    use_refiner: bool
    refiner_max_tokens: int
    refiner_max_chars_per_chunk: int
    refiner_timeout: float
    use_semantic_cache: bool
```

- `@runtime_checkable` — `isinstance()` check works
- Used by `RagPipeline` (`scripts/rag/pipeline.py`); consumed by `scripts/mcp/rag_pipeline/service.py`
- `agent/` does NOT use `RagConfig` directly (no in-process RAG pipeline)
- `SimpleNamespace` adapter can satisfy this protocol

---

## 5. `RawHit`, `MergedHit`, `RankedHit`, `RagHit` (`shared/types.py`)

```python
@dataclasses.dataclass
class RawHit:
    """Raw search result from vector or FTS search."""
    chunk_id: int
    content: str
    url: str
    title: str
    distance: float | None = None
    bm25_score: float | None = None

@dataclasses.dataclass
class MergedHit:
    """RawHit after RRF merge; carries aggregated rrf_score."""
    chunk_id: int
    content: str
    url: str
    title: str
    rrf_score: float

@dataclasses.dataclass
class RankedHit:
    """MergedHit after cross-encoder rerank; carries rerank_score."""
    chunk_id: int
    content: str
    url: str
    title: str
    rrf_score: float
    rerank_score: float

RagHit = RawHit | MergedHit | RankedHit
```

- Canonically defined in `shared/types.py`; fields are added incrementally by pipeline stages
- **Canonical import:** `from shared.types import RagHit, RawHit, MergedHit, RankedHit`
- **Compatibility import (backward-compat only):** `from rag.types import RagHit` — re-exported by `scripts/rag/types.py`; prefer `shared.types` for new code
- Used by `rag/`, `agent/`, and `shared/plugin_registry.py`

---

## 6. `LLMUsage` / `LLMResponse` (`shared/llm_types.py`)

```python
@dataclass(frozen=True)
class LLMUsage:
    prompt_tokens: int
    completion_tokens: int

@dataclass(frozen=True)
class LLMResponse:
    message: LLMMessage       # shared/types.py LLMMessage TypedDict
    finish_reason: str | None
    usage: LLMUsage | None = None
```

- Separated from `llm_client.py` so callers can import DTOs without importing `LLMClient`
- Import: `from shared.llm_types import LLMUsage, LLMResponse`

---

## 6a. `ToolCallResult` / `TransportErrorInfo` (`shared/transport_dto.py`)

```python
@dataclass(frozen=True)
class ToolCallResult:
    output: str            # Tool output string (truncated if > MCP_MAX_RESPONSE_BYTES)
    is_error: bool         # True if the tool call failed
    request_id: str        # x-request-id from HTTP transport; "" for plugin/cache
    server_key: str        # server key that handled the call; "" for plugin tools
    error_type: str = ""   # "transport" | "tool" | "" (empty on success)

    @classmethod
    def from_transport(cls, output: str, is_error: bool, request_id: str = "") -> "ToolCallResult"

@dataclass(frozen=True)
class TransportErrorInfo:
    summary: str           # Human-readable error summary
    detail: str            # JSON-encoded dict for audit log
```

- `ToolCallResult` is the canonical result contract for all tool call executions (transport, plugin, cache)
- `TransportErrorInfo` is used for structured error info in audit logs
- Import: `from shared.transport_dto import ToolCallResult, TransportErrorInfo`

---

## 7. `ActionResult` (`shared/action_result.py`)

```python
ActionType = Literal["continue", "call_tool", "retrieve_more_context", "ask_user", "fail", "retry"]

@dataclass(frozen=True)
class ActionResult:
    action: ActionType
    reason: str = ""
    required_context: list[str] = field(default_factory=list)
    payload: dict[str, object] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    confidence: float = 1.0
```

- Generic machine-decision schema for agent action routing
- `frozen=True` — immutable after construction

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

## 8. `ArtifactEvent` / `RetryEvent` (`shared/events.py`)

```python
class ArtifactEvent(TypedDict, total=False):
    """Emitted when a repo artifact is created or updated."""
    event_type: str  # "artifact.updated" | "artifact.created" | "artifact.deleted"
    repo: str        # "owner/repo"
    branch: str      # branch name
    commit: str      # commit SHA or empty
    path: str        # file path or empty (for whole-branch events)
    pr_number: int   # PR number or 0
    session_id: int  # agent session that triggered the event
    timestamp: str   # ISO-8601 UTC

class RetryEvent(TypedDict):
    """Emitted when a workflow stage retry is triggered."""
    event_type: str
    workflow_id: str
    task_id: str
    attempt_number: int
    max_attempts: int
    error_type: str
    backoff_sec: float
    session_id: str
    timestamp: str   # ISO-8601 UTC
```

> **Note:** `ArtifactEvent` is a data definition only. No event bus is implemented.

### Future event envelope (aspirational — not implemented)

These fields are reserved for a future event-bus layer. They are documented
in `shared/events.py` as design direction only. Do not assume they exist on
any current `ArtifactEvent` instance.

| Field | Type | Purpose |
|---|---|---|
| `event_id` | str | UUID v7 — unique identifier per event |
| `source` | str | Emitting module (e.g. `"mcp/github"`) |
| `timestamp` | str | ISO-8601 UTC — already present as a field |
| `correlation_id` | str | Trace ID linking related events |

When an event bus is implemented, these fields will be added to `ArtifactEvent`
and populated by the emitter before delivery to subscribers.

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
