---
title: "Shared Types and Protocols - Tool and Execution DTOs (Part 1)"
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
  - 90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md
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
    source: str = ""       # "mcp" | "plugin" | "" (cache/error paths)
    error_type: str = ""   # "transport" | "tool" | "plugin_contract" | "" (empty on success)

    @classmethod
    def from_transport(cls, output: str, is_error: bool, request_id: str = "") -> "ToolCallResult"

@dataclass(frozen=True)
class TransportErrorInfo:
    summary: str           # Human-readable error summary
    detail: str            # JSON-encoded dict for audit log
```

- `ToolCallResult` はすべてのツール呼び出し実行 (transport, plugin, cache) における正規の結果契約である
- `source` フィールドは呼び出し元がMCPツールかプラグインツールかを区別する。`from_transport()` は常に `source="mcp"` を設定する (Explicit in code: `scripts/shared/transport_dto.py`)
- `error_type` には `"plugin_contract"` も存在する(プラグインの契約違反を表す)。ドキュメント旧版の `"transport" | "tool" | ""` の3値だけではない (Explicit in code)
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
- 実際のスケジューリングロジックは `agent/tool_scheduler.py` にある。`requires_serial=True` のツールは単独のグループとして直列実行され、同一の `resource_scope` かつ `is_write=True` のツール同士も直列化される。`resource_scope` を持たない write ツールは write-first グループにまとめられる (Explicit in code: `scripts/agent/tool_scheduler.py`)
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

### Current behavior — 実運用では未使用

`ToolResultCache` は現在 `ToolExecutor` からは使われていない。`ToolExecutor` は独自の `OrderedDict` ベースのキャッシュを内部に持ち(`shared/tool_executor.py` の `_execute_with_cache()` / `_store_and_evict()`)、`ToolResultCache` にはない stampede 防止機構(`_inflight` future 共有)と密結合している。
`ToolResultCache` は非推奨ではなく、stampede 防止が不要な将来の利用者向けにシンプルな LRU+TTL キャッシュとして残されている実装だが、現時点での正規キャッシュではない (Explicit in code: `scripts/shared/tool_cache.py` モジュールdocstring)。

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_02_01_types_and_protocols-core-types.md`
- `90_shared_02_03_types_and_protocols-reference.md`
- `90_shared_02_02_types_and_protocols-tool-and-execution-dto-part2.md`

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
