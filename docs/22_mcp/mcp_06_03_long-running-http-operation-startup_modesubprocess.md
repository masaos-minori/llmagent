---
title: "Long-Running HTTP Operation (startup_mode=subprocess)"
area: mcp
tags:
  - mcp
  - startup-modes
  - subprocess
related:
  - mcp_06_01_configuration-file-inventory.md
---
# Long-Running HTTP Operation (startup_mode=subprocess)

At startup, the Agent starts uvicorn and polls `/health` periodically until `startup_timeout_sec` is reached. If the health check never succeeds, a `RuntimeError` is raised.

On failure, `McpServerStarter` (`scripts/agent/startup_mcp_starter.py`) retries once after a fixed delay (`RETRY_DELAY_SEC`, via `agent/shared/retry_helper.py::retry_once_with_delay()`). If the second attempt also fails, an error with the `[fatal]` prefix is raised and startup is aborted. This applies to every subprocess server regardless of `required` (the spawn and post-start health-check paths in `McpServerStarter` do not read `required`), and does not depend on `security_profile` (`SecurityProfile` has only a `PRODUCTION` member). The health check itself originates from the `/health` polling in `scripts/agent/http_lifecycle.py` (`HttpStartupError`) (Explicit in code — `scripts/agent/startup_mcp_starter.py::McpServerStarter.start_servers`, `scripts/agent/startup.py::StartupOrchestrator.run`).

The `required` flag takes effect later, at live `/v1/tools` discovery (`scripts/agent/services/mcp_tool_discovery.py`): an unreachable `required=true` server is FATAL, while an unreachable `required=false` server is a WARNING, is disabled, and startup continues (see [mcp_06_09](mcp_06_09_startup-validation-behavior-tool_definitions_strict.md)). A `required=false` subprocess server that fails to start is therefore not reached by that rule, because the subprocess phase aborts first.

---

## Keywords

configuration
