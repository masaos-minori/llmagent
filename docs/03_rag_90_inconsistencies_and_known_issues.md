# RAG Inconsistencies and Known Issues

This file catalogs known bugs, spec conflicts, document inconsistencies, and open questions
discovered during the restructuring of RAG documentation.

Each entry uses: Type / Impact / Description / Safe interpretation / Recommended action / Source.

---

## Implementation Bugs

### BUG-1: `chunking_strategy` field lost in ingester

- **Type:** BUG
- **Impact scope:** `scripts/rag/ingestion/ingester.py`, `documents` table
- **Description:** `_read_chunk_json()` uses `dataclasses.asdict(read_json_file(path))`.
  `read_json_file()` returns a `ChunkDocument` dataclass, which does not declare
  `chunking_strategy`. Fields not in the dataclass definition are silently dropped.
  Result: `chunking_strategy` is always written as `'text'` (default) regardless of
  the actual chunk strategy. (`ingester.py:94`)
- **Current safe interpretation:** `documents.chunking_strategy` is unreliable; always `'text'`.
- **Recommended action:** Replace `_read_chunk_json()` with `orjson.loads(path.read_bytes())`
  to read the raw JSON dict, bypassing the dataclass conversion. (`ingester.py:237-245`)
- **Source reference:** `03_spec_rag.md §13`
- **Notes for AI:** Do not rely on `documents.chunking_strategy` for logic until this is fixed.

---

### BUG-2: `normalized_content` hardcoded to None in ingester

- **Type:** BUG
- **Impact scope:** `scripts/rag/ingestion/ingester.py`, `chunks` table, FTS5 search quality
- **Description:** Same root cause as BUG-1. `normalized_content` (Sudachi normalized text)
  is present in the chunk JSON file but is not a field in `ChunkDocument`, so it is dropped
  by `dataclasses.asdict()`. The ingester writes `normalized_content = None` for all chunks
  regardless of language. (`ingester.py:255`)
  Consequence: `chunks_fts` indexes `content` (original text) instead of normalized forms
  for Japanese chunks. FTS5 Japanese search quality degrades — Sudachi normalization
  is effectively bypassed.
- **Current safe interpretation:** Japanese FTS5 search uses raw text, not normalized forms.
  Expect degraded recall for morphological variants.
- **Recommended action:** Same fix as BUG-1 (`orjson.loads` in `_read_chunk_json()`).
- **Source reference:** `03_spec_rag.md §13`
- **Notes for AI:** `/rag search` results for Japanese queries are affected. This is a known
  quality issue, not a system failure.

---

### BUG-3: `chunk_index` always 0 in ingester

- **Type:** BUG
- **Impact scope:** `scripts/rag/ingestion/ingester.py`, `chunks.chunk_index` column
- **Description:** Same root cause as BUG-1/2. `chunk_index` is not a field in `ChunkDocument`.
  The `_embed_and_store()` method has dead code `try: idx = 0` that hardcodes the value.
  All chunks for a document are registered with `chunk_index=0`. (`ingester.py:257-260`)
  Consequence: `fetch_full_document()` cannot reconstruct document order by `chunk_index`.
- **Current safe interpretation:** `chunks.chunk_index` is always 0; document-order reconstruction
  via `chunk_index` is not reliable.
- **Recommended action:** Same fix as BUG-1/2. After fix, verify `fetch_full_document()` ordering.
- **Source reference:** `03_spec_rag.md §13`
- **Notes for AI:** BUG-1, BUG-2, BUG-3 share a single root cause. One fix resolves all three.

---

## Spec Conflicts

### SPEC-1: `use_rrf=False` has no effect

- **Type:** SPEC_CONFLICT
- **Impact scope:** `rag/stages/fusion.py`, `RagConfig.use_rrf`, `rag/repository._dedup_hits`
- **Statement A:** `RagConfig.use_rrf` is documented as a flag to disable RRF merging and fall
  back to `_dedup_hits()` (simple deduplication by chunk_id, all `rrf_score=0.0`).
- **Statement B:** `FusionStage` implementation does not check `use_rrf`; it always executes RRF.
  `_dedup_hits()` is dead code.
- **Preferred source:** `05_ref-rag.md` (canonical; explicitly states current implementation ignores flag)
- **Current safe interpretation:** Setting `use_rrf=False` in config has no effect.
  RRF is always applied.
- **Recommended action:** Either implement the flag check in `FusionStage`, or remove `use_rrf`
  from `RagConfig` and documentation. Document the decision.
- **Source reference:** `05_ref-rag.md §1.1`
- **Notes for AI:** Do not interpret `use_rrf=False` as "dedup fallback is active."

---

### SPEC-2: Ingestion stage count — "3 steps" vs "4 phases"

- **Type:** SPEC_CONFLICT
- **Impact scope:** Documentation only; no code defect
- **Statement A:** `03_spec_rag.md §1` describes "4段階" (4 phases): crawl / chunk split /
  embedding generation / SQLite storage.
- **Statement B:** `03_rag-ingestion-run.md §1` describes "3ステップ" (3 steps): crawler /
  chunk_splitter / ingester.
- **Preferred interpretation:** Both are correct from different perspectives.
  3 scripts, 4 processing phases (embedding generation and storage are both done by `ingester.py`).
- **Current safe interpretation:** Use "3 scripts / 4 processing phases" when both accuracy
  and brevity are needed.
- **Source reference:** `03_spec_rag.md §1`, `03_rag-ingestion-run.md §1`
- **Notes for AI:** When counting "stages" in the ingestion pipeline, clarify whether you
  mean scripts (3) or processing phases (4).

---

## Document Inconsistencies

### DOC-1: Module name — `web_crawler.py` vs `crawler.py`

- **Type:** DOC_INCONSISTENCY
- **Impact scope:** Documentation references only; actual file is `scripts/rag/ingestion/crawler.py`
- **Description:** `03_rag-ref-crawler.md` title says `web_crawler.py`. Execution docs and spec
  say `crawler.py`. The class is `WebCrawler`.
- **Authoritative name:** `crawler.py` (confirmed by `03_rag-ingestion-run.md` CLI commands
  and `03_spec_rag.md §2`)
- **Recommended action:** Correct the title in `03_rag-ref-crawler.md` if the file is retained.
- **Notes for AI:** Use `crawler.py` in all file path references.

---

### DOC-2: Module name — `rag_ingester.py` vs `ingester.py`

- **Type:** DOC_INCONSISTENCY
- **Impact scope:** Documentation references only; actual file is `scripts/rag/ingestion/ingester.py`
- **Description:** `03_rag-ref-ingester.md` title says `rag_ingester.py`. Execution docs and spec
  say `ingester.py`. The class is `RagIngester`.
- **Authoritative name:** `ingester.py` (confirmed by `03_rag-ingestion-run.md` CLI commands)
- **Recommended action:** Correct the title in `03_rag-ref-ingester.md` if the file is retained.
- **Notes for AI:** Use `ingester.py` in all file path references.

---

## Open Questions

### OQ-1: External RAG service — authentication and error handling undefined

- **Type:** OPEN_QUESTION
- **Impact scope:** `RagPipeline._augment_http()`, `cfg.rag_service_url`
- **Description:** When `rag_service_url` is configured, `_augment_http()` delegates to the
  external service. No authentication mechanism is specified. Error handling (timeout, 5xx,
  malformed response) falls back to in-process pipeline, but retry policy is unspecified.
- **Current safe interpretation:** External RAG delegation works for simple setups; production
  use with authentication requirements is unsupported.
- **Recommended action:** Define authentication headers and retry policy before enabling in production.
- **Source reference:** `05_ref-rag.md §1.1`, `03_spec_rag.md §13`

---

### OQ-2: MDQ vs RAG boundary — migration criteria undefined

- **Type:** OPEN_QUESTION
- **Impact scope:** `mcp/mdq/`, `mcp/rag_pipeline/`
- **Description:** MDQ (Markdown-dedicated index) and RAG serve overlapping use cases for
  Markdown content. The boundary for when to use MDQ vs RAG is not defined.
- **Recommended action:** Define migration criteria in `docs/04_mcp-mdq.md`.

---

### OQ-3: `test_ingester.py` missing

- **Type:** OPEN_QUESTION
- **Impact scope:** Test coverage for `scripts/rag/ingestion/ingester.py`
- **Description:** No unit test file covers `ingester.py`. DB write behavior, BUG-1/2/3 fixes,
  and `chunking_strategy` column reflection are all untested.
- **Recommended action:** Create `tests/test_ingester.py` covering: `ingest_url_group()`,
  `_read_chunk_json()` field preservation, `chunk_index` correctness, and `--force` behavior.

---

### OQ-4: `use_refiner=True` edge cases

- **Type:** OPEN_QUESTION
- **Impact scope:** `RagPipeline._augment_refiner()`
- **Description:** When `_augment_refiner()` returns an empty string, the caller returns raw
  chunks. The condition that produces empty string output (vs exception) is not documented.
- **Recommended action:** Add explicit documentation for the empty-output fallback path.

---

### OQ-5: `SemanticCache.prune()` concurrent access behavior

- **Type:** OPEN_QUESTION
- **Impact scope:** `rag/cache.py SemanticCache`
- **Description:** `prune()` removes oldest entries (FIFO). Thread safety under concurrent
  `put()`/`lookup()` calls is not specified.
- **Recommended action:** Verify or add a lock if `RagPipeline` instances are shared across
  async tasks that call `put()` concurrently.

---

### OQ-6: `chunks_fts` COALESCE trigger behavior for `normalized_content=None`

- **Type:** OPEN_QUESTION
- **Impact scope:** `chunks_fts`, FTS5 for English/code chunks
- **Description:** The `chunks_ai` trigger uses `COALESCE(normalized_content, content)`.
  For English and code chunks, `normalized_content` is NULL. Verify FTS5 correctly falls
  back to `content` for indexing and querying in all SQLite versions used.
- **Recommended action:** Add an integration test asserting English chunk FTS search works
  when `normalized_content` is NULL.

---

### OQ-7: `_augment_http()` fallback trigger condition

- **Type:** OPEN_QUESTION
- **Impact scope:** `RagPipeline._augment_http()`
- **Description:** The method returns `None` to signal "fall back to in-process pipeline."
  The exact conditions that trigger this (`None` return) are not documented. Is it any exception,
  HTTP error, empty result, or only connection failure?
- **Recommended action:** Document the explicit conditions that cause `_augment_http()` to
  return `None`.
