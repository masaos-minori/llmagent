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
  - 90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md
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

- TTL 失効とオプションの最大サイズ超過時のエビクションを備えた、ツール呼び出し結果用の LRU キャッシュ
- `is_error=False` の結果のみキャッシュされる (`store_if_success` はエラー結果をスキップする)
- キャッシュキーの形式: `{tool_name}:{json_dumps(args)}` (`shared.json_utils.dumps` を使用)
- TTL チェック: `time.time() - cached_at >= ttl` → エビクトして None を返す
- LRU エビクション: `max_size > 0` かつキャッシュが上限を超えた場合、`popitem(last=False)` で最も古いエントリを削除する
- インポート: `from shared.tool_cache import ToolResultCache`
- **[Explicit in code]** `shared/tool_cache.py` のモジュール docstring により、`ToolResultCache` は現時点で `ToolExecutor` からは使用されていないと明記されている。`ToolExecutor` は `shared/tool_executor.py` 内に独自の `OrderedDict` ベースのキャッシュ（キャッシュ処理とエビクション処理）を持ち、`_inflight` (`dict[str, asyncio.Future]`) によるスタンピード防止 (同時リクエストの future 共有) と統合されている。`ToolResultCache` にはスタンピード防止の仕組みが無い
- **[Explicit in code]** `ToolResultCache` は非推奨ではなく、スタンピード防止を必要としない将来の呼び出し元向けに、LRU+TTL キャッシュ単体機能を提供するスタンドアロンユーティリティとして残置されている
- **[Explicit in code]** `get_result()` の戻り値 `ToolCallResult` は `request_id=""`, `server_key=""` で構築され、`error_type` は `is_error=True` のとき `"tool"`、それ以外は `""` となる

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
- `90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md`
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
