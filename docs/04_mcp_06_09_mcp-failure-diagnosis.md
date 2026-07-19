---
title: "MCP Failure Diagnosis"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
  - 04_mcp_06_12_watchdog-configuration-monitoring.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# MCP Failure Diagnosis

## MCP Failure Diagnosis

失敗した、または予期しないMCP tool callを追跡するには、以下のフローを使用する:

```
1. Was the request delivered to the server?
   NO  → Transport failure (error_type="transport" in agent-side audit log). See §Error Type Distinction.
   YES → continue

2. Did the tool return an error response (is_error=true)?
   YES → Tool-level error (error_type="tool" in agent-side audit log). See §Error Type Distinction.
   NO (timeout or silent fail) → continue

3. Has server health status changed?
   YES → Check `/mcp status` for the current DEGRADED/UNAVAILABLE state and health_reason.
   NO  → continue

4. Has the circuit breaker tripped (UNAVAILABLE)?
   YES → No automatic restart will happen (the MCP watchdog was removed on 2026-07-16;
         see 04_mcp_06_12_watchdog-configuration-monitoring.md). Manual recovery required —
         either wait for the next tool call to trigger ensure_ready(), or restart the
         server/agent process manually.
   NO  → Check serialization. See §Serialization in Tool Execution.
```

agent、transport、サーバのログを横断した相関分析については §End-to-End Tool Call Tracing を参照。

#### Tool dispatch時のensure ready動作

内部ディスパッチパス経由でtool callが到着した場合:

```python
# In agent/factory.py _ServerLifecycleRouter.ensure_ready():
if _shutting_down: return immediately          # shutdown guard
cfg.transport != HTTP or cfg.startup_mode != SUBPROCESS: return immediately  # non-subprocess servers skip this check
not http_mgr.verify_running(server_key):      # subprocess-mode, not running -> start!
    set_state(LifecycleState.STARTING)         # optimistic state before starting
    await http_mgr.start(server_key, cfg)       # spawn subprocess, poll /health
    set_state(LifecycleState.RUNNING)           # success
except Exception:                               # any startup failure
    set_state(LifecycleState.FAILED)           # mark as failed for subsequent attempts
    raise                                       # propagate up so caller sees the failure
```

つまり、サーバーが繰り返しクラッシュしていても、まだ自身のcircuit-breakの閾値に
達していない個々のtool callは、`ensure_ready()` を通じて回復を試みることができる。
これが現在唯一の自動復旧経路である（旧MCP watchdogによる周期的なポーリング＋自動再起動は
2026-07-16に削除された。[04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md)参照）。

> **実装上の補足 (Explicit in code):** `ensure_ready()` は `shared/tool_executor.py` にはなく、
> `agent/factory.py` の `_ServerLifecycleRouter` クラスに実装されている。実際のsubprocess起動/停止は
> `agent/http_lifecycle.py` の `HttpServerLifecycleManager` に委譲される。`ToolExecutor` は
> `LifecycleProtocol`(`shared/tool_lifecycle.py`)経由でこのルータを呼び出すのみで、起動ロジック自体は持たない。

---

**再起動が妥当なケース:** ヘルス状態が `FAILED` に遷移＋閾値内でのtransportエラーの繰り返し、または
subprocessクラッシュ後の `ensure_ready()` の成功。

**再起動が妥当でないケース:** 単発のtoolエラー、一度限りのタイムアウト、直列化による遅延。

#### Tool実行層のcircuit breaker（`McpServerHealthRegistry`）

`shared/mcp_health.py` の `McpServerHealthRegistry` は、サーバーごとの
連続失敗をトラッキングしディスパッチをゲートする独立したcircuit breakerである。

- `record_failure()` は失敗カウントをインクリメントし、`failure_threshold`(デフォルト3)に達すると
  状態を `UNAVAILABLE` にする。
- `is_unavailable()` は単なるgetterではない。`UNAVAILABLE` になってから
  `half_open_cooldown_sec`(デフォルト30秒)経過すると、呼び出し側に気づかれないまま状態を
  `HALF_OPEN`（1回だけ試行を許可する窓）へ遷移させ、その呼び出しでは `False` を返す。
- `HALF_OPEN` 中の失敗は即座に `UNAVAILABLE` に戻り、cooldownがリセットされる。
- `record_success()` は状態を `HEALTHY` に戻し、失敗カウント・degraded理由をクリアする。

根拠: Explicit in code（`shared/mcp_health.py`）。`ToolExecutor` の実行処理内の
ヘルスチェックがディスパッチ前のゲートとしてこの機構を参照する。


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)
- [04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md)

## Keywords

configuration
