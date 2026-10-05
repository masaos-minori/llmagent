---
title: "Long-Running HTTP Operation (startup_mode=subprocess)"
area: mcp
tags:
  - mcp
  - startup-modes
  - subprocess
related:
  - mcp_06_02_configuration-file-inventory.md
---
# Long-Running HTTP Operation (startup_mode=subprocess)

At startup, the Agent starts uvicorn and polls `/health` every 0.5 seconds until `startup_timeout_sec` is reached. If the health check never succeeds, a `RuntimeError` is raised.

On failure, `McpServerStarter` (`scripts/agent/startup_mcp_starter.py`) retries once after a fixed delay (`RETRY_DELAY_SEC`, via `agent/shared/retry_helper.py::retry_once_with_delay()`). If the second attempt also fails, a `RuntimeError` with the `[fatal]` prefix is raised and startup is aborted; this behavior does not depend on `security_profile` (`SecurityProfile` has only a `PRODUCTION` member). The health check itself originates from the `/health` polling in `scripts/agent/http_lifecycle.py` (`HttpStartupError`).

---

## Keywords

configuration
