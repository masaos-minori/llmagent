---
title: "DESIGN-3 Table Responsibilities"
category: rag
tags:
  - rag
  - design-decision
  - database
related:
  - 03_rag_00_document-guide.md
---

# DESIGN-3 テーブルの責務


## DESIGN-3 リグレッションテストの期待値

**既存のテスト:**

| Test | File | Coverage |
|------|------|----------|
| FTS5トリガー同期の検証 | `tests/test_fts_fallback.py` | ✓ INSERT/UPDATE/DELETEトリガーがCOALESCEを使用していることを確認 |
| ベクトル孤立検出 | `scripts/db/maintenance.py:check_rag_consistency()` | ✓ `orphan_vec_count`が報告される |

**リグレッションテスト:**

| Test ID | Description | File | Status |
|---------|-------------|------|--------|
| TEST-DESIGN3-01 | FTS再構築がCOALESCE(normalized_content, content)を使用する | `tests/test_rag_index_integrity.py` | ✓ 追加済み |
| TEST-DESIGN3-02 | `chunks_fts`は`chunks`から同期される (独立して維持されるものではない) | `tests/test_rag_index_integrity.py` | ✓ 追加済み |
| TEST-DESIGN3-03 | 強制再取り込みは孤立したベクトルレコードを残さない | `tests/test_rag_index_integrity.py` | ✓ 追加済み |
| TEST-DESIGN3-04 | 削除順序の不変条件: `chunks_vec` → `documents`（`ON DELETE CASCADE` により `chunks` を削除） | `tests/test_rag_index_integrity.py` | ✓ 追加済み |
| TEST-DESIGN3-05 | 整合性チェックが派生インデックスの非同期を検出する | `tests/test_rag_index_integrity.py` | ✓ 追加済み |

**バグ修正 — reconcile_url()のFTS削除:**

`RagMaintenanceService.reconcile_url()`は`DELETE FROM chunks_fts WHERE chunk_id IN (...)`を
使用していたが、これはFTS5コンテンツテーブルでは無効である。
`scripts/agent/services/rag_maintenance_service.py`で修正し、正しい行単位のFTS5削除コマンド構文
`INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', ?, ?)`を使用するようにした。
リグレッションテスト: `tests/test_rag_index_integrity.py::test_reconcile_url_fts_deletion`。

**TEST-DESIGN3-01: FTS再構築がCOALESCEを使用する**

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

**TEST-DESIGN3-02: chunks_ftsは派生であり、正規ではない**

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

**TEST-DESIGN3-03: 強制再取り込みで孤立ベクトルが発生しないこと**

```python
# Pseudocode for integration test
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

**TEST-DESIGN3-04: 削除順序の不変条件**

```python
# Pseudocode for integration test
def test_deletion_order_invariant(db):
    """Deletion must follow: chunks_vec → documents (CASCADE removes chunks)."""
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

**TEST-DESIGN3-05: 整合性チェックが非同期を検出する**

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
