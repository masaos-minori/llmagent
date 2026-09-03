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
| Embedding dimensions | Fixed code-level constant (`scripts/db/store_protocols.py::get_embedding_dims()`), not config-driven. float32 little-endian BLOB |
| Crawl depth | Code default requires `max_depth` to be specified (`config/crawler.toml` is mandatory). Operational `config/crawler.toml` uses `max_depth = 3` |
| Max crawl pages | Code default is 500 pages per site (`crawler.py` uses `cfg.get("max_pages", 500)`). Operational `config/crawler.toml` uses `max_pages = 200` |
| Replication | Single-node SQLite only |
| `chunk_index` type constraint | Non-negative `int`; `bool` is explicitly rejected before the `int` check (`_validate_int_non_negative`) — no implicit conversion from strings or booleans |
| `url` non-empty requirement | Required non-empty string for both crawl and chunk artifacts (`_validate_str`); no fallback |
| `content` non-empty requirement | Chunk artifacts: required non-empty string (`_validate_str`), no exception. Crawl artifacts: empty string allowed only when `code_blocks` is non-empty (cross-field rule) |
| `lang` validation scope | Any non-empty string accepted at parse time (`_validate_str`); the `en`/`ja` value set defined by `LanguageCode` (`scripts/rag/enums.py`) is a convention only, not enforced by either reader (Needs confirmation: whether parse-time enforcement is intended) |

**Evidence:**
- CJK threshold, character count threshold, chunk size/overlap, embedding dims/endianness: Explicit in code (`scripts/rag/ingestion/crawler_utils.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/utils.py:floats_to_blob`, `config/agent.toml`, `config/ingester.toml`).
- Crawl depth and max pages: Explicit in code, but operational values in `config/crawler.toml` differ from code defaults. Previous versions stated "`config/agent.toml:43`", "max 6 hops", and "max 500 pages", but in the current `config/agent.toml`, `embed_url` is on line 10, and actual `config/crawler.toml` values are `max_depth=3` and `max_pages=200`. Line number references are deprecated; use section-based references instead.
- `chunk_index`/`url`/`content` validation, `lang` non-enforcement: Explicit in code
  (`scripts/rag/ingestion/pipeline_utils.py:53-97` validator definitions, `:100-233`
  `read_crawl_json()`/`read_chunk_json()` call sites); `LanguageCode`'s `en`/`ja`
  members are defined in `scripts/rag/enums.py` but never referenced by either reader.

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- [03_rag_05_7-rag-index-consistency-checks.md](03_rag_05_7-rag-index-consistency-checks.md)

## Keywords

configuration
constraints
chunking
embedding-dims
