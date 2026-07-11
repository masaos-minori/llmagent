---
title: "MCP Failure Diagnosis"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
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
   YES → See §Watchdog Behavior. Check health transition timestamp.
   NO  → continue

4. Has the watchdog taken action (restart / circuit-break)?
   YES → See §Watchdog Behavior.
   NO  → Check serialization. See §Serialization in Tool Execution.
```

agent、transport、サーバのログを横断した相関分析については §End-to-End Tool Call Tracing を参照。

#### Tool dispatch時のensure ready動作

`_raw_execute()` パス経由でtool callが到着した場合:

```python
# In shared/tool_executor.py ensure_ready():
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

つまり、watchdogが自動再起動を諦めた後（max_restartsを超えた後）であっても、
まだ自身のcircuit-breakの閾値に達していない個々のtool callは、`ensure_ready()` を通じて
回復を試みることができる。

---

**再起動が妥当なケース:** ヘルス状態が `FAILED` に遷移＋閾値内でのtransportエラーの繰り返し、または
subprocessクラッシュ後の `ensure_ready()` の成功。

**再起動が妥当でないケース:** 単発のtoolエラー、一度限りのタイムアウト、直列化による遅延。

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
