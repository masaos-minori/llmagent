---
title: "Shared Runtime and Execution - Caching and Reference (Part 2)"
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

## 17. `McpServerHealthState` / `McpServerHealthRegistry` (`shared/mcp_health.py`)

Enum for MCP server health states: HEALTHY (normal operation), DEGRADED (failing but not yet unavailable), UNAVAILABLE (circuit breaker open), HALF_OPEN (experimental probe after cooldown), UNKNOWN (unregistered key returns HEALTHY default, UNKNOWN never observed in practice).

Per-server health tracking for ToolExecutor dispatch gating. Constructor accepts failure_threshold (default 3 consecutive failures → UNAVAILABLE) and half_open_cooldown_sec (default 30s). Methods: record_failure() transitions HEALTHY→DEGRADED→UNAVAILABLE; record_degraded() records watchdog reachability probes (does not override UNAVAILABLE/HALF_OPEN); record_restart_exhausted() tags degraded reason as 'restart_limit_reached'; record_success() resets to HEALTHY plus clears failure counts/degraded reasons; get_state() returns current state; is_unavailable() handles UNAVAILABLE→HALF_OPEN transition on cooldown expiry.

State transitions: HEALTHY→DEGRADED on first failure; DEGRADED→UNAVAILABLE on failure_threshold consecutive failures (default 3); UNAVAILABLE→HALF_OPEN after half_open_cooldown_sec (default 30s, experimental probe); HALF_OPEN→UNAVAILABLE on probe failure (cooldown resets); HALF_OPEN→HEALTHY on probe success; any state→HEALTHY on successful response.

**[Explicit in code — 追加]** get_state() returns HEALTHY default for unregistered keys (UNKNOWN never observed). record_degraded() does not override UNAVAILABLE/HALF_OPEN states (intentional guard against breaking circuit breaker/trial window). record_restart_exhausted() does not change state (assumes record_failure() already set UNAVAILABLE), only tags degraded reason. record_success() resets _failure_counts/_unavailable_since/_degraded_reasons (prevents immediate re-UNAVAILABLE on next failure due to stale counts).

---

## 18. `LlmPayloadHandler` (`shared/llm_payload.py`)

All methods are `@staticmethod`. build_payload() takes history (list[LLMMessage]), tool_defs (list[dict]), temperature (float, required), max_tokens (int, required), stream (bool, default False) — returns payload with messages/tools/tool_choice="auto"/temperature/max_tokens, adds "stream": True when stream=True. parse_response() accepts raw parsed JSON dict (not httpx.Response), validates choices/message structure, raises ValueError on invalid input, delegates usage parsing to LlmSseHelpers.parse_usage(). parse_non_stream_response() is a third method (not in old docs): decodes bytes via orjson.loads(), raises ValueError if not dict, then delegates to parse_response().

on_usage parameter is Callable[[int, int], None] | None, called from LlmSseHelpers.parse_usage() as on_usage(prompt_tokens, completion_tokens). Only production caller is scripts/agent/factory.py's _on_llm_usage.

---

## 19. `LlmHotConfigHandler` (`shared/llm_hot_config.py`)

Manages hot-reloadable config fields for LLMClient. HOT_CONFIG_FIELDS is a tuple of (instance_attr_name, kwarg_name) pairs covering 9 fields: temperature, max_tokens, max_retries, retry_base_delay, sse_heartbeat_timeout, sse_malformed_retry, sse_reconnect_max, stream_retry_on_heartbeat_timeout, stream_retry_on_malformed_chunk. apply_one() sets a single field via setattr. apply_config() accepts keyword-only args, applies only non-None values (partial update, unspecified items unchanged).

---

## 20. AI リファレンスガイド

| 質問 | 回答 |
|---|---|
| 設定ファイルの読み込み方法 | `ConfigLoader().load("filename.toml")` または `load_all()` |
| 設定オーナーシップ表 | **§2a 設定オーナーシップを参照** — プロセス分離方針とプロセスごとの設定ファイル一覧の正式なリファレンス |
| `load_all()` は `agent.toml` を含むか? | **含む(それのみ)** — `_BASE_CONFIG_FILES = ("agent.toml",)` の1件のみで、他の設定ファイル(crawler.toml等)は各プロセスが個別にロードする (§2a 設定オーナーシップを参照) |
| ToolExecutor がキャッシュを使うのはいつか? | `is_error=False` の結果のみ; TTL + LRU。ただし `ToolExecutor` は `shared/tool_cache.py` の `ToolResultCache`（standalone utility, not used by ToolExecutor）ではなく、`shared/tool_executor.py` 内の自前の `OrderedDict` ベースキャッシュ (`_execute_with_cache()`) を使う (§15 を参照) |
| `git_helper.get_repo_info()` は信頼できるか? | `RepoInfoResult` を返す; `.success` と `.failure_reason` (FailureReason enum) を確認すること |
| 正確なトークン数を取得する方法 | `await get_token_count(history, tokenize_url, http)` |
| LLM の再試行はどう動くか? | 指数バックオフ: 429/503 および接続エラー時に `retry_base_delay * (2**attempt)` |
| ToolExecutor のキャッシュキー形式は? | `{tool_name}:{json_dumps(args)}` (`shared.json_utils.dumps` を使用) |
| ヘルスゲートの状態遷移は? | HEALTHY → DEGRADED → UNAVAILABLE → HALF_OPEN → HEALTHY/UNAVAILABLE (§17 を参照)。`UNKNOWN` 状態も定義されているが `get_state()` の既定値は `HEALTHY` |


