---
title: "Memory Layer — Module Reference"
category: agent
tags:
  - agent
  - agent
  - memory
  - semantic
  - episodic
  - embedding
related:
  - 05_agent_00_document-guide.md
---

# Memory Layer — Module Reference

ivation Gate](#activation-gate) section and [Disabled Behavior by Module](#disabled-behavior-by-module) table above for the full per-module breakdown.

Summary:
- `use_memory_layer=False` → `ctx.services.memory` is `None`; all memory operations are skipped
- `EmbeddingClient.enabled=False` → `fetch()` returns `DISABLED` error; retrieval falls back to FTS5-only
- `cli_view.py` reflects memory layer status at startup banner

---

## Related Documents

- Runtime ar

chitecture: [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
- Configuration: [05_agent_08_configuration.md](05_agent_08_configuration.md)