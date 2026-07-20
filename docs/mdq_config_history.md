---
title: "MDQ Config: Removed Key History"
category: mcp
tags:
  - mcp
  - mdq
  - config
  - history
related:
  - 04_mcp_04_04_mdq.md
---

# MDQ Config: Removed Key History

This document is a historical record of config keys that were once part of
`config/mdq_mcp_server.toml` and have since been removed. It exists so that
anyone who finds a stale reference to one of these keys, or wonders why it is
no longer in the active config file, can find the rationale and removal date
here. `config/mdq_mcp_server.toml` itself now carries only a short pointer
comment to this document; this file preserves the full historical detail.

## `audit_log_path` (removed 2026-07-13)

`audit_log_path` was removed (2026-07-13). `MdqService.audit_log_path` was
parsed but never subsequently read -- audit events are emitted via `_audit_log()`
into the standard mdq-mcp.log app logger (JSON-lines), not a dedicated file at
this path. See `docs/04_mcp_06_07_reading-audit-logs.md`. Re-add only alongside an
implementation that actually opens and writes to this path.

## `concurrency_limit` (removed 2026-07-13)

`concurrency_limit` was removed (2026-07-13). It was never read anywhere in
`scripts/mcp_servers/mdq/` -- index/refresh serialization is instead achieved via a
fixed internal `asyncio.Lock` (`MdqService._index_lock`), independent of any config
value (see `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`). Re-add only
alongside an implementation that actually reads it.

## `max_search_results` (removed 2026-07-16)

`max_search_results` was removed (2026-07-16). It was parsed but never read
anywhere in `scripts/mcp_servers/mdq/` -- `max_results_limit` is the sole enforced
result-count key (see `docs/04_mcp_04_04_mdq.md`). Re-add only alongside an
implementation that actually reads this key.

## `use_embedding`, `embedding_dims`, `vector_table`, `embedding_model` (removed 2026-07-16)

`use_embedding`, `embedding_dims`, `vector_table`, and `embedding_model` were
removed (2026-07-16). Hybrid/semantic search was never functionally implemented
-- `_search_vector()` in `search.py` always returned an empty list. FTS5 (BM25) is
the only supported search mode; use the RAG pipeline (`rag-pipeline-mcp`) for
semantic search. See `docs/04_mcp_04_04_mdq.md` and
`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`. Re-add only alongside a real
embedding-search implementation.

## `summary_cache_enabled`, `summary_threshold`, `summary_model` (removed 2026-07-16)

`summary_cache_enabled`, `summary_threshold`, and `summary_model` were
removed (2026-07-16). The summary-cache feature never generated a real
summary -- `_generate_and_cache_summary()` always returned `None` for the only
supported `summary_model` value (`"default"`), and the indexer wrote a
truncated verbatim copy of the raw chunk content into `chunk_summaries`, not
an actual summary. `get_chunk()` now always returns raw (optionally
truncated) content. See `docs/04_mcp_04_04_mdq.md`. Re-add only alongside a
real LLM-based summarization implementation.

## `enable_refresh` (removed 2026-07-16)

`enable_refresh` was removed (2026-07-16). It was parsed but never
enforced -- `refresh_index()` had no gate check on it and always ran
regardless of this flag's value. Index/refresh serialization (a separate
concern) is achieved via `MdqService._index_lock`, independent of any config
value. See `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`. Re-add only
alongside an implementation that actually reads and enforces it.

## `status` (removed 2026-07-17)

`status` was removed (2026-07-17). It was a free-text label (`"production"`)
never read by `MdqService` or any other Python code in `scripts/mcp_servers/mdq/` --
`tools.py`'s per-tool `"status": "production"` strings are unrelated hardcoded
tool-metadata literals, not derived from this config key. Re-add only
alongside an implementation that actually reads and acts on this value.
