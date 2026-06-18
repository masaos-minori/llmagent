# Shared Types and Protocols

- Overview → [06_shared_01_overview.md](06_shared_01_overview.md)

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
| `RagConfig` | Protocol | `shared/types.py` | `rag/`, `mcp/rag_pipeline/` |
| `RagHit` | TypedDict | `rag/types.py` | `rag/`, `agent/` |
| `LLMUsage` | frozen dataclass | `shared/llm_types.py` | `agent/`, `shared/` |
| `LLMResponse` | frozen dataclass | `shared/llm_types.py` | `agent/`, `shared/` |
| `ActionResult` | frozen dataclass | `shared/action_result.py` | `agent/` |
| `ArtifactEvent` | TypedDict | `shared/events.py` | `agent/`, `mcp/github/` |
| `ShellPolicy` | dataclass | `shared/protocols/shell.py` | `mcp/shell/` |
| `DbConfig` | dataclass | `db/config.py` | `db/`, `agent/` |
| `CallToolRequest` / `CallToolResponse` | Pydantic models | `mcp/models.py` | `mcp/` only |
| Tool frozensets | `frozenset[str]` | `shared/tool_constants.py` | `shared/`, `agent/`, `mcp/` |

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
    use_refiner: bool
    refiner_max_tokens: int
    refiner_max_chars_per_chunk: int
    refiner_timeout: float
```

- `@runtime_checkable` — `isinstance()` check works
- Used by `RagPipeline` (`rag/pipeline.py`); consumed by `mcp/rag_pipeline/service.py`
- `agent/` does NOT use `RagConfig` directly (no in-process RAG pipeline)
- `SimpleNamespace` adapter can satisfy this protocol

---

## 5. `RagHit` (`rag/types.py`)

```python
class RagHit(TypedDict, total=False):
    chunk_id: int         # added at vector/fts search stage
    content: str          # chunk body (original text)
    url: str              # source document URL
    title: str            # source document title
    distance: float       # L2 distance (vector_search only; smaller = closer)
    bm25_score: float     # BM25 score (fts_search only; negative; larger abs = higher relevance)
    rrf_score: float      # RRF score (after rrf_merge; larger = higher relevance)
    rerank_score: float   # Cross-Encoder score (after rerank; larger = higher relevance)
```

- Defined in `rag/types.py`, not `shared/`
- Fields are added incrementally by pipeline stages

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

## 8. `ArtifactEvent` (`shared/events.py`)

```python
class ArtifactEvent(TypedDict, total=False):
    event_type: str   # "artifact.updated" | "artifact.created" | "artifact.deleted"
    repo: str         # "owner/repo"
    branch: str
    commit: str       # commit SHA or empty string
    path: str         # file path or empty string
    pr_number: int    # PR number or 0
    session_id: int
    timestamp: str    # ISO-8601 UTC
```

> **Note:** `ArtifactEvent` is a data definition only. No event bus is implemented.
> See [06_shared_90 UNIMPL-01](06_shared_90_inconsistencies_and_known_issues.md).

---

## 9. `ShellPolicy` (`shared/protocols/shell.py`)

- Pure `dataclass` — no FastAPI, MCP, or agent dependencies
- Used by `mcp/shell/service.py` as its configuration object
- Fields: see `shared/protocols/shell.py` source directly
- Purpose: decouple shell execution policy from MCP server implementation

---

## 9. `DbConfig` (`db/config.py`)

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
- Built by `build_db_config()` which reads `common.toml` via `ConfigLoader().load("common.toml")`
- Used by `SQLiteHelper`, `maintenance.py`, and session factory code

---

## 10. Tool Constants (`shared/tool_constants.py`)

All constants are `frozenset[str]`. Used by `ToolRouteResolver` for static fallback routing.

| Constant | Tool names |
|---|---|
| `READ_TOOLS` | `list_directory`, `list_directory_with_sizes`, `directory_tree`, `read_text_file`, `read_media_file`, `read_multiple_files`, `search_files`, `grep_files`, `get_file_info` (9 tools) |
| `WRITE_TOOLS` | `write_file`, `edit_file`, `create_directory`, `move_file` (4 tools) |
| `DELETE_TOOLS` | `delete_file`, `delete_directory` (2 tools) |
| `RAG_TOOLS` | `rag_run_pipeline`, `rag_debug_pipeline` |
| `CICD_TOOLS` | `trigger_workflow`, `get_workflow_runs`, `get_workflow_status`, `get_workflow_logs` |
| `MDQ_TOOLS` | `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs` |
| `GIT_TOOLS` | `git_status`, `git_log`, `git_diff`, `git_branch`, `git_show`, `git_add`, `git_commit`, `git_checkout`, `git_pull`, `git_push` |

Used by `ToolRouteResolver._fallback_route()` in `shared/route_resolver.py`.
Referenced also by `shared/tool_executor.py` and `agent/tool_runner.py`.

**Note:** `query_sqlite` is NOT in any frozenset — must be declared in `McpServerConfig.tool_names`.

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
| `TypedDict` | `LLMMessage`, `ArtifactEvent`, `RagHit` | Mutable dict | No (unless `@runtime_checkable`) | Data transport; duck-typed |
| `Protocol` | `RagConfig` | Depends on impl | Yes (if `@runtime_checkable`) | Structural contract; any object satisfying fields works |
| frozen `dataclass` | `LLMUsage`, `LLMResponse`, `ActionResult` | Immutable | Yes | Value objects; hashable |
| `dataclass` | `ShellPolicy`, `DbConfig` | Mutable | Yes | Configuration objects |
| Pydantic model | `CallToolRequest`, `CallToolResponse` | Mutable | Yes | MCP HTTP request/response validation |

**AI guidance:** When a function accepts `RagConfig`, any object with the required fields
(including `SimpleNamespace`) satisfies the protocol. Do not assume it must be `AgentConfig`.
