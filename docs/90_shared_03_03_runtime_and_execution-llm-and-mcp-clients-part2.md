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
  - 90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md
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
        sse_malformed_retry: int = 2,
        sse_reconnect_max: int = 1,
        llm_stream_retry_on_heartbeat_timeout: bool = True,
        llm_stream_retry_on_malformed_chunk: bool = False,
    )

    async def call(url: str, history: list[LLMMessage], tool_defs: list[dict[str, Any]]) -> LLMResponse      # Non-streaming
    async def stream(url: str, history: list[LLMMessage], tool_defs: list[dict[str, Any]]) -> LLMResponse  # Streaming
    def build_payload(history: list[LLMMessage], tool_defs: list[dict[str, Any]], stream: bool = False) -> dict[str, Any]  # Payload construction
```

**訂正 (Explicit in code):** 旧記述は `sse_malformed_retry`(既定2)、`sse_reconnect_max`(既定1)、`llm_stream_retry_on_heartbeat_timeout`(既定True)、`llm_stream_retry_on_malformed_chunk`(既定False)を欠いていた。これらはコンストラクタ引数であると同時に `apply_config()` によるホットリロード対象でもある。

**エラー挙動:**
- HTTPエラー → `LLMErrorKind` 分類付きの `LLMTransportError`(`shared/llm_exceptions.py`)。`kind` は `HTTP_STATUS_RETRYABLE` / `HTTP_STATUS_FATAL` / `CONNECT_ERROR` / `READ_TIMEOUT` / `HEARTBEAT_TIMEOUT` / `MALFORMED_SSE_FRAME` / `UTF8_PARTIAL_DECODE_ERROR` / `PREMATURE_EOF` / `UNKNOWN_STREAM_ERROR` のいずれか(Explicit in code)
- SSEハートビートタイムアウト → リトライ(`llm_stream_retry_on_heartbeat_timeout` で設定可能)
- SSEの不正なチャンク → リトライ(`llm_stream_retry_on_malformed_chunk` で設定可能)。既定は `sse_malformed_retry=2` 回まで許容し、超過すると `MALFORMED_SSE_FRAME` として送出される(`shared/sse_parser.py` の `RobustSSEParser`)
- リトライ上限到達 → `LLMTransportError` を発生。`partial_text` に失敗までに蓄積した出力を保持する
- HTTPステータス429/503 → リトライ対象(`HTTP_STATUS_RETRYABLE`)、それ以外は `HTTP_STATUS_FATAL` として即失敗(`shared/llm_transport_errors.py`)

**リトライ:** `retry_base_delay` から始まる指数バックオフ。上限は `max_retries`(非ストリーミング、`shared/llm_retry.py`)。ストリーミング再接続は別カウンタ `sse_reconnect_max` で上限管理される(`shared/llm_reconnect.py`)。

**統計(インスタンスレベル):** `stat_retries`、`stat_reconnects`、`stat_heartbeat_timeouts`、`stat_parse_errors`

**訂正 (Explicit in code):** `stat_partial_completions` というインスタンス属性は存在しない。`LlmReconnectHandler.stream()` は `partial_completions`(部分出力ありで再接続した回数)をタプルの一要素として返すが、`LLMClient.stream()` はこの値をどのインスタンス属性にも蓄積していない — 呼び出し元に伝播されずに破棄される。

**設定:** `apply_config()`(`shared/llm_hot_config.py` の `LlmHotConfigHandler`)は次のフィールドをホットリロードする: `temperature`、`max_tokens`、`max_retries`、`retry_base_delay`、`sse_heartbeat_timeout`、`sse_malformed_retry`、`sse_reconnect_max`、`stream_retry_on_heartbeat_timeout`、`stream_retry_on_malformed_chunk`。`None` を渡したフィールドは更新されない(既存値を保持)。

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

> **注記:** `McpServerConfig.transport` は(単純な`str`ではなく)`TransportType` enum を使用する。同モジュール内の関連enum: `StartupMode`(`none`/`persistent`/`subprocess`）、`SecurityProfile`(`local`/`production`、MCP認証強制を制御）。`HealthcheckMode` enumは2026-07-17に削除された — HTTPが唯一のtransportであり、healthcheck方式は常に`"http"`だったため、実装されたことのない第2の方式のための不要な配線だった。

`shared/route_resolver.py` の `build_discovery_map(server_tool_lists)` は現在 `tuple[dict[str, str], dict[str, list[str]]]` を返す: `(route_map, duplicates)` であり、`duplicates` は複数サーバから要求されたツール名を、要求元サーバキーの一覧にマッピングする。

---

## 12. 実行フローのまとめ

**設定の読み込み:**
```
build_agent_config()
  → ConfigLoader().load_all()     [_BASE_CONFIG_FILES = ("agent.toml",) の1ファイルのみ — 詳細は90_shared_03_01 §2aを参照]
```

**実装上の補足:** 他の設定(crawler.toml、chunk_splitter.toml、ingester.toml、各`*_mcp_server.toml`等)はプロセス分離方針により各プロセスが個別にロードし、エージェントの`load_all()`には含まれない(Explicit in code)。

**ツール実行:**
```
ToolExecutor.execute(tool_name, args)
  → ヘルスゲート → キャッシュ → 生のMCP呼び出し
```

---

## 13. インポート境界と設計上の注記

- `shared/` は `agent/`、`mcp_servers/`、`rag/`、`db/` をインポートしてはならない
- `LLMClient` の詳細は本ドキュメント(§10)および [05_agent_05_llm-and-streaming-part1.md](05_agent_05_llm-and-streaming-part1.md) を参照
- `ToolExecutor` の詳細は本ドキュメント(§9)、[04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)、[05_agent_06_01_tool-execution-and-approval-execution.md](05_agent_06_01_tool-execution-and-approval-execution.md) を参照

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_03_01_runtime_and_execution-config-and-logging.md`
- `90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`
- `90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md`
- `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md`

## Keywords

LLMClient
McpServerConfig
McpServerHealthRegistry
execution flow summary
import boundaries
