---
title: "Shared Runtime and Execution - Caching and Reference"
category: shared
tags:
  - shared
  - runtime
  - retry-handler
  - tool-cache
  - tool-spec
  - plugin-invoker
  - ai-reference
related:
  - 90_shared_00_document-guide.md
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
  - 90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md
source:
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
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

## 17. `PluginToolInvoker` (`shared/plugin_tool_invoker.py`)

```python
class PluginToolInvoker:
    async def try_execute(self, tool_name: str, args: dict[str, Any]) -> ToolCallResult | None
```

- `plugin_registry.register_tool()` 経由で登録されたプラグインツールを実行する
- 指定された名前に対応するプラグインツールが登録されていない場合は `None` を返す
- プラグインの例外を `ToolCallResult(is_error=True)` に変換し、エラーをローカルに留める (決して伝播させない)
- 戻り値の契約に対して防御的なランタイム検証を行う: 厳密に2要素のタプル `(str, bool)` でなければならない
- output が str でない、または is_error が bool でない場合は `TypeError` をスローする
- インポート: `from shared.plugin_tool_invoker import PluginToolInvoker`

---

## 18. `McpServerHealthState` / `McpServerHealthRegistry` (`shared/mcp_health.py`)

```python
class McpServerHealthState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"   # failing but not yet unavailable
    UNAVAILABLE = "unavailable"
    HALF_OPEN = "half_open"

class McpServerHealthRegistry:
    def __init__(self, failure_threshold: int = 3, half_open_cooldown_sec: float = 30.0)
    def record_failure(self, server_key: str) -> McpServerHealthState
    def record_success(self, server_key: str) -> None
    def get_state(self, server_key: str) -> McpServerHealthState
    def is_unavailable(self, server_key: str) -> bool
```

- ToolExecutor のディスパッチゲーティングのために、サーバーごとのヘルス状態を追跡する
- 状態遷移:
  - HEALTHY → DEGRADED (最初の失敗)
  - DEGRADED → UNAVAILABLE (failure_threshold 回連続失敗、デフォルト 3 回)
  - UNAVAILABLE → HALF_OPEN (half_open_cooldown_sec 経過後、デフォルト 30 秒、試験的プローブ)
  - HALF_OPEN → UNAVAILABLE (試験的プローブ中の失敗、クールダウンがリセットされる)
  - HALF_OPEN → HEALTHY (試験的プローブ中の成功)
  - いずれの状態からも → HEALTHY (成功レスポンスによりすべてがリセットされる)
- `is_unavailable()` は、クールダウン失効時の UNAVAILABLE → HALF_OPEN 遷移も処理する
- インポート: `from shared.mcp_health import McpServerHealthState, McpServerHealthRegistry`

---

## 19. `LlmPayloadHandler` (`shared/llm_payload.py`)

```python
class LlmPayloadHandler:
    def build_payload(self, history: list[LLMMessage], tool_defs: list[dict[str, Any]], stream: bool = False) -> dict[str, Any]
    def parse_response(self, response: httpx.Response) -> LLMResponse
```

- history とツール定義から LLM リクエストペイロードを構築する
- HTTP レスポンスを LLMResponse DTO にパースする
- インポート: `from shared.llm_payload import LlmPayloadHandler`

---

## 20. `LlmHotConfigHandler` (`shared/llm_hot_config.py`)

```python
class LlmHotConfigHandler:
    """Hot-reloadable config fields for LLMClient."""
```

- LLMClient のホットリロード可能な設定フィールド (temperature, max_tokens など) を管理する
- インポート: `from shared.llm_hot_config import LlmHotConfigHandler`

---

## 21. AI リファレンスガイド

| 質問 | 回答 |
|---|---|
| 設定ファイルの読み込み方法 | `ConfigLoader().load("filename.toml")` または `load_all()` |
| 設定オーナーシップ表 | **§2a 設定オーナーシップを参照** — 12 個の TOML ファイルすべての正式なリファレンス |
| `load_all()` は `agent.toml` を含むか? | **含む** — `_BASE_CONFIG_FILES` のインデックス 0 に含まれる (§2a 設定オーナーシップを参照) |
| プラグインツールの登録方法 | `plugins/*.py` 内の `@register_tool("name")` デコレータ |
| ToolExecutor がキャッシュを使うのはいつか? | `is_error=False` の結果のみ; TTL + LRU |
| `git_helper.get_repo_info()` は信頼できるか? | `RepoInfoResult` を返す; `.success` と `.failure_reason` (FailureReason enum) を確認すること |
| 正確なトークン数を取得する方法 | `await get_token_count(history, tokenize_url, http)` |
| LLM の再試行はどう動くか? | 指数バックオフ: 429/503 および接続エラー時に `retry_base_delay * (2**attempt)` |
| ToolExecutor のキャッシュキー形式は? | `{tool_name}:{json_dumps(args)}` (`shared.json_utils.dumps` を使用) |
| ヘルスゲートの状態遷移は? | HEALTHY → DEGRADED → UNAVAILABLE → HALF_OPEN → HEALTHY/UNAVAILABLE (§18 を参照) |

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_03_01_runtime_and_execution-config-and-logging.md`
- `90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md`
- `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`

## Keywords

LlmRetryHandler
ToolResultCache
CacheEntry
ToolSpec
PluginToolInvoker
McpServerHealthState
LlmPayloadHandler
LlmHotConfigHandler
