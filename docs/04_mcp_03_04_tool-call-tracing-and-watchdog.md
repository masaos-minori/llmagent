---
title: "Transport Error Tracing and Lifecycle Flow"
category: mcp
tags:
  - mcp
  - tracing
  - lifecycle
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_01_dispatch-and-routing.md
  - 04_mcp_03_02_tool-registry.md
  - 04_mcp_03_03_transport-and-health-part1.md
  - 04_mcp_03_03_transport-and-health-part2.md
  - 04_mcp_03_05_lifecycle-and-new-server.md
  - 04_mcp_06_12_watchdog-configuration-monitoring.md
---

# トランスポートエラー追跡とライフサイクルフロー

> **注記:** 本ドキュメントのファイル名には歴史的経緯により `watchdog` の語が残っているが、
> MCP watchdog(自動ヘルスポーリング・自動再起動ループ)は2026-07-16に削除された。
> 詳細は [04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md) を参照。

### 失敗パスの例（トランスポートエラー）

```
1-2. Same as above.

3. MCP server unreachable (timeout / 5xx):
   HttpTransport raises TransportError.

4. Agent:
   Transport error handler records the error for "file_read"
   → stat_transport_errors["file_read"] += 1
   → HealthRegistry.record_failure("file_read") → state: HEALTHY → DEGRADED

5. ToolCallResult:
   (output=str(error), is_error=True, server_key="file_read", error_type="transport")

6. audit_tool_exec():
    audit log (JSON-lines): {"event":"tool_exec","task_id":"...","tool":"read_text_file","mcp_request_id":"","is_error":true,"error_type":"transport","ts":...}
    Note: mcp_request_id="" because no response was received.

7. Next real tool call to "file_read" (ToolExecutor._raw_execute):
   ensure_ready() attempts recovery (subprocess mode only), then dispatch proceeds.
   → if the call succeeds: HealthRegistry.record_success("file_read") → HALF_OPEN → HEALTHY
   → if it fails again: HealthRegistry.record_failure("file_read") → DEGRADED → UNAVAILABLE
   No background poller retries this automatically; see
   04_mcp_06_12_watchdog-configuration-monitoring.md for the removed watchdog.
```

---

### 追跡におけるツールエラーとトランスポートエラーの違い

| フィールド | ツールエラー | トランスポートエラー |
|---|---|---|
| `is_error` | `True` | `True` |
| `error_type` | `"tool"` | `"transport"` |
| `mcp_request_id` | 設定される（サーバーが応答した） | `""`（レスポンスを受信していない） |
| `HealthRegistry` | `record_success()`（サーバーが応答した） | `record_failure()`（サーバーに到達不可） |
| `stat_tool_errors` | インクリメントされる | 変化なし |
| `stat_transport_errors` | 変化なし | インクリメントされる |

ツールエラーとは、サーバーがリクエストを処理したがエラーを返したことを意味する。
トランスポートエラーとは、エージェントがサーバーからのレスポンスを一度も受信しなかったことを意味する。

運用上の追跡手順については [04_mcp_06 §End-to-End Tool Call Tracing](04_mcp_06_08_end-to-end-tool-call-tracing.md#end-to-end-tool-call-tracing) を参照。

---

## ライフサイクルフロー

ツール定義の起動時バリデーション動作については `04_mcp_06` §Startup Validation Behavior を参照。

```
AgentREPL.run()
  → MCP server startup
       → startup_mode="subprocess" (http): start_http_subprocess() + health poll
            stderr → /opt/llm/logs/mcp_servers/{server_key}.stderr.log (append mode)
       → startup_mode="persistent" (http): no lifecycle action needed
       → startup_mode="none": no subprocess spawn, no health check — server is disabled
   → [REPL loop]
   → tool call → ToolExecutor raw execute
         → startup_mode="none" rejects immediately
              with a "disabled" tool error, before health check or transport
             → ensure_ready(server_key):
                  if _shutting_down: return immediately (shutdown guard)
                  if subprocess-mode and not running: start() [auto-restart on demand]
   → finally: lifecycle.shutdown_all()
                  sets _shutting_down=True (blocks further start/restart calls)
                + close stderr log file handles
                + AsyncClient.close()
```

`_ServerLifecycleRouter._shutting_down` は `ensure_ready()`, `start_http_subprocess()`,
`restart()`, `shutdown_idle()` を保護する: `shutdown_all()` が呼び出された後は、これらのメソッドは
ログ行を出力して即座にリターンし、`HttpServerLifecycleManager` への委譲は行わない。

### 実装上の補足(二重 SIGINT ガード)

`HttpServerLifecycleManager.shutdown_all()`(`agent/http_lifecycle.py`)は、クリーンアップ実行中にシグナルハンドラを一時的に `_absorb_sigint_during_shutdown()` に差し替え、後続の SIGINT を WARNING ログのみで吸収する(メインスレッド以外で呼ばれた場合は `signal.signal()` が `ValueError` を送出するため、ガードなしで続行する)。ユーザーが Ctrl-C を connectionを待っている間に2回押してループを中断し、残存サブプロセスが孤児化することを防ぐ意図。クリーンアップ完了後に元のハンドラへ復元する。(Explicit in code)

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_03_01_dispatch-and-routing.md`
- `04_mcp_03_02_tool-registry.md`
- `04_mcp_03_03_transport-and-health-part1.md`
- `04_mcp_03_03_transport-and-health-part2.md`
- `04_mcp_03_05_lifecycle-and-new-server.md`
- `04_mcp_06_12_watchdog-configuration-monitoring.md`

## Keywords

mcp
tool error
transport error
lifecycle flow
health check
restart
