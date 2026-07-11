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
  - 90_shared_02_01_types_and_protocols-core-types.md
  - 90_shared_02_03_types_and_protocols-reference.md
source:
  - 90_shared_02_01_types_and_protocols-core-types.md
---

# 共有の型とプロトコル

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

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

- 呼び出し元が `LLMClient` をインポートせずに DTO をインポートできるよう `llm_client.py` から分離されている
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

- `ToolCallResult` はすべてのツール呼び出し実行 (transport, plugin, cache) における正規の結果契約である
- `TransportErrorInfo` はオーディットログ用の構造化エラー情報として使われる
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

- エージェントのアクションルーティング用の汎用的な機械判定スキーマ
- `frozen=True` — 構築後は不変

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

- DAG スケジューリングで使用される (無条件) — ツール呼び出しごとに ToolSpec が構築される
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

- TTL 失効とオプションの最大サイズによるエビクションを備えた、ツール呼び出し結果用の LRU キャッシュ
- `is_error=False` の結果のみがキャッシュされる
- キャッシュキー: `(tool_name, serialized_args via json_utils.dumps)`
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

- `PluginFailure` — 個々のプラグイン読み込み失敗の詳細
- `PluginLoadResult` — `load_plugins()` 呼び出しから集約された結果
- `PluginLoadError` — `strict_mode=True` で失敗または MCP 競合がある場合にのみ発生する
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

- 不変のツール定義 — 1 つのツールは必ず 1 つの MCP サーバーに属する
- インポート時に `tool_constants.py` の frozenset から値が設定される
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

> **Note:** `ArtifactEvent` はデータ定義のみである。イベントバスは実装されていない。

### 将来のイベントエンベロープ (構想段階 — 未実装)

これらのフィールドは将来のイベントバス層のために予約されている。`shared/events.py` に
設計方針としてのみ記載されている。現在の `ArtifactEvent` インスタンスにこれらが
存在すると仮定してはならない。

| Field | Type | Purpose |
|---|---|---|
| `event_id` | str | UUID v7 — イベントごとの一意識別子 |
| `source` | str | 発行元モジュール (例: `"mcp/github"`) |
| `timestamp` | str | ISO-8601 UTC — 既にフィールドとして存在 |
| `correlation_id` | str | 関連イベントを結びつけるトレース ID |

イベントバスが実装された場合、これらのフィールドは `ArtifactEvent` に追加され、
サブスクライバーへの配信前に発行元によって値が設定される。

---

## 9. `ShellPolicy` (`shared/protocols/shell.py`)

- 純粋な `dataclass` — FastAPI、MCP、エージェントへの依存はない
- `mcp/shell/service.py` がその設定オブジェクトとして使用する
- フィールド: `shared/protocols/shell.py` のソースを直接参照
- 目的: シェル実行ポリシーを MCP サーバー実装から分離すること

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_02_01_types_and_protocols-core-types.md`
- `90_shared_02_03_types_and_protocols-reference.md`

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
