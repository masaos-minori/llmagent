---
title: "Long-Running HTTP Operation (startup_mode=subprocess)"
area: mcp
tags:
  - mcp
  - startup-modes
  - subprocess
related:
---
# Long-Running HTTP Operation (startup_mode=subprocess)

At startup, the Agent starts uvicorn and polls `/health` every 0.5 seconds until `startup_timeout_sec` is reached. If the health check never succeeds, a `RuntimeError` is raised.

The handling of this `RuntimeError` differs depending on the `security_profile` (`SecurityProfile` in `scripts/shared/mcp_config.py`). If `security_profile=production`, after one retry (with a delay defined by `HEALTH_CHECK_RETRY_DELAY_SEC`), if it still fails, the `RuntimeError` is propagated without being caught, causing the entire Agent process to terminate. If `security_profile=local`, the same failure is only logged and displayed as a warning; the specific server is disabled, but the Agent process and other MCP servers continue to operate. The health check itself originates from the `/health` polling in `scripts/agent/http_lifecycle.py` (`HttpStartupError`), and `scripts/agent/startup.py` applies the aforementioned `security_profile`-dependent branching.

---

## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
