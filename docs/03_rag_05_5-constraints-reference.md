---
title: "5. Constraints Reference"
category: rag
tags:
  - rag
  - configuration
related:
  - 03_rag_00_document-guide.md
  - 03_rag_05_configuration_and_operations.md
source:
  - 03_rag_05_configuration_and_operations.md
---

# 5. Constraints Reference

## 5. Constraints Reference

| Constraint | Value |
|---|---|
| Language detection threshold | CJK ratio ≥ 0.10 → `ja`; pages < 100 chars → use hint language |
| Chunk size range | 40–500 chars (configurable) |
| Chunk overlap | 50 chars sliding window |
| Embedding dimension | 384 (production, `config/agent.toml:43`). float32 little-endian BLOB |
| Crawl depth | max 6 hops |
| Crawl page limit | max 500 pages/site |
| Replica | Single-node SQLite only |

---


## Related Documents

- [03_rag_05_configuration_and_operations.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
