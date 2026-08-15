
title: "Shared Runtime and Execution - LLM and MCP Clients (Part 1)"
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
  - 90_shared_03_04_runtime_and_execution-caching-and-reference.md
source:
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md


# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 9. `ToolExecutor` and Surrounding Concepts (`shared/tool_executor.py`)

**責務:** ツールディスパッチのコアエンジン — ツール→サーバの解決、キャッシュ、同時実行数制限、ヘルスゲーティング、トランスポート通信を担う。

**`ToolCallResult` データクラス(結果の契約、`shared/transport_dto.py`、frozen dataclass):** frozen dataclass with output (truncated if > MCP_MAX_RESPONSE_BYTES), is_error, request_id (X-Request-Id from MCP server, empty for cache hits), server_key (routing target), source ('mcp'/'cache'/empty), error_type ('transport'/'tool'/empty). error_type used by health gate and error counter aggregation.

**実行フロー:** TTL+LRU cache check (success results only); stampede protection shares Future for same-key concurrent calls; resolve tool_name → server_key via ToolRouteResolver; startup_mode=none gate rejects disabled servers; McpServerHealthRegistry.is_unavailable() blocks UNAVAILABLE dispatch (HALF_OPEN allows one attempt per cooldown); lifecycle.ensure_ready() if configured; execute via HttpTransport.call() behind per-server-key semaphore; cache success results only; return ToolCallResult.

**キャッシュの挙動:** Success results only (is_error=False excluded); TTL+LRU eviction configurable via tool_cache_ttl_sec/tool_cache_maxsize; key = (tool_name, serialized_args); side-effect tools fully bypass cache.

**ヘルスゲート:** McpServerHealthRegistry.is_unavailable() blocks dispatch when UNAVAILABLE; consecutive transport failures transition HEALTHY→DEGRADED→UNAVAILABLE (failure_threshold reaches UNAVAILABLE); success response resets to HEALTHY (clears failure count/degraded reason). HALF_OPEN exists as experimental circuit-breaker recovery: after half_open_cooldown_sec in UNAVAILABLE, one dispatch attempt allowed; failure during HALF_OPEN returns immediately to UNAVAILABLE; record_degraded() does not override UNAVAILABLE/HALF_OPEN states.

**同時実行の挙動:** concurrency_limits maps server_key → max concurrent calls; semaphore-based throttling in ToolTransportInvoker; tool-call-batch parallel/serial scheduling is unified under a single path — `agent/tool_runner.py::_execute_with_dag()`, which delegates to `agent/tool_scheduler.py::build_execution_groups()`. The former non-DAG path (`_execute_standard()`) has been removed; `ctx.cfg.tool.serial_tool_calls=True` now feeds `force_serial=True` into the scheduler instead of selecting a different execution engine.

**副作用の検出:** `build_execution_groups()` reads each call's `is_write` from `PreparedToolCall.spec` (resolved once during `agent/tool_preparation.py::prepare_tool_calls()`, sourced from `RuntimeToolRegistry.tool_spec_for_call()`) — an unregistered tool is rejected fail-closed during preparation and never reaches scheduling, so no conservative "assume True" fallback remains. `_SIDE_EFFECT_TOOLS`/`is_side_effect()` (tool_executor_helpers.py) are unrelated to this decision — they back only the TTL-cache-bypass check in `shared/tool_executor.py`. See [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md) for the scheduler's grouping rules.

**ルーティング (Explicit in code):** `shared/runtime_tool_registry.py` の `RuntimeToolRegistry` が唯一のルーティング権威(sole routing authority)。`ToolRouteResolver.resolve()`(`shared/route_resolver.py`)は `RuntimeToolRegistry.resolve()` のみを参照し、未知のツールは即座に `ValueError` で失敗する。`shared/tool_registry.py` の `ToolRegistry` はルーティング判断には一切使われず、起動時のドリフト検証(`shared/tool_routing_validation.py`)専用のシードデータに格下げされている。設定ファイルの `tool_names` はドリフト検証専用のメタデータであり、実行時のルーティング判断には使われない。旧「2段カスケード」方式(ライブ検出→レジストリの順で解決)は現行コードには存在しない。ルーティングの詳細は [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md) を参照。

---

# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 9a. `ToolExecutor` and Surrounding Concepts (`shared/tool_executor.py`)

**責務:** ツールディスパッチのコアエンジン — ツール→サーバの解決、キャッシュ、同時実行数制限、ヘルスゲーティング、トランスポート通信を担う。

**`ToolCallResult` データクラス(結果の契約、`shared/transport_dto.py`、frozen dataclass):** frozen dataclass with output (truncated if > MCP_MAX_RESPONSE_BYTES), is_error, request_id (X-Request-Id from MCP server, empty for cache hits), server_key (routing target), source ('mcp'/'cache'/empty), error_type ('transport'/'tool'/empty). error_type used by health gate and error counter aggregation.

**実行フロー:** TTL+LRU cache check (success results only); stampede protection shares Future for same-key concurrent calls; resolve tool_name → server_key via ToolRouteResolver; startup_mode=none gate rejects disabled servers; McpServerHealthRegistry.is_unavailable() blocks UNAVAILABLE dispatch (HALF_OPEN allows one attempt per cooldown); lifecycle.ensure_ready() if configured; execute via HttpTransport.call() behind per-server-key semaphore; cache success results only; return ToolCallResult.

**キャッシュの挙動:** Success results only (is_error=False excluded); TTL+LRU eviction configurable via tool_cache_ttl_sec/tool_cache_maxsize; key = (tool_name, serialized_args); side-effect tools fully bypass cache.

**ヘルスゲート:** McpServerHealthRegistry.is_unavailable() blocks dispatch when UNAVAILABLE; consecutive transport failures transition HEALTHY→DEGRADED→UNAVAILABLE (failure_threshold reaches UNAVAILABLE); success response resets to HEALTHY (clears failure count/degraded reason). HALF_OPEN exists as experimental circuit-breaker recovery: after half_open_cooldown_sec in UNAVAILABLE, one dispatch attempt allowed; failure during HALF_OPEN returns immediately to UNAVAILABLE; record_degraded() does not override UNAVAILABLE/HALF_OPEN states.

**同時実行の挙動:** concurrency_limits maps server_key → max concurrent calls; semaphore-based throttling in ToolTransportInvoker; tool-call-batch parallel/serial scheduling is unified under a single path — `agent/tool_runner.py::_execute_with_dag()`, which delegates to `agent/tool_scheduler.py::build_execution_groups()`. The former non-DAG path (`_execute_standard()`) has been removed; `ctx.cfg.tool.serial_tool_calls=True` now feeds `force_serial=True` into the scheduler instead of selecting a different execution engine.

**副作用の検出:** `build_execution_groups()` reads each call's `is_write` from `PreparedToolCall.spec` (resolved once during `agent/tool_preparation.py::prepare_tool_calls()`, sourced from `RuntimeToolRegistry.tool_spec_for_call()`) — an unregistered tool is rejected fail-closed during preparation and never reaches scheduling, so no conservative "assume True" fallback remains. `_SIDE_EFFECT_TOOLS`/`is_side_effect()` (tool_executor_helpers.py) are unrelated to this decision — they back only the TTL-cache-bypass check in `shared/tool_executor.py`. See [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md) for the scheduler's grouping rules.

**ルーティング (Explicit in code):** `shared/runtime_tool_registry.py` の `RuntimeToolRegistry` が唯一のルーティング権威(sole routing authority)。`ToolRouteResolver.resolve()`(`shared/route_resolver.py`)は `RuntimeToolRegistry.resolve()` のみを参照し、未知のツールは即座に `ValueError` で失敗する。`shared/tool_registry.py` の `ToolRegistry` はルーティング判断には一切使われず、起動時のドリフト検証(`shared/tool_routing_validation.py`)専用のシードデータに格下げされている。設定ファイルの `tool_names` はドリフト検証専用のメタデータであり、実行時のルーティング判断には使われない。旧「2段カスケード」方式(ライブ検出→レジストリの順で解決)は現行コードには存在しない。ルーティングの詳細は [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md) を参照。

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

**詳細:** ストリーミングプロトコルの詳細とSSEパーサの内部実装は [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md) を参照。

---

## 11. `McpServerConfig` / `McpServerHealthRegistry`

両方とも `shared/mcp_config.py` で定義されている。フィールド全体のリファレンスは [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md) と [05_agent_08_01_configuration-loading-agent-config.md](05_agent_08_01_configuration-loading-agent-config.md) を参照。

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
- `LLMClient` の詳細は本ドキュメント(§10)および [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md) を参照
- `ToolExecutor` の詳細は本ドキュメント(§9)、[04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)、[05_agent_06_01_tool-execution-and-approval-execution.md](05_agent_06_01_tool-execution-and-approval-execution.md) を参照

---

# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 10a. `LLMClient` (`shared/llm_client.py`)

**責務:** リトライロジック、SSEストリーミング、エラーハンドリングを備えたLLM API通信用HTTPクライアント。

**主要API:** LLMClient wraps AsyncClient with retry logic, SSE streaming, error handling. Constructor accepts http client, max_retries, retry_base_delay, temperature, max_tokens, optional callbacks (on_token/on_usage), SSE parameters (sse_heartbeat_timeout=30, sse_malformed_retry=2, sse_reconnect_max=1, llm_stream_retry_on_heartbeat_timeout=True, llm_stream_retry_on_malformed_chunk=False). call()/stream() accept url/history/tool_defs; build_payload constructs request dict.

**エラー挙動:** HTTP errors → LLMTransportError classified by kind: HTTP_STATUS_RETRYABLE (429/503), HTTP_STATUS_FATAL (others), CONNECT_ERROR, READ_TIMEOUT, HEARTBEAT_TIMEOUT, MALFORMED_SSE_FRAME, UTF8_PARTIAL_DECODE_ERROR, PREMATURE_EOF, UNKNOWN_STREAM_ERROR. SSE heartbeat timeout retries if enabled; malformed chunk retries up to sse_malformed_retry times then raises MALFORMED_SSE_FRAME. Retry exhaustion raises LLMTransportError with partial_text containing accumulated output.

**リトライ:** Exponential backoff starting from retry_base_delay; limit max_retries for non-streaming; streaming reconnection uses separate counter sse_reconnect_max.

**統計(インスタンスレベル):** Instance-level stats: stat_retries, stat_reconnects, stat_heartbeat_timeouts, stat_parse_errors. Note: stat_partial_completions does not exist; LlmReconnectHandler.stream() returns partial_completions as tuple element but LLMClient.stream() discards without accumulating.

**設定:** LlmHotConfigHandler applies hot reload for: temperature, max_tokens, max_retries, retry_base_delay, sse_heartbeat_timeout, sse_malformed_retry, sse_reconnect_max, stream_retry_on_heartbeat_timeout, stream_retry_on_malformed_chunk. None values leave existing values unchanged.

**詳細:** ストリーミングプロトコルの詳細とSSEパーサの内部実装は [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md) を参照。

---

## 11a. `McpServerConfig` / `McpServerHealthRegistry`

両方とも `shared/mcp_config.py` で定義されている。フィールド全体のリファレンスは [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md) と [05_agent_08_01_configuration-loading-agent-config.md](05_agent_08_01_configuration-loading-agent-config.md) を参照。

**概要:** Per-server transport config (transport, url, cmd, startup_mode, tool_names, auth_token, env) validated by __post_init__ (URL scheme, timeout range, tool_names uniqueness, env type). key field set from TOML section name, excluded from == comparison. McpServerHealthState: HEALTHY / DEGRADED / UNAVAILABLE. McpServerHealthRegistry tracks consecutive failures; UNAVAILABLE blocks dispatch; record_degraded(key, reason) / get_degraded_reason(key) track "reachable but degraded" servers without incrementing failure count.

> **注記:** McpServerConfig.transport uses TransportType enum instead of plain str. Related enums: StartupMode (none/persistent/subprocess), SecurityProfile (local/production controls MCP auth enforcement). HealthcheckMode enum deleted 2026-07-17 — HTTP was only transport.

`shared/route_resolver.py` の `build_discovery_map(server_tool_lists)` は現在 `tuple[dict[str, str], dict[str, list[str]]]` を返す: `(route_map, duplicates)` であり、`duplicates` は複数サーバから要求されたツール名を、要求元サーバキーの一覧にマッピングする。

---

## 12a. 実行フローのまとめ

**設定の読み込み:** build_agent_config() → ConfigLoader().load_all() reads agent.toml only (_BASE_CONFIG_FILES = ("agent.toml",)). Other configs (crawler.toml, chunk_splitter.toml, ingester.toml, *_mcp_server.toml) loaded separately per process isolation policy.

**ツール実行:** ToolExecutor.execute(tool_name, args) → health gate → cache → raw MCP call.

---

## 13a. インポート境界と設計上の注記

- `shared/` は `agent/`、`mcp_servers/`、`rag/`、`db/` をインポートしてはならない
- `LLMClient` の詳細は本ドキュメント(§10)および [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md) を参照
- `ToolExecutor` の詳細は本ドキュメント(§9)、[04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)、[05_agent_06_01_tool-execution-and-approval-execution.md](05_agent_06_01_tool-execution-and-approval-execution.md) を参照

---

