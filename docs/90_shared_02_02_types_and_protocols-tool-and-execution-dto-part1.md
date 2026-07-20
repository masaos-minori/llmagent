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
    request_id: str        # x-request-id from HTTP transport; "" for cache hits
    server_key: str        # server key that handled the call
    source: str = ""       # "mcp" for MCP tools, "cache" for cache hits, "" for error paths
    error_type: str = ""   # "transport" | "tool" | "" (empty on success)

    @classmethod
    def from_transport(cls, output: str, is_error: bool, request_id: str = "") -> "ToolCallResult"

@dataclass(frozen=True)
class TransportErrorInfo:
    summary: str           # Human-readable error summary
    detail: str            # JSON-encoded dict for audit log
```

- `ToolCallResult` はすべてのツール呼び出し実行 (transport, cache) における正規の結果契約である
- `source` フィールドは呼び出し元の種別(`"mcp"`/`"cache"`)を区別する。`from_transport()` は常に `source="mcp"` を設定する (Explicit in code: `scripts/shared/transport_dto.py`)
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

### 実運用では未使用

`ToolResultCache` は現在 `ToolExecutor` からは使われていない。`ToolExecutor` は独自の `OrderedDict` ベースのキャッシュを内部に持ち（キャッシュ処理とエビクション処理）、`ToolResultCache` にはない stampede 防止機構（`_inflight` future 共有）と密結合している。
`ToolResultCache` は非推奨ではなく、stampede 防止が不要な将来の利用者向けにシンプルな LRU+TTL キャッシュとして残されている実装だが、現時点での正規キャッシュではない (Explicit in code: `scripts/shared/tool_cache.py` モジュールdocstring)。

---

## 7c. `RuntimeTool` (`shared/runtime_tool.py`)

```python
AgentSafetyTier = Literal["READ_ONLY", "WRITE_SAFE", "WRITE_DANGEROUS", "ADMIN"]

@dataclass(frozen=True)
class RuntimeTool:
    """Normalized runtime metadata for a single tool."""
    name: str
    server_key: str
    server_url: str
    description: str
    input_schema: dict[str, object]
    raw_definition: dict[str, object]
    status: str
    is_write: bool
    requires_serial: bool
    resource_scope: str
    agent_safety_tier: AgentSafetyTier
    requires_approval: bool
    enabled_for_llm: bool

def build_runtime_tool(
    name: str,
    server_key: str,
    server_url: str = "",
    description: str = "",
    input_schema: dict[str, object] | None = None,
    raw_definition: dict[str, object] | None = None,
    status: str = "active",
    is_write: bool | None = None,
    requires_serial: bool | None = None,
    resource_scope: str = "",
    agent_safety_tier: AgentSafetyTier | None = None,
    requires_approval: bool | None = None,
    enabled_for_llm: bool | None = None,
) -> RuntimeTool
```

- 13フィールドの正規化されたツール実行メタデータ (ルーティング、LLMスキーマ、スケジューラメタデータ、副作用検出、安全性ティア、承認要否) を1つの型で表現する
- `AgentSafetyTier` の4値 (`READ_ONLY`/`WRITE_SAFE`/`WRITE_DANGEROUS`/`ADMIN`) は `agent/tool_policy.py` の `_TIER_TO_RISK` dict のキー文字列と同一だが、`shared-is-leaf` インポート制約 (`shared` は `agent` をインポートしない) のため `agent.tool_enums` からインポートせず、本モジュール内でローカルな `Literal` 型として重複定義している
- `build_runtime_tool()` はモジュール関数 (classmethodではない) で、未指定の注釈フィールドに安全側のデフォルトを適用する: `is_write` 省略時は `False`、`requires_serial` は `is_write` が明示指定されていない場合のみ `True`、`agent_safety_tier` 省略時は最も保守的な `"WRITE_DANGEROUS"`、`requires_approval` 省略時は `True`、`enabled_for_llm` 省略時は `False`
- **[Explicit in code]** browser-mcp `browser_fetch` ツールが `config_dependent: True` を採用したことで、`RuntimeTool` / `build_runtime_tool()` が初めて実データで使用されている。MCPツールディスカバリによる実データの投入も完了済み
- Import: `from shared.runtime_tool import RuntimeTool, build_runtime_tool, AgentSafetyTier`

---

## 7d. `RuntimeToolRegistry` (`shared/runtime_tool_registry.py`)

```python
class RuntimeToolRegistry:
    def __init__(self, tools: dict[str, RuntimeTool] | None = None) -> None
    def resolve(self, tool_name: str) -> str | None
    def get(self, tool_name: str) -> RuntimeTool
    def all_tools(self) -> list[RuntimeTool]
    def llm_tool_definitions(self) -> list[dict[str, object]]
    def tool_spec_map(self) -> dict[str, ToolSpec]
    def tool_spec_for_call(self, call_id: str, name: str, args: dict[str, object]) -> ToolSpec
    def is_side_effect(self, tool_name: str) -> bool
    def classify_operation_type(self, tool_name: str) -> Literal["read", "write"]
    def apply_policy(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None
```

- `{name: RuntimeTool}` を保持するインメモリレジストリ。プレーンな可変クラスで `dict` をラップするのみ（`Protocol`/`ABC` なし）
- `resolve()` は未登録名に対して `shared.tool_registry.ToolRegistry.get_server_for_tool()` と同じ挙動（`None` を返す）で、`get()`（および内部で `get()` を呼ぶ `tool_spec_for_call()`/`is_side_effect()`/`classify_operation_type()`）は未登録名に対して `KeyError` を送出する — 「登録済みだが注釈不足」（安全側デフォルトが既に適用済み）と「レジストリに存在しない」を区別する設計
- `classify_operation_type()` は `agent.tool_enums.OperationType` ではなく、ローカルな `Literal["read", "write"]` を返す — `RuntimeTool` が `is_write: bool` しか持たないため `DELETE`/`API_WRITE`/`EXECUTE` の粒度は導出できない（`shared-is-leaf` インポート制約により `agent.tool_enums` はインポートしない、意図的な未対応であり隠れた欠落ではない）
- `apply_policy()` は `agent.config_dataclasses.ToolConfig`/`ApprovalConfig` ではなく、プレーンな `tier_map: Mapping[str, AgentSafetyTier]` と `allowed_tools: Sequence[str] = ()` を受け取る（同じく `shared-is-leaf` 制約のため）。`allowed_tools` が空の場合は全ツール許可（`ToolConfig.allowed_tools` と同じ規約）。`requires_approval`/`enabled_for_llm` の再導出規則（`WRITE_DANGEROUS`/`ADMIN` ティアは承認必須）は暫定的な既定であり、後続の `/reload` 実装ステップで見直される可能性がある
- `is_side_effect()` は `shared.tool_executor_helpers.is_side_effect()`（`_SIDE_EFFECT_TOOLS` frozenset ベース）を置き換えるものではなく、意図的に並行して重複させた実装（登録済み `RuntimeTool.is_write` を参照する）— どちらも `shared/` にあるためレイヤー制約上の問題はない
- **[Explicit in code]** MCP ディスカバリ（`McpToolDiscoveryService`）がレジストリを実データで投入し、`ToolExecutor.set_runtime_registry()` で接続済み。`ToolRouteResolver.resolve()` は RuntimeToolRegistry を最優先で解決し、見つからない場合に `ToolRegistry` にフォールバックする
- Import: `from shared.runtime_tool_registry import RuntimeToolRegistry`

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
ToolDefinition
ArtifactEvent
ShellPolicy
DbConfig
RuntimeTool
AgentSafetyTier
build_runtime_tool
RuntimeToolRegistry
