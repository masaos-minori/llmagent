---
title: "5. Constraints Reference"
area: rag
tags:
  - rag
  - configuration
related:
  - 03_rag_00_document-guide.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_05_1-configuration-reference.md
---


# 5. Constraints Reference

| Constraint | Value |
|---|---|
| Language detection threshold | CJK ratio $\ge$ 0.10 $\rightarrow$ `ja`; If page < 100 chars $\rightarrow$ use hint language |
| Chunk size range | 40–500 characters (Configurable via `min_chunk`/`max_chunk` in `config/chunk_splitter.toml`) |
| Chunk overlap | 50 character sliding window (`config/chunk_splitter.toml:chunk_overlap`) |
| Embedding dimensions | 384 (`config/agent.toml:embedding_dims`, and `config/ingester.toml:embedding_dims`). float32 little-endian BLOB |
| Crawl depth | Code default requires `max_depth` to be specified (`config/crawler.toml` is mandatory). Operational `config/crawler.toml` uses `max_depth = 3` |
| Max crawl pages | Code default is 500 pages per site (`crawler.py` uses `cfg.get("max_pages", 500)`). Operational `config/crawler.toml` uses `max_pages = 200` |
| Replication | Single-node SQLite only |

**Evidence:**
- CJK threshold, character count threshold, chunk size/overlap, embedding dims/endianness: Explicit in code (`scripts/rag/ingestion/crawler_utils.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/utils.py:floats_to_blob`, `config/agent.toml`, `config/ingester.toml`).
- Crawl depth and max pages: Explicit in code, but operational values in `config/crawler.toml` differ from code defaults. Previous versions stated "`config/agent.toml:43`", "max 6 hops", and "max 500 pages", but in the current `config/agent.toml`, `embedding_dims` is on line 17, and actual `config/crawler.toml` values are `max_depth=3` and `max_pages=200`. Line number references are deprecated; use section-based references instead.

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- [03_rag_05_7-rag-index-consistency-checks.md](03_rag_05_7-rag-index-consistency-checks.md)

## Keywords

configuration
constraints
chunking
embedding-dims
