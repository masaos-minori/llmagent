---
title: "Shared Runtime and Execution - Caching and Reference (Part 1)"
category: shared
tags:
  - shared
  - runtime
  - retry-handler
  - tool-cache
  - tool-spec
  - ai-reference
related:
  - 90_shared_00_document-guide.md
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
  - 90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md
source:
  - 90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md
---

# 共有ランタイムおよび実行インフラストラクチャ

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 14. `LlmRetryHandler` (`shared/llm_retry.py`)

```python
class LlmRetryHandler:
    @staticmethod
    async def request_with_retry(
        http: httpx.AsyncClient,
        url: str,
        payload: dict[str, object],
        max_retries: int,
        retry_base_delay: float,
    ) -> httpx.Response
```

- LLM への HTTP POST リクエストに対する指数バックオフ再試行
- 429 (レート制限) と 503 (サービス利用不可)、および `httpx.RequestError` (接続エラー) を再試行対象とする
- 一時的でない HTTP エラー (429/503 以外の 4xx, 5xx) は即座に再スローされる
- 遅延計算式: `retry_base_delay * (2**attempt)` (attempt は 0 始まり)
- すべての試行を使い切った場合は最後の例外をスローする
- インポート: `from shared.llm_retry import LlmRetryHandler`

---

## 15. `ToolResultCache` / `CacheEntry` (`shared/tool_cache.py`)

```python
@dataclass(frozen=True)
class CacheEntry:
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

**ToolResultCache**: Standalone LRU+TTL cache utility for tool results. Not currently used by ToolExecutor; kept for potential future use without stampede protection.

---

## 16. `ToolSpec` (`shared/tool_spec.py`)

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

- DAG スケジューリング (無条件) で使用される — DAG 実行レイヤーが各ツール呼び出しに対して ToolSpec を構築する
- `resource_scope` により、同一リソースに対する並列ツール呼び出し間の競合検出が可能になる
- `requires_serial` は、並列実行モードであっても強制的にシリアライズする
- `is_write` は `is_side_effect()` が書き込み/削除系ツールを分類する際に使用される
- インポート: `from shared.tool_spec import ToolSpec`

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_03_01_runtime_and_execution-config-and-logging.md`
- `90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`
- `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md`
- `90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md`

## Keywords

LlmRetryHandler
ToolResultCache
CacheEntry
_inflight
ToolSpec
McpServerHealthState
LlmPayloadHandler
LlmHotConfigHandler
