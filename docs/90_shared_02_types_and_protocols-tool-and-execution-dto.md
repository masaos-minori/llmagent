---
title: "Shared Types and Protocols - Tool and Execution DTOs"
category: shared
tags:
  - shared
  - types
  - tool-dto
  - action-result
  - tool-spec
  - cache
  - events
related:
  - 90_shared_00_document-guide.md
  - 90_shared_02_types_and_protocols-core-types.md
  - 90_shared_02_types_and_protocols-reference.md
source:
  - 90_shared_02_types_and_protocols-core-types.md
---

# Shared Types and Protocols

- Overview → [90_shared_01_overview-purpose-and-scope.md](90_shared_01_overview-purpose-and-scope.md)

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

- Used in DAG scheduling (unconditional) — ToolSpec is constructed for each tool call
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

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_02_types_and_protocols-core-types.md`
- `90_shared_02_types_and_protocols-reference.md`

## Keywords

ToolCallResult
ActionResult
ToolSpec
CacheEntry
PluginFailure
ToolDefinition
ArtifactEvent
ShellPolicy
DbConfig
