---
title: "Shared Runtime and Execution - LLM and MCP Clients (Part 2)"
category: shared
tags:
  - shared
  - runtime
  - llm-client
  - mcp-server-config
  - execution-flow
related:
  - 90_shared_00_document-guide.md
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
  - 90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md
  - 90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md
source:
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md
---

# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 10. `LLMClient` (`shared/llm_client.py`)

**責務:** リトライロジック、SSEストリーミング、エラーハンドリングを備えたLLM API通信用HTTPクライアント。

**主要API:**
```python
class LLMClient:
    def __init__(
        http: AsyncClient,
        max_retries: int,
        retry_base_delay: float,
        temperature: float,
        max_tokens: int,
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
        sse_heartbeat_timeout: float = 30.0,
    )

    async def call(url: str, history: list[LLMMessage], tool_defs: list[dict[str, Any]]) -> LLMResponse      # Non-streaming
    async def stream(url: str, history: list[LLMMessage], tool_defs: list[dict[str, Any]]) -> LLMResponse  # Streaming
    def build_payload(history: list[LLMMessage], tool_defs: list[dict[str, Any]], stream: bool = False) -> dict[str, Any]  # Payload construction
```

**エラー挙動:**
- HTTPエラー → `LLMErrorKind` 分類付きの `LLMTransportError`
- SSEハートビートタイムアウト → リトライ(`llm_stream_retry_on_heartbeat_timeout` で設定可能)
- SSEの不正なチャンク → リトライ(`llm_stream_retry_on_malformed_chunk` で設定可能)
- リトライ上限到達 → `LLMTransportError` を発生

**リトライ:** `retry_base_delay` から始まる指数バックオフ。上限は `max_retries`。

**統計(インスタンスレベル):** `stat_retries`、`stat_reconnects`、`stat_heartbeat_timeouts`、`stat_partial_completions`、`stat_parse_errors`

**設定:** `apply_config()` は設定辞書からtemperature、max_tokens等のフィールドをホットリロードする。

**詳細:** ストリーミングプロトコルの詳細とSSEパーサの内部実装は [05_agent_05_llm-and-streaming-part1.md](05_agent_05_llm-and-streaming-part1.md) を参照。

---

## 11. `McpServerConfig` / `McpServerHealthRegistry`

両方とも `shared/mcp_config.py` で定義されている。フィールド全体のリファレンスは
[04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md) と
[05_agent_08_01_configuration-loading-agent-config-part1.md](05_agent_08_01_configuration-loading-agent-config-part1.md) を参照。

**概要:**
- `McpServerConfig`: サーバごとのトランスポート設定(transport、url、cmd、startup_mode、tool_names、auth_token等) — `__post_init__` により検証される(URLスキーム、タイムアウト範囲、tool_namesの一意性、env型)。`key` フィールドは `_build_single_server()` がTOMLセクション名から設定し、`==` 比較からは除外される。
- `McpServerHealthState`: `HEALTHY` / `DEGRADED` / `UNAVAILABLE`
- `McpServerHealthRegistry`: 連続失敗を追跡する;`UNAVAILABLE` はディスパッチをブロックする;`record_degraded(key, reason)` / `get_degraded_reason(key)` は失敗カウントを増やさずに「到達可能だが劣化している」サーバを追跡する

> **注記:** `McpServerConfig.transport` は(単純な`str`ではなく)`TransportType` enum を使用する。同モジュール内の関連enum: `StartupMode`(`none`/`persistent`/`subprocess`）、`HealthcheckMode`(`http`）、`SecurityProfile`(`local`/`production`、MCP認証強制を制御）。

`shared/route_resolver.py` の `build_discovery_map(server_tool_lists)` は現在 `tuple[dict[str, str], dict[str, list[str]]]` を返す: `(route_map, duplicates)` であり、`duplicates` は複数サーバから要求されたツール名を、要求元サーバキーの一覧にマッピングする。

---

## 12. 実行フローのまとめ

**設定の読み込み:**
```
build_agent_config()
  → ConfigLoader().load_all()     [agent.toml含む12ファイル — 全体表は§2a Config Ownershipを参照]
```

**プラグインの読み込み:**
```
プラグインレジストリの初期化
  → plugin_registry.load_plugins(plugin_dir)
  → plugins/*.py をアルファベット順にインポート
  → @register_* デコレータがグローバルレジストリを構築
```

**ツール実行:**
```
ToolExecutor.execute(tool_name, args)
  → プラグイン優先 → ヘルスゲート → キャッシュ → 生のMCP呼び出し
```

---

## 13. インポート境界と設計上の注記

- `shared/` は `agent/`、`mcp/`、`rag/`、`db/` をインポートしてはならない
- `LLMClient` の詳細は本ドキュメント(§10)および [05_agent_05_llm-and-streaming-part1.md](05_agent_05_llm-and-streaming-part1.md) を参照
- `ToolExecutor` の詳細は本ドキュメント(§9)、[04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)、[05_agent_06_01_tool-execution-and-approval-execution.md](05_agent_06_01_tool-execution-and-approval-execution.md) を参照

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_03_01_runtime_and_execution-config-and-logging.md`
- `90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md`
- `90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md`
- `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md`

## Keywords

LLMClient
McpServerConfig
McpServerHealthRegistry
execution flow summary
import boundaries
