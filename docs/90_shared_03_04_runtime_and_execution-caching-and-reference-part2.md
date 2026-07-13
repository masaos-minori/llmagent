---
title: "Shared Runtime and Execution - Caching and Reference (Part 2)"
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
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md
source:
  - 90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md
---

# 共有ランタイムおよび実行インフラストラクチャ

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 18. `McpServerHealthState` / `McpServerHealthRegistry` (`shared/mcp_health.py`)

```python
class McpServerHealthState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"   # failing but not yet unavailable
    UNAVAILABLE = "unavailable"
    HALF_OPEN = "half_open"
    UNKNOWN = "unknown"

class McpServerHealthRegistry:
    def __init__(self, failure_threshold: int = 3, half_open_cooldown_sec: float = 30.0)
    def record_failure(self, server_key: str) -> McpServerHealthState
    def record_degraded(self, server_key: str, reason: str | None = None) -> None
    def record_restart_exhausted(self, server_key: str) -> None
    def get_degraded_reason(self, server_key: str) -> str | None
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
- **[Explicit in code — 追加]** `McpServerHealthState` には上記4状態に加えて `UNKNOWN` が定義されている。`get_state()` は未登録の `server_key` に対しては `UNKNOWN` ではなく `HEALTHY` をデフォルトとして返す (`_states.get(server_key, HEALTHY)`) ため、`UNKNOWN` がいつ観測されるかはこのモジュール単体からは確認できない
- **[Explicit in code — 追加]** `record_degraded(server_key, reason=None)`: ウォッチドッグの到達可能だが劣化しているプローブ結果を記録する。現在の状態が `UNAVAILABLE` または `HALF_OPEN` の場合は状態を上書きせず (サーキットブレーカーやトライアル窓を壊さないための意図的なガード)、debug ログのみ出力して何もしない
- **[Explicit in code — 追加]** `record_restart_exhausted(server_key)`: ウォッチドッグの再起動試行が上限に達したことを記録する。状態自体は変更せず (`record_failure()` により既に `UNAVAILABLE` になっている前提)、`_degraded_reasons` に `"restart_limit_reached"` をタグ付けするのみ。「まだ再起動サイクル中」と「ウォッチドッグが諦めて手動対応が必要」を `/mcp status` 等で区別するためのもの
- **[Explicit in code — 追加]** `get_degraded_reason(server_key)`: 直近に記録された劣化理由 (文字列) を返す。無ければ `None`
- **[Explicit in code — 追加]** `record_success()` は状態を `HEALTHY` にするだけでなく、`_failure_counts` / `_unavailable_since` / `_degraded_reasons` もリセットする。`_failure_counts` をリセットしない場合、成功後の次の失敗が古いカウントの残留により即座に `UNAVAILABLE` へ遷移してしまうため
- インポート: `from shared.mcp_health import McpServerHealthState, McpServerHealthRegistry`

---

## 19. `LlmPayloadHandler` (`shared/llm_payload.py`)

```python
class LlmPayloadHandler:
    @staticmethod
    def build_payload(history: list[LLMMessage], tool_defs: list[dict[str, Any]], temperature: float, max_tokens: int, stream: bool = False) -> dict[str, Any]
    @staticmethod
    def parse_response(raw: dict[str, Any], on_usage: object | None = None) -> LLMResponse
    @staticmethod
    def parse_non_stream_response(content: bytes, on_usage: object | None = None) -> LLMResponse
```

- history とツール定義から LLM リクエストペイロードを構築する
- 生の JSON (dict) を LLMResponse DTO にパースする
- インポート: `from shared.llm_payload import LlmPayloadHandler`
- **[Explicit in code — 訂正]** 全メソッドは `@staticmethod`。旧記載のシグネチャは実装と相違があり以下のとおり訂正する:
  - `build_payload()` は `temperature: float` と `max_tokens: int` を必須引数に取る (旧記載には無かった)。返す payload には `messages` / `tools` / `tool_choice="auto"` / `temperature` / `max_tokens` が含まれ、`stream=True` のときのみ `"stream": True` を追加する
  - `parse_response()` の第一引数は `httpx.Response` ではなく、パース済みの `raw: dict[str, Any]` (LLM 応答 JSON)。`choices` が list でない/空、`choices[0]` が dict でない、`message` が dict でない場合は `ValueError` を送出する。`usage` は `shared.llm_sse_helpers.LlmSseHelpers.parse_usage()` に委譲する
  - `parse_non_stream_response(content: bytes, ...)` という第三のメソッドが存在する (旧記載に無い)。`orjson.loads(content)` で bytes をデコードし、結果が dict でなければ `ValueError` を送出したうえで `parse_response()` に委譲する非ストリーミング用のエントリポイント
- **[Needs confirmation]** `on_usage` の型は `object | None` としか宣言されておらず、実際の用途 (使用箇所でのコールバック形状) はこのモジュール単体からは断定できない

---

## 20. `LlmHotConfigHandler` (`shared/llm_hot_config.py`)

```python
class LlmHotConfigHandler:
    """Hot-reloadable config fields for LLMClient."""

    HOT_CONFIG_FIELDS: tuple[tuple[str, str], ...]

    @staticmethod
    def apply_one(instance: object, field: str, kwarg: str, value: Any) -> None
    @staticmethod
    def apply_config(instance: object, *, temperature: float | None = None, max_tokens: int | None = None, max_retries: int | None = None, retry_base_delay: float | None = None, sse_heartbeat_timeout: float | None = None, sse_malformed_retry: int | None = None, sse_reconnect_max: int | None = None, stream_retry_on_heartbeat_timeout: bool | None = None, stream_retry_on_malformed_chunk: bool | None = None) -> None
```

- LLMClient のホットリロード可能な設定フィールド (temperature, max_tokens など) を管理する
- **[Explicit in code]** `HOT_CONFIG_FIELDS` は `(インスタンス属性名, kwarg 名)` のタプル一覧で、対象フィールドは `temperature`, `max_tokens`, `max_retries`, `retry_base_delay`, `sse_heartbeat_timeout`, `sse_malformed_retry`, `sse_reconnect_max`, `stream_retry_on_heartbeat_timeout`, `stream_retry_on_malformed_chunk` の9件
- **[Explicit in code]** `apply_config()` はキーワード専用引数を受け取り、値が `None` でないフィールドのみ `apply_one()` 経由で `setattr` する (未指定の項目は変更しない部分更新)
- インポート: `from shared.llm_hot_config import LlmHotConfigHandler`

---

## 21. AI リファレンスガイド

| 質問 | 回答 |
|---|---|
| 設定ファイルの読み込み方法 | `ConfigLoader().load("filename.toml")` または `load_all()` |
| 設定オーナーシップ表 | **§2a 設定オーナーシップを参照** — プロセス分離方針とプロセスごとの設定ファイル一覧の正式なリファレンス |
| `load_all()` は `agent.toml` を含むか? | **含む(それのみ)** — `_BASE_CONFIG_FILES = ("agent.toml",)` の1件のみで、他の設定ファイル(crawler.toml等)は各プロセスが個別にロードする (§2a 設定オーナーシップを参照) |
| プラグインツールの登録方法 | `plugins/*.py` 内の `@register_tool("name")` デコレータ |
| ToolExecutor がキャッシュを使うのはいつか? | `is_error=False` の結果のみ; TTL + LRU。ただし `ToolExecutor` は `shared/tool_cache.py` の `ToolResultCache` ではなく、`shared/tool_executor.py` 内の自前の `OrderedDict` ベースキャッシュ (`_execute_with_cache()`) を使う (§15 を参照) |
| `git_helper.get_repo_info()` は信頼できるか? | `RepoInfoResult` を返す; `.success` と `.failure_reason` (FailureReason enum) を確認すること |
| 正確なトークン数を取得する方法 | `await get_token_count(history, tokenize_url, http)` |
| LLM の再試行はどう動くか? | 指数バックオフ: 429/503 および接続エラー時に `retry_base_delay * (2**attempt)` |
| ToolExecutor のキャッシュキー形式は? | `{tool_name}:{json_dumps(args)}` (`shared.json_utils.dumps` を使用) |
| ヘルスゲートの状態遷移は? | HEALTHY → DEGRADED → UNAVAILABLE → HALF_OPEN → HEALTHY/UNAVAILABLE (§18 を参照)。`UNKNOWN` 状態も定義されているが `get_state()` の既定値は `HEALTHY` |

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_03_01_runtime_and_execution-config-and-logging.md`
- `90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md`
- `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md`
- `90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md`

## Keywords

LlmRetryHandler
ToolResultCache
CacheEntry
ToolSpec
PluginToolInvoker
McpServerHealthState
McpServerHealthRegistry
record_degraded
record_restart_exhausted
LlmPayloadHandler
parse_non_stream_response
LlmHotConfigHandler
HOT_CONFIG_FIELDS
