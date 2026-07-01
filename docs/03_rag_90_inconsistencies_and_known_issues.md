# RAG Inconsistencies and Known Issues

This file catalogs known bugs, spec conflicts, document inconsistencies, and open questions
discovered during the restructuring of RAG documentation.

Each entry uses: Type / Impact / Description / Safe interpretation / Recommended action / Source.

---

## Confirmed Design Decisions

### DESIGN-2: FTS5 uses `normalized_content`; LLM receives `content`

- **Type:** Confirmed design decision
- **Impact scope:** `chunks` table, `chunks_fts` virtual table, `scripts/rag/repository.py _build_fts_query()`, `scripts/rag/stages/augment.py`
- **Invariants (non-negotiable):**
  - `chunks.content` is the original chunk text and the **only** text used for LLM context.
  - `chunks.normalized_content` is Sudachi-normalized Japanese text used **exclusively** for FTS5 search indexing; it must never appear in LLM context.
  - FTS5 indexes `COALESCE(normalized_content, content)` via the `chunks_ai` trigger.
  - Japanese chunks store Sudachi `normalized_form()` space-joined text in `normalized_content`. English/code chunks keep `normalized_content = NULL`; FTS5 falls back to `content`.
  - `AugmentStage` must always output `content`, never `normalized_content`.
- **Description:** Japanese chunks store two text representations. `chunks.content` (original text) is injected into the LLM context by `AugmentStage`. `chunks.normalized_content` (Sudachi-normalized) is indexed by the `chunks_ai` trigger into `chunks_fts`. FTS5 query-side also normalizes Japanese terms in `_build_fts_tokens_ja()`. This separation ensures LLM receives readable original text while BM25 search uses morphologically normalized forms.
- **Notes for AI reference:** Never replace `content` with `normalized_content` in the Augment stage output. The separation is intentional and confirmed. Source: `03_rag_02_ingestion_pipeline.md §FTS5/LLM content separation`, `03_rag_03_query_pipeline.md §5.5 AugmentStage`.

---

### DESIGN-3: Separation of responsibilities among `documents`, `chunks`, `chunks_fts`, `chunks_vec`

- **Type:** Confirmed design decision
- **Impact scope:** DB schema, all ingestion and query code
- **Invariants (non-negotiable):**
  - `documents` and `chunks` are **canonical data stores**; all mutations go through them.
  - `chunks_fts` and `chunks_vec` are **derived indexes**; application code must treat them as read-only.
  - `chunks_fts` sync: trigger-based (`chunks_ai`/`chunks_au`/`chunks_ad`); never INSERT/UPDATE directly. Manual edits to `chunks_fts` are prohibited — use `/db rag rebuild-fts` instead.
  - `chunks_vec` sync: ingestion-time INSERT and explicit DELETE; no FK constraint (sqlite-vec limitation).
  - Deletion order for force-reinsertion: `chunks_vec` first → `chunks` → `documents` (mandatory to avoid orphaned vector records).
  - RAG consistency checks (`/db consistency`) validate synchronization between canonical `chunks` and derived indexes `chunks_fts` and `chunks_vec`.
- **Description:**
  - `documents`: canonical URL/document metadata (url, title, lang, fetched_at, etag, last_modified, chunking_strategy); one row per URL.
  - `chunks`: canonical chunk text and position data (content, normalized_content, chunk_index, chunk_type); FK to `documents` via `doc_id` (ON DELETE CASCADE).
  - `chunks_fts`: derived FTS5/BM25 full-text index; auto-synced by triggers using `COALESCE(normalized_content, content)`; BM25 search only. Must not be manually edited — use `/db rag rebuild-fts` to repair.
  - `chunks_vec`: derived sqlite-vec KNN vector index; float32 embedding BLOB; KNN search only.
- **RAG consistency checks:** validate synchronization between canonical data and derived indexes:
  - `fts_gap`: number of chunks missing from `chunks_fts` (repair: `/db rag rebuild-fts`)
  - `fts_orphan_count`: FTS entries without matching chunks (data loss risk; repair: `/db rag rebuild-fts`)
  - `orphan_vec_count`: vector rows without matching chunks (repair: `ingester.py --force`)
- **Notes for AI reference:** sqlite-vec virtual tables do not support standard FK constraints. RAG consistency checks (`/db consistency`) validate synchronization between canonical `chunks` and derived indexes `chunks_fts` and `chunks_vec`. Source: `03_rag_04_data_model_and_interfaces.md §DB Schema`, `03_rag_05_configuration_and_operations.md §RAG index consistency checks`.

---

### DESIGN-2 Regression Test Expectations

**Existing tests:**

| Test | File | Coverage |
|------|------|----------|
| COALESCE fallback for NULL `normalized_content` | `tests/test_fts_fallback.py` | ✓ English/code chunks indexed on `content` when `normalized_content` is NULL |
| Mixed-language document indexing | `tests/test_fts_fallback.py` | ✓ Japanese chunk uses `normalized_content`; English chunk uses `content` |
| Empty string vs NULL `normalized_content` | `tests/test_fts_fallback.py` | ✓ `""` ≠ NULL (COALESCE semantics) |

**Missing tests:**

| Test ID | Description | Priority |
|---------|-------------|----------|
| TEST-DESIGN2-01 | AugmentStage outputs `content` only, not `normalized_content` | High |
| TEST-DESIGN2-02 | Japanese chunk FTS search via normalized terms returns original `content` in LLM context | High |
| TEST-DESIGN2-03 | LLM context does not contain `normalized_content` unless identical to `content` | Medium |

**TEST-DESIGN2-01: AugmentStage content-only invariant**

```python
# Pseudocode for integration test
def test_augment_stage_content_only(db):
    """AugmentStage must format chunks.content only, never normalized_content."""
    # Insert Japanese chunk with both content and normalized_content
    insert_chunk(
        doc_id=1,
        content="日本語テキスト",
        normalized_content="にほんご テキスト",  # Sudachi-normalized
        chunk_index=0,
    )
    # Run AugmentStage
    augment_result = _format_chunks(reranked=[RagHit(content="日本語テキスト", ...)])
    # Verify: content appears in output
    assert "日本語テキスト" in augment_result
    # Verify: normalized_content does NOT appear
    assert "にほんご テキスト" not in augment_result
```

**TEST-DESIGN2-02: Japanese FTS search returns original content**

```python
# Pseudocode for integration test
def test_japanese_fts_returns_original_content(db):
    """Japanese chunk found via normalized terms must return original content."""
    insert_chunk(
        doc_id=1,
        content="食べる",
        normalized_content="食べる",  # Sudachi-normalized (space-joined)
        chunk_index=0,
    )
    # Search using Sudachi-normalized form
    results = fts_search("食べる")
    assert len(results) == 1
    assert results[0].content == "食べる"  # Original text, not normalized
```

**TEST-DESIGN2-03: LLM context integrity**

```python
# Pseudocode for integration test
def test_llm_context_no_normalized_content(db):
    """LLM context must not contain normalized_content unless identical to content."""
    insert_chunk(
        doc_id=1,
        content="検索結果",
        normalized_content="けんさく けっか",  # Different from original
        chunk_index=0,
    )
    augment_result = _format_chunks(reranked=[RagHit(content="検索結果", ...)])
    assert "検索結果" in augment_result
    assert "けんさく けっか" not in augment_result
```

---

### DESIGN-3 Regression Test Expectations

**Existing tests:**

| Test | File | Coverage |
|------|------|----------|
| FTS5 trigger sync verification | `tests/test_fts_fallback.py` | ✓ INSERT/UPDATE/DELETE triggers use COALESCE |
| Vector orphan detection | `scripts/db/maintenance.py:check_rag_consistency()` | ✓ `orphan_vec_count` reported |

**Missing tests:**

| Test ID | Description | Priority |
|---------|-------------|----------|
| TEST-DESIGN3-01 | FTS rebuild uses COALESCE(normalized_content, content) | High |
| TEST-DESIGN3-02 | `chunks_fts` is synchronized from `chunks` (not independently maintained) | High |
| TEST-DESIGN3-03 | Force re-ingestion does not leave orphan vector records | High |
| TEST-DESIGN3-04 | Deletion order invariant: `chunks_vec` → `chunks` → `documents` | Medium |
| TEST-DESIGN3-05 | Consistency checks detect derived index desynchronization | Medium |

**TEST-DESIGN3-01: FTS rebuild uses COALESCE**

```python
# Pseudocode for integration test
def test_fts_rebuild_uses_cascade(db):
    """RagMaintenanceService.rebuild_fts() must use COALESCE(normalized_content, content)."""
    # Insert chunk with NULL normalized_content
    insert_chunk(
        doc_id=1,
        content="english text",
        normalized_content=None,
        chunk_index=0,
    )
    # Delete all FTS entries
    db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('delete-all')")
    # Rebuild using the maintenance service
    RagMaintenanceService().rebuild_fts()
    # Verify: content is indexed (not NULL)
    results = fts_search("english")
    assert len(results) == 1
    assert results[0].content == "english text"
```

**TEST-DESIGN3-02: chunks_fts is derived, not canonical**

```python
# Pseudocode for integration test
def test_chunks_fts_is_derived_index(db):
    """chunks_fts must not be directly INSERTed/UPDATEed by application code."""
    # Insert chunk via canonical path (INSERT into chunks)
    insert_chunk(doc_id=1, content="test", normalized_content=None, chunk_index=0)
    # Verify: FTS entry exists (trigger-synced)
    results = fts_search("test")
    assert len(results) == 1
```

**TEST-DESIGN3-03: Force re-ingestion no orphan vectors**

```python
# Pseudocode for integration test
def test_force_reingest_no_orphan_vectors(db):
    """Force re-ingestion must not leave orphan chunks_vec records."""
    # Insert document and chunks
    insert_doc(url="http://example.com")
    insert_chunk(doc_id=1, content="text", normalized_content=None, chunk_index=0)
    # Force re-ingestion (deletes chunks_vec first, then chunks, then documents)
    RagMaintenanceService().delete_document("http://example.com")
    # Verify: no orphan vec rows remain
    orphan_count = db.execute(
        "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
    ).fetchone()[0]
    assert orphan_count == 0
```

**TEST-DESIGN3-04: Deletion order invariant**

```python
# Pseudocode for integration test
def test_deletion_order_invariant(db):
    """Deletion must follow: chunks_vec → chunks → documents."""
    # Insert document with chunks and vectors
    insert_doc(url="http://order-test.com")
    chunk_id = insert_chunk(doc_id=1, content="test", normalized_content=None, chunk_index=0)
    db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
    # Delete via canonical path
    delete_document_chain(db, doc_id=1)
    # Verify: no orphan vec rows remain
    orphan_count = db.execute(
        "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
    ).fetchone()[0]
    assert orphan_count == 0
```

**TEST-DESIGN3-05: Consistency checks detect desynchronization**

```python
# Pseudocode for integration test
def test_consistency_checks_detect_fts_gap(db):
    """check_rag_consistency() must detect FTS index desync."""
    # Insert chunk without triggering FTS (simulate trigger failure)
    insert_chunk(doc_id=1, content="test", normalized_content=None, chunk_index=0)
    # Manually remove FTS entry to simulate trigger failure
    db.execute("DELETE FROM chunks_fts WHERE rowid = ?", (chunk_id,))
    report = check_rag_consistency(db)
    assert report.fts_gap == 1
    assert report.affected_chunk_ids is not None
```

---

## Active Issues

---



