---
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
  - 90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md
source:
  - 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md
---

# Shared Runtime and Execution Infrastructure

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)

## 9. `ToolExecutor` and Surrounding Concepts (`shared/tool_executor.py`)

**責務:** ツールディスパッチのコアエンジン — ツール→サーバの解決、キャッシュ、同時実行数制限、ヘルスゲーティング、トランスポート通信を担う。

**`ToolCallResult` データクラス(結果の契約、`shared/transport_dto.py`、frozen dataclass):** frozen dataclass with output (truncated if > MCP_MAX_RESPONSE_BYTES), is_error, request_id (X-Request-Id from MCP server, empty for cache hits), server_key (routing target), source ('mcp'/'cache'/empty), error_type ('transport'/'tool'/empty). error_type used by health gate and error counter aggregation.

**実行フロー:** TTL+LRU cache check (success results only); stampede protection shares Future for same-key concurrent calls; resolve tool_name → server_key via ToolRouteResolver; startup_mode=none gate rejects disabled servers; McpServerHealthRegistry.is_unavailable() blocks UNAVAILABLE dispatch (HALF_OPEN allows one attempt per cooldown); lifecycle.ensure_ready() if configured; execute via HttpTransport.call() behind per-server-key semaphore; cache success results only; return ToolCallResult.

**キャッシュの挙動:** Success results only (is_error=False excluded); TTL+LRU eviction configurable via tool_cache_ttl_sec/tool_cache_maxsize; key = (tool_name, serialized_args); side-effect tools fully bypass cache.

**ヘルスゲート:** McpServerHealthRegistry.is_unavailable() blocks dispatch when UNAVAILABLE; consecutive transport failures transition HEALTHY→DEGRADED→UNAVAILABLE (failure_threshold reaches UNAVAILABLE); success response resets to HEALTHY (clears failure count/degraded reason). HALF_OPEN exists as experimental circuit-breaker recovery: after half_open_cooldown_sec in UNAVAILABLE, one dispatch attempt allowed; failure during HALF_OPEN returns immediately to UNAVAILABLE; record_degraded() does not override UNAVAILABLE/HALF_OPEN states.

**同時実行の挙動:** concurrency_limits maps server_key → max concurrent calls; semaphore-based throttling in ToolTransportInvoker; execute_all_tool_calls() serializes entire round when any side-effect tool detected regardless of serial_tool_calls setting.

**副作用の検出:** _SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | {'shell_run'} | GIT_WRITE_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS; is_side_effect(tool_name) checks membership; defined in tool_executor_helpers.py not tool_executor.py; execute_all_tool_calls() in agent/tool_runner.py uses this to switch parallel/serial per-round.

**ルーティング (Explicit in code):** `shared/runtime_tool_registry.py` の `RuntimeToolRegistry` が唯一のルーティング権威(sole routing authority)。`ToolRouteResolver.resolve()`(`shared/route_resolver.py`)は `RuntimeToolRegistry.resolve()` のみを参照し、未知のツールは即座に `ValueError` で失敗する。`shared/tool_registry.py` の `ToolRegistry` はルーティング判断には一切使われず、起動時のドリフト検証(`shared/tool_routing_validation.py`)専用のシードデータに格下げされている。設定ファイルの `tool_names` はドリフト検証専用のメタデータであり、実行時のルーティング判断には使われない。旧「2段カスケード」方式(ライブ検出→レジストリの順で解決)は現行コードには存在しない。ルーティングの詳細は [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md) を参照。

---
