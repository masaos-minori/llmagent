---
title: "Long-Running HTTP Operation (startup_mode=subprocess)"
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

# Long-Running HTTP Operation (startup_mode=subprocess)

Agentは起動時にuvicornを起動し、`startup_timeout_sec` まで1秒ごとに `/health` をポーリングする。
ヘルスチェックが一度も成功しない場合は `RuntimeError` となる。

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
