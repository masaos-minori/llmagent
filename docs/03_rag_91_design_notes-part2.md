---
title: "DESIGN-3 Table Responsibilities"
category: rag
tags:
  - rag
  - design-decision
  - database
related:
  - 03_rag_00_document-guide.md
  - 03_rag_91_design_notes.md
source:
  - 03_rag_91_design_notes.md
---

# DESIGN-3 Table Responsibilities


## DESIGN-3 Regression Test Expectations

**Existing tests:**

| Test | File | Coverage |
|------|------|----------|
| FTS5 trigger sync verification | `tests/test_fts_fallback.py` | ✓ INSERT/UPDATE/DELETE triggers use COALESCE |
| Vector orphan detection | `scripts/db/maintenance.py:check_rag_consistency()` | ✓ `orphan_vec_count` reported |

**Regression tests:**

| Test ID | Description | File | Status |
|---------|-------------|------|--------|
| TEST-DESIGN3-01 | FTS rebuild uses COALESCE(normalized_content, content) | `tests/test_rag_index_integrity.py` | ✓ Added |
| TEST-DESIGN3-02 | `chunks_fts` is synchronized from `chunks` (not independently maintained) | `tests/test_rag_index_integrity.py` | ✓ Added |
| TEST-DESIGN3-03 | Force re-ingestion does not leave orphan vector records | `tests/test_rag_index_integrity.py` | ✓ Added |
| TEST-DESIGN3-04 | Deletion order invariant: `chunks_vec` → `chunks` → `documents` | `tests/test_rag_index_integrity.py` | ✓ Added |
| TEST-DESIGN3-05 | Consistency checks detect derived index desynchronization | `tests/test_rag_index_integrity.py` | ✓ Added |

**Bug fix — reconcile_url() FTS deletion:**

`RagMaintenanceService.reconcile_url()` used `DELETE FROM chunks_fts WHERE chunk_id IN (...)`
which is invalid on an FTS5 content table. Fixed in
`scripts/agent/services/rag_maintenance_service.py` to use the correct per-row FTS5
delete-command syntax:
`INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', ?, ?)`.
Regression test: `tests/test_rag_index_integrity.py::test_reconcile_url_fts_deletion`.

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


## Related Documents

- [03_rag_91_design_notes.md](03_rag_91_design_notes-part1.md)

## Keywords

design-decision
database
responsibilities
