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

**主要API:** LLMClient wraps AsyncClient with retry logic, SSE streaming, error handling. Constructor accepts http client, max_retries, retry_base_delay, temperature, max_tokens, optional callbacks (on_token/on_usage), SSE parameters (sse_heartbeat_timeout=30, sse_malformed_retry=2, sse_reconnect_max=1, llm_stream_retry_on_heartbeat_timeout=True, llm_stream_retry_on_malformed_chunk=False). call()/stream() accept url/history/tool_defs; build_payload constructs request dict.

**エラー挙動:** HTTP errors → LLMTransportError classified by kind: HTTP_STATUS_RETRYABLE (429/503), HTTP_STATUS_FATAL (others), CONNECT_ERROR, READ_TIMEOUT, HEARTBEAT_TIMEOUT, MALFORMED_SSE_FRAME, UTF8_PARTIAL_DECODE_ERROR, PREMATURE_EOF, UNKNOWN_STREAM_ERROR. SSE heartbeat timeout retries if enabled; malformed chunk retries up to sse_malformed_retry times then raises MALFORMED_SSE_FRAME. Retry exhaustion raises LLMTransportError with partial_text containing accumulated output.

**リトライ:** Exponential backoff starting from retry_base_delay; limit max_retries for non-streaming; streaming reconnection uses separate counter sse_reconnect_max.

**統計(インスタンスレベル):** Instance-level stats: stat_retries, stat_reconnects, stat_heartbeat_timeouts, stat_parse_errors. Note: stat_partial_completions does not exist; LlmReconnectHandler.stream() returns partial_completions as tuple element but LLMClient.stream() discards without accumulating.

**設定:** LlmHotConfigHandler applies hot reload for: temperature, max_tokens, max_retries, retry_base_delay, sse_heartbeat_timeout, sse_malformed_retry, sse_reconnect_max, stream_retry_on_heartbeat_timeout, stream_retry_on_malformed_chunk. None values leave existing values unchanged.

**詳細:** ストリーミングプロトコルの詳細とSSEパーサの内部実装は [05_agent_05_llm-and-streaming-part1.md](05_agent_05_llm-and-streaming-part1.md) を参照。

---

## 11. `McpServerConfig` / `McpServerHealthRegistry`

両方とも `shared/mcp_config.py` で定義されている。フィールド全体のリファレンスは [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md) と [05_agent_08_01_configuration-loading-agent-config-part1.md](05_agent_08_01_configuration-loading-agent-config-part1.md) を参照。

**概要:** Per-server transport config (transport, url, cmd, startup_mode, tool_names, auth_token, env) validated by __post_init__ (URL scheme, timeout range, tool_names uniqueness, env type). key field set from TOML section name, excluded from == comparison. McpServerHealthState: HEALTHY / DEGRADED / UNAVAILABLE. McpServerHealthRegistry tracks consecutive failures; UNAVAILABLE blocks dispatch; record_degraded(key, reason) / get_degraded_reason(key) track "reachable but degraded" servers without incrementing failure count.

> **注記:** McpServerConfig.transport uses TransportType enum instead of plain str. Related enums: StartupMode (none/persistent/subprocess), SecurityProfile (local/production controls MCP auth enforcement). HealthcheckMode enum deleted 2026-07-17 — HTTP was only transport.

`shared/route_resolver.py` の `build_discovery_map(server_tool_lists)` は現在 `tuple[dict[str, str], dict[str, list[str]]]` を返す: `(route_map, duplicates)` であり、`duplicates` は複数サーバから要求されたツール名を、要求元サーバキーの一覧にマッピングする。

---

## 12. 実行フローのまとめ

**設定の読み込み:** build_agent_config() → ConfigLoader().load_all() reads agent.toml only (_BASE_CONFIG_FILES = ("agent.toml",)). Other configs (crawler.toml, chunk_splitter.toml, ingester.toml, *_mcp_server.toml) loaded separately per process isolation policy.

**ツール実行:** ToolExecutor.execute(tool_name, args) → health gate → cache → raw MCP call.

---

## 13. インポート境界と設計上の注記

- `shared/` は `agent/`、`mcp_servers/`、`rag/`、`db/` をインポートしてはならない
- `LLMClient` の詳細は本ドキュメント(§10)および [05_agent_05_llm-and-streaming-part1.md](05_agent_05_llm-and-streaming-part1.md) を参照
- `ToolExecutor` の詳細は本ドキュメント(§9)、[04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)、[05_agent_06_01_tool-execution-and-approval-execution.md](05_agent_06_01_tool-execution-and-approval-execution.md) を参照

---
