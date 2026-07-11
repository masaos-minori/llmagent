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
- `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md`
- `90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md`

## Keywords

LlmRetryHandler
ToolResultCache
CacheEntry
ToolSpec
PluginToolInvoker
McpServerHealthState
LlmPayloadHandler
LlmHotConfigHandler
