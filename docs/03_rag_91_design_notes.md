# DESIGN-2 FTS5 Content Separation

## DESIGN-2: FTS uses `normalized_content`, while LLM receives `content`

- **Type:** Confirmed design decision
- **Impact scope:** `chunks` table, `chunks_fts` virtual table, `scripts/rag/repository.py`, `scripts/rag/stages/augment.py`
- **Invariants (non-negotiable):**
  - `chunks.content` is the original chunk text and is the **only** text used in the LLM context.
  - `chunks.normalized_content` is Japanese text normalized with Sudachi and is used **exclusively** for the FTS5 search index. It must not be included in the LLM context.
  - FTS5 indexes `COALESCE(normalized_content, content)` via the `chunks_ai` trigger.
  - Japanese chunks store whitespace-separated text normalized by Sudachi in `normalized_content`. English/code chunks maintain `normalized_content = NULL`, and FTS5 falls back to `content`.
  - `AugmentStage` must always output `content` and must never output `normalized_content`.
- **Description:** Japanese chunks maintain two types of text representations. `chunks.content` (original text) is injected into the LLM context by `AugmentStage`. `chunks.normalized_content` (Sudachi-normalized) is indexed into `chunks_fts` by the `chunks_ai` trigger. On the FTS query side, Sudachi morphological filtering is also used to normalize Japanese words. This separation allows the LLM to receive readable original text while BM25 search uses morphologically normalized forms.
- **Notes for AI reference:** Do not replace `content` with `normalized_content` in the output of the Augment stage. This separation is intentional and finalized. Source: `03_rag_02_01_ingestion_pipeline-overview.md FTS5/LLM content separation`, `03_rag_03_01_query_pipeline-overview.md section 5.5 AugmentStage`.

---

## DESIGN-3: Separation of Responsibilities between `documents`, `chunks`, `chunks_fts`, and `chunks_vec`

- **Type:** Confirmed design decision
- **Impact scope:** DB schema, all ingestion and query processing code
- **Invariants (non-negotiable):**
  - `documents` and `chunks` are the **authoritative data stores**, and all modification operations must go through them.
  - `chunks_fts` and `chunks_vec` are **derived indexes**, and application code must treat them as read-only.
  - `chunks_fts` synchronization: Performed via triggers (`chunks_ai`/`chunks_au`/`chunks_ad`); direct INSERT/UPDATE is prohibited. Manual editing of `chunks_fts` is forbidden; use `/session rag-rebuild-fts` instead.
  - `chunks_vec` synchronization: Performed via INSERT during ingestion and explicit DELETE. No foreign key constraints exist (due to `sqlite-vec` limitations).
  - Deletion order during forced re-insertion: Explicitly delete `chunks_vec` before deleting `documents` (so `chunks` is deleted via `ON DELETE CASCADE`). This is only effective with connections using `write_mode=True` (to enable `PRAGMA foreign_keys=ON`). Note that the `chunks_vec_ad` trigger is a defensive backstop against direct deletions of `chunks` and is not the primary path described above.
  - RAG consistency checks (`/session rag-consistency`) verify synchronization between authoritative `chunks` and derived indexes `chunks_fts` and `chunks_vec`.
- **Description:**
  - `documents`: Authoritative URL/document metadata (`url`, `title`, `lang`, `fetched_at`, `etag`, `last_modified`, `chunking_strategy`). One row per URL.
  - `chunks`: Authoritative chunk text and position information (`content`, `normalized_content`, `chunk_index`, `chunk_type`). Foreign key to `documents` via `doc_id` (`ON DELETE CASCADE`).
  - `chunks_fts`: Derived FTS5/BM25 full-text search index. Automatically synchronized via triggers using `COALESCE(normalized_content, content)`. Dedicated to BM25 search. Must not be manually edited; use `/session rag-rebuild-fts` for repairs.
  - `chunks_vec`: Derived `sqlite-vec` KNN vector index. float32 embedding BLOB. Dedicated to KNN search.
- **RAG consistency checks:** Verifies synchronization between authoritative data and derived indexes:
  - `fts_gap`: Number of chunks missing from `chunks_fts` (Fix: `/session rag-rebuild-fts`)
  - `fts_orphan_count`: FTS entries without corresponding chunks (Data loss risk; Fix: `/session rag-rebuild-fts`)
  - `orphan_vec_count`: Vector rows without corresponding chunks (Fix: `ingester.py --force`)
- **Notes for AI reference:** `sqlite-vec` virtual tables do not support standard foreign key constraints. RAG consistency checks (`/session rag-consistency`) verify synchronization between authoritative `chunks` and derived indexes `chunks_fts` and `chunks_vec`. Source: `03_rag_04_05_dto-types.md DB Schema`, `03_rag_05_1-configuration-reference.md RAG index consistency checks`.

---

**Existing Tests:**

| Test | File | Coverage |
|------|------|----------|
| COALESCE fallback for NULL `normalized_content` | `tests/test_fts_fallback.py` | ✓ English/code chunks are indexed with `content` when `normalized_content` is NULL |
| Indexing multi-language documents | `tests/test_fts_fallback.py` | ✓ Japanese chunks use `normalized_content` and English chunks use `content` |
| Distinction between empty string and NULL for `normalized_content` | `tests/test_fts_fallback.py` | ✓ `""` ≠ NULL (COALESCE semantics) |
| TEST-DESIGN2-01: Chunk output contains only `content` field | `tests/test_rag_pipeline.py::TestFormatChunksDesign2` | ✓ `test_content_appears_in_output`, `test_normalized_content_does_not_appear` |
| TEST-DESIGN2-02: Japanese FTS search returns original `content` | `tests/test_fts_fallback.py` | ✓ covered by `test_code_search_returns_original_content` and `test_mixed_japanese_english_document` |
| TEST-DESIGN2-03: If `normalized_content` differs from `content`, `normalized_content` is not in LLM context | `tests/test_rag_pipeline.py::TestFormatChunksDesign2`, `tests/test_rag_pipeline_stage.py::TestAugmentStage` | ✓ `test_normalized_differs_from_content_not_in_output`, `test_augment_stage_normalized_does_not_leak` |
| TEST-DESIGN2-01 (AugmentStage path): AugmentStage outputs only `content` | `tests/test_rag_pipeline_stage.py::TestAugmentStage` | ✓ `test_augment_stage_content_only_invariant`, `test_augment_stage_normalized_does_not_leak` |

**Missing Tests:**

| Test ID | Description | Priority |
|---------|-------------|----------|
| _(None — all tests related to DESIGN-2 implemented)_ | | | 

**Implementation Verification (2026-07-12):** Confirmed existence of all test classes/functions listed above (`TestEnglishFtsFallback`/`TestCodeFtsFallback`/`TestNormalizedContentEdgeCases` in `tests/test_fts_fallback.py`, `TestFormatChunksDesign2` in `tests/test_rag_pipeline.py`, `TestAugmentStage` in `tests/test_rag_pipeline_stage.py`). No discrepancies with invariants, trigger SQL, or test status. Classification: Explicit in code.

---



## Related Documents

- [03_rag_91_design_notes.md](03_rag_91_design_notes.md)

## Keywords

design-decision
database
responsibilities

# DESIGN-3 Table Responsibilities

## DESIGN-3 Regression Test Expectations

**Existing Tests:**

| Test | File | Coverage |
|------|------|----------|
| FTS5 trigger synchronization verification | `tests/test_fts_fallback.py` | ✓ Verified INSERT/UPDATE/DELETE triggers use COALESCE |
| Vector orphan detection | `scripts/db/maintenance.py:check_rag_consistency()` | ✓ `orphan_vec_count` is reported |

**Regression Tests:**

| Test ID | Description | File | Status |
|---------|-------------|------|--------|
| TEST-DESIGN3-01 | FTS rebuild uses `COALESCE(normalized_content, content)` | `tests/test_rag_index_integrity.py` | ✓ Added |
| TEST-DESIGN3-02 | `chunks_fts` is derived from `chunks` (not maintained independently) | `tests/test_rag_index_integrity.py` | ✓ Added |
| TEST-DESIGN3-03 | Force re-ingestion does not leave orphan vector records | `tests/test_rag_index_integrity.py` | ✓ Added |
| TEST-DESIGN3-04 | Deletion order invariant: `chunks_vec` $\rightarrow$ `documents` (CASCADE removes `chunks`) | `tests/test_rag_index_integrity.py` | ✓ Added |
| TEST-DESIGN3-05 | Consistency checks detect desynchronization in derived indexes | `tests/test_rag_index_integrity.py` | ✓ Added |

**Bug Fixes — FTS deletion in `reconcile_url()`:**

`RagMaintenanceService.reconcile_url()` was using `DELETE FROM chunks_fts WHERE chunk_id IN (...)`, which is invalid for FTS5 content tables. Fixed in `scripts/agent/services/rag_maintenance_service.py` to use correct row-based FTS5 deletion syntax: `INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', ?, ?)`. Regression test: `tests/test_rag_index_integrity.py::test_reconcile_url_fts_deletion`.

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

**TEST-DESIGN3-02: `chunks_fts` is derived, not authoritative**

```python
# Pseudocode for integration test - chunks_fts_derived_index
def test_chunks_fts_is_derived_index(db):
    """chunks_fts must not be directly INSERTed/UPDATEed by application code."""
    # Insert chunk via canonical path (INSERT into chunks)
    insert_chunk(doc_id=1, content="test", normalized_content=None, chunk_index=0)
    # Verify: FTS entry exists (trigger-synced)
    results = fts_search("test")
    assert len(results) == 1
```

**TEST-DESIGN3-03: Force re-ingestion does not leave orphan vectors**

```python
# Pseudocode for integration test - force_reingest_no_orphan_vectors
def test_force_reingest_no_orphan_vectors(db):
    """Force re-ingestion must not leave orphan chunks_vec records."""
    # Insert document and chunks
    insert_doc(url="http://example.com")
    insert_chunk(doc_id=1, content="text", normalized_content=None, chunk_index=0)
    # Force re-ingestion (deletes chunks_vec first, then documents; CASCADE removes chunks)
    RagMaintenanceService().delete_document("http://example.com")
    # Verify: no orphan vec rows remain
    orphan_count = db.execute(
        "SELECT COUNT(*) FROM chunks_vec WHERE chunk_id NOT IN (SELECT chunk_id FROM chunks)"
    ).fetchone()[0]
    assert orphan_count == 0
```

**TEST-DESIGN3-04: Deletion order invariant**

```python
# Pseudocode for integration test - deletion_order_invariant
def test_deletion_order_invariant(db):
    """Deletion must follow: chunks_vec $\rightarrow$ documents (CASCADE removes chunks)."""
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
# Pseudocode for integration test - consistency_checks_detect_fts_gap
def test_consistency_checks_detect_fts_gap(db):
    """check_rag_consistency() must detect FTS index desync."""
    # Insert chunk without triggering FTS (simulate trigger failure)
    insert_chunk(doc_id=1, content="test", normalized_content=None, chunk_index=0)
    # Manually remove the FTS-synced row to simulate desync
    db.execute("DELETE FROM chunks_fts WHERE rowid = 1")
    # Verify: check_rag_consistency() reports the gap
    result = check_rag_consistency(db)
    assert result.fts_gap > 0
```

Corresponding implementation (`test_consistency_check_detects_fts_gap` in `tests/test_rag_index_integrity.py`) exists. (Explicit in code)

## Related Documents

- [03_rag_91_design_notes.md](03_rag_91_design_notes.md)

## Keywords

design-decision
database
responsibilities
