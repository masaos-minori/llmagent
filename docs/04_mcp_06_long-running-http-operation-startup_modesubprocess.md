---
title: "Long-Running HTTP Operation (startup_mode=subprocess)"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_configuration_and_operations.md
source:
  - 04_mcp_06_configuration_and_operations.md
---

# Long-Running HTTP Operation (startup_mode=subprocess)

## Long-Running HTTP Operation (startup_mode=subprocess)

Agent spawns uvicorn at launch, polls `/health` every 1 second up to `startup_timeout_sec`.
`RuntimeError` if health check never succeeds.

---


## Related Documents

- [04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration-file-inventory.md)

## Keywords

configuration
