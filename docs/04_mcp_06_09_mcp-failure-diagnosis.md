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

Use this flow to trace a failed or unexpected MCP tool call:

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

For correlation across agent, transport, and server logs, see §End-to-End Tool Call Tracing.

#### Ensure ready behavior during tool dispatch

When a tool call arrives via `_raw_execute()` path:

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

This means that even when the watchdog has given up on auto-restart (after exceeding max_restarts), individual tool calls can still attempt recovery through `ensure_ready()`, provided they haven't triggered their own circuit-break thresholds yet.

---

**Restart-worthy:** health transition to `FAILED` + repeated transport errors within threshold OR successful `ensure_ready()` after sub-process crash.

**Not restart-worthy:** single tool error, one-time timeout, or serialization delay.

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
