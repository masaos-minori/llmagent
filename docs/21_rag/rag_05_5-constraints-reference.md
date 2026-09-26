---
title: "5. Constraints Reference"
area: rag
tags:
  - rag
  - configuration
related:
  - rag_00_document-guide.md
  - rag_05_1-configuration-reference.md
source:
  - rag_05_1-configuration-reference.md
---


# 5. Constraints Reference

| Constraint | Value |
|---|---|
| Language detection threshold | CJK ratio $\ge$ 0.10 $\rightarrow$ `ja`; If page < 100 chars $\rightarrow$ use hint language |
| Chunk size range | Bounded to keep each chunk within a useful retrieval granularity — not so small it is noise, not so large it dilutes relevance. Current operational value in [Configuration Reference §1.2](rag_05_1-configuration-reference.md). Rationale for the specific bounds tracked as unresolved in NC-034 (`docs/governance_03_issue-and-uncertainty-management.md`). |
| Chunk overlap | Preserves context continuity across chunk boundaries by including a trailing slice of the previous chunk. Current operational value in [Configuration Reference §1.2](rag_05_1-configuration-reference.md). Rationale tracked as unresolved in NC-034. |
| Embedding dimensions | Fixed code-level constant (`scripts/db/store_protocols.py::get_embedding_dims()`), not config-driven. float32 little-endian BLOB |
| Crawl depth | Bounds BFS traversal depth to prevent unbounded crawl time and external-site load. Current operational value in [Configuration Reference §1.1](rag_05_1-configuration-reference.md). Rationale for the specific limit tracked as unresolved in NC-035. |
| Max crawl pages | Bounds crawl scope per site to prevent unbounded processing time and storage growth. Current operational value in [Configuration Reference §1.1](rag_05_1-configuration-reference.md). Rationale for the specific limit tracked as unresolved in NC-035. |
| Replication | Single-node SQLite only |
| `chunk_index` type constraint | Non-negative `int`; `bool` is explicitly rejected before the `int` check (`_validate_int_non_negative`) — no implicit conversion from strings or booleans |
| `url` non-empty requirement | Required non-empty string for both crawl and chunk artifacts (`_validate_str`); no fallback |
| `content` non-empty requirement | Chunk artifacts: required non-empty string (`_validate_str`), no exception. Crawl artifacts: empty string allowed only when `code_blocks` is non-empty (cross-field rule) |
| `lang` validation scope | Any non-empty string accepted at parse time (`_validate_str`); the `en`/`ja` value set defined by `LanguageCode` (`scripts/rag/enums.py`) is a convention only, not enforced by either reader (Needs confirmation: whether parse-time enforcement is intended) |
| `chunking_strategy` validation scope | Any non-empty string accepted at parse time (`_validate_str`); the `"text"`/`"heading"` value set is a convention only, not enforced in code (Needs confirmation: whether a closed value set is intended) |

**Evidence:**
- CJK threshold, character count threshold, chunk size/overlap, embedding dims/endianness: Explicit in code (`scripts/rag/ingestion/crawler_utils.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/utils.py:floats_to_blob`, `config/agent.toml`, `config/ingester.toml`).
- Crawl depth and max pages: Explicit in code, but operational values in `config/crawler.toml` differ from code defaults. Previous versions stated "`config/agent.toml:43`", "max 6 hops", and "max 500 pages", but in the current `config/agent.toml`, `embed_url` is on line 10, and actual `config/crawler.toml` values are `max_depth=3` and `max_pages=200`. Line number references are deprecated; use section-based references instead.
- `chunk_index`/`url`/`content` validation, `lang`/`chunking_strategy` non-enforcement: Explicit in code
  (`scripts/rag/ingestion/pipeline_utils.py:53-97` validator definitions, `:100-233`
  `read_crawl_json()`/`read_chunk_json()` call sites); `LanguageCode`'s `en`/`ja`
  members are defined in `scripts/rag/enums.py` but never referenced by either reader.

---


## Related Documents

- [rag_05_1-configuration-reference.md](rag_05_1-configuration-reference.md)
- [rag_05_7-rag-index-consistency-checks.md](rag_05_7-rag-index-consistency-checks.md)

## Keywords

configuration
constraints
chunking
embedding-dims
