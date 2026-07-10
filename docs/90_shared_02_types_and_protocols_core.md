---
title: "Shared Types and Protocols - Core Types"
category: shared
tags:
  - shared
  - type
  - protocol
  - dto
  - llmmessag
  - ragconfig
  - raghit
  - rawhit
  - mergedhit
  - rankedhit
  - llmusage
  - llmresponse
  - toolcallresult
  - transporterrorinfo
  - actionresult
  - artifactevent
  - retryevent
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_overview.md
source:
  - 90_shared_02_types_and_protocols_core.md
---

# Shared Types and Protocols - Core Types

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

## Related Documents

- [90_shared_00_document-guide.md](90_shared_00_document-guide.md)
- [90_shared_01_overview.md](90_shared_01_overview.md)
- [90_shared_02_types_and_protocols_agent.md](90_shared_02_types_and_protocols_agent.md)

## Keywords

type
protocol
dto
llmmessag
ragconfig
raghit
rawhit
mergedhit
rankedhit
llmusage
llmresponse
toolcallresult
transporterrorinfo
actionresult
artifactevent
retryevent
