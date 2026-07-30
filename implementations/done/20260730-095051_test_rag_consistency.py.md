## Goal

Extend RAG consistency checks to detect document-level and URL-level integrity problems: documents with zero chunks, chunks without vector rows, duplicate chunk_index values, and URL-level mismatches between chunks/vectors/FTS.

## Scope

**In-Scope:**
- Add `documents_without_chunks_count` — documents that have no chunks
- Add `chunks_without_vec_count` — chunks without corresponding vector rows
- Add `duplicate_chunk_index_count` — duplicate chunk_index values within the same document
- Add URL-level counts: document URL, chunk count, vector count, FTS count per URL
- Include affected doc_ids and URLs where possible
- Update `summarize_issues()` with clear severity and repair guidance for new checks
- Update `is_consistent()` to consider new checks

**Out-of-Scope:**
- Adding UNIQUE(doc_id, chunk_index) constraint (deferred to later migration)
- Changes to SQLite schema
- Changes to ingestion logic itself

## Assumptions

1. A document is considered "without chunks" only if it exists in the documents table but has no corresponding rows in chunks.
2. A chunk is considered "without vector" if it exists in chunks but has no row in chunks_vec.
3. Duplicate chunk_index means the same chunk_index value appears multiple times within the same doc_id.
4. URL-level inconsistency means a URL has different chunk counts across chunks/chunks_vec/chunks_fts tables.
5. All new checks should use read-only queries (no writes).

## Unknowns & Gaps

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Should `is_consistent()` return False when any new check fails, or keep backward compatibility by only checking original conditions? | No evidence of existing convention | Conservative: make is_consistent() stricter — all checks must pass | False |
| UNK-02 | What is the performance impact of adding URL-level aggregation queries on large datasets? | Need to estimate query complexity | Use LIMIT 10 for affected identifiers like existing code does | False |
| UNK-03 | Can a document exist in documents table without being referenced by chunks? If so, how common is this? | No evidence of existing convention | Treat as anomaly — likely indicates partial deletion failure | False |

## Affected Areas & Tool Evidence

- **Affected Files**:
  - `scripts/db/rag_consistency.py` — add new consistency checks, update summarize_issues(), update is_consistent()
  - `scripts/db/models.py` — add new fields to RagConsistencyReport dataclass

- **Blast Radius**: Medium — changes affect core consistency reporting; incorrect implementation could produce false positives

- **Risk Metrics**: `rag_consistency.py` has moderate churn (~148 lines); `models.py` has low churn (~106 lines)

- **Deploy Impact**: None — no config keys, ports, or deploy.sh changes

## Design decisions

- **Test isolation**: Use in-memory SQLite database (_FakeSQLiteHelper) following existing patterns
- **Severity verification**: Verify [WARNING] vs [CRITICAL] prefixes match expected levels
- **Comprehensive coverage**: Test each new check individually plus combined scenarios

## Alternatives considered

- **Integration tests only**: Could rely solely on integration tests. Rejected because unit tests provide faster feedback and clearer failure diagnostics.
- **Parametrized tests**: Could use pytest parametrization for all new checks. Rejected because separate test functions provide better error messages.

## Implementation

### Target file

`tests/test_rag_consistency.py`

### Procedure

#### Phase 6: Tests

1. Test: documents with zero chunks detected
   ```python
   def test_documents_without_chunks_detected(self) -> None:
       """Documents that exist without any chunks should be flagged."""
       db = _make_rag_db()
       doc_id = _insert_doc(db)
       # Don't insert any chunks for this document
       
       report = check_rag_consistency(db)  # type: ignore[arg-type]
       assert report.documents_without_chunks_count == 1
       assert report.affected_docs_without_chunks is not None
       assert doc_id in report.affected_docs_without_chunks
       assert not is_consistent(report)
       issues = summarize_issues(report)
       assert any("[WARNING]" in i and "Documents without chunks" in i for i in issues)
   ```

2. Test: chunks without vectors detected
   ```python
   def test_chunks_without_vectors_detected(self) -> None:
       """Chunks that lack corresponding vector rows should be flagged."""
       db = _make_rag_db()
       doc_id = _insert_doc(db)
       chunk_id = _insert_chunk(db, doc_id, "text without vector")
       # Don't insert into chunks_vec
       
       report = check_rag_consistency(db)  # type: ignore[arg-type]
       assert report.chunks_without_vec_count == 1
       assert report.affected_chunks_without_vec is not None
       assert chunk_id in report.affected_chunks_without_vec
       assert not is_consistent(report)
       issues = summarize_issues(report)
       assert any("[CRITICAL]" in i and "Chunks without vector" in i for i in issues)
   ```

3. Test: duplicate chunk_index values detected
   ```python
   def test_duplicate_chunk_index_detected(self) -> None:
       """Duplicate chunk_index values within the same document should be flagged."""
       db = _make_rag_db()
       doc_id = _insert_doc(db)
       # Insert two chunks with the same chunk_index
       cur1 = db.execute(
           "INSERT INTO chunks (doc_id, content, chunk_index) VALUES (?, ?, 1)",
           (doc_id, "first chunk"),
       )
       db.commit()
       chunk_id1 = cur1.lastrowid
       
       cur2 = db.execute(
           "INSERT INTO chunks (doc_id, content, chunk_index) VALUES (?, ?, 1)",
           (doc_id, "second chunk"),
       )
       db.commit()
       chunk_id2 = cur2.lastrowid
       
       report = check_rag_consistency(db)  # type: ignore[arg-type]
       assert report.duplicate_chunk_index_count == 1
       assert report.affected_duplicate_chunk_indices is not None
       assert (doc_id, 1) in report.affected_duplicate_chunk_indices
       assert not is_consistent(report)
       issues = summarize_issues(report)
       assert any("[CRITICAL]" in i and "Duplicate chunk_index" in i for i in issues)
   ```

4. Test: URL-level chunk/vector/FTS mismatches detected
   ```python
   def test_url_level_mismatches_detected(self) -> None:
       """URLs with mismatched chunk/vector/FTS counts should be flagged."""
       db = _make_rag_db()
       doc_id = _insert_doc(db)
       chunk_id = _insert_chunk(db, doc_id, "url mismatch test")
       db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
       db.commit()
       
       # Simulate FTS gap for this chunk
       db.execute(
           "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
           (chunk_id, "url mismatch test"),
       )
       db.commit()
       
       report = check_rag_consistency(db)  # type: ignore[arg-type]
       assert report.url_level_mismatches is not None
       assert len(report.url_level_mismatches) > 0
       # The URL should appear in url_level_mismatches with mismatched counts
       url = next(iter(report.url_level_mismatches.keys()))
       assert "Affected URLs" in str(summarize_issues(report))
   ```

5. Test: regression — existing orphan vector and FTS gap behavior unchanged
   ```python
   def test_existing_checks_still_work(self) -> None:
       """Existing checks should still work after adding new ones."""
       # Orphan vec
       db = _make_rag_db()
       db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (99999)", ())
       db.commit()
       report = check_rag_consistency(db)  # type: ignore[arg-type]
       assert report.orphan_vec_count == 1
       assert not is_consistent(report)
       
       # FTS gap
       db = _make_rag_db()
       doc_id = _insert_doc(db)
       chunk_id = _insert_chunk(db, doc_id, "fts gap test")
       db.execute(
           "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
           (chunk_id, "fts gap test"),
       )
       db.commit()
       report = check_rag_consistency(db)  # type: ignore[arg-type]
       assert report.fts_gap == 1
       assert not is_consistent(report)
   ```

6. Test: is_consistent() returns False when new checks fail
   ```python
   def test_is_consistent_false_on_new_failures(self) -> None:
       """is_consistent() should return False when any new check fails."""
       db = _make_rag_db()
       doc_id = _insert_doc(db)
       # Document without chunks
       report = check_rag_consistency(db)  # type: ignore[arg-type]
       assert not is_consistent(report)
   ```

7. Test: is_consistent() returns True when all checks pass
   ```python
   def test_is_consistent_true_when_all_pass(self) -> None:
       """is_consistent() should return True when all checks pass."""
       db = _make_rag_db()
       doc_id = _insert_doc(db)
       chunk_id = _insert_chunk(db, doc_id, "consistent test")
       db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
       db.commit()
       
       report = check_rag_consistency(db)  # type: ignore[arg-type]
       assert is_consistent(report)
       assert report.documents_without_chunks_count == 0
       assert report.chunks_without_vec_count == 0
       assert report.duplicate_chunk_index_count == 0
       assert not report.url_level_mismatches
   ```

8. Test: URL-level mismatch includes repair guidance
   ```python
   def test_url_mismatch_includes_repair_guidance(self) -> None:
       """URL-level mismatch issue should include repair guidance."""
       db = _make_rag_db()
       doc_id = _insert_doc(db)
       chunk_id = _insert_chunk(db, doc_id, "url repair guidance test")
       db.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
       db.commit()
       
       # Simulate FTS gap
       db.execute(
           "INSERT INTO chunks_fts (chunks_fts, rowid, content) VALUES ('delete', ?, ?)",
           (chunk_id, "url repair guidance test"),
       )
       db.commit()
       
       issues = summarize_issues(check_rag_consistency(db))  # type: ignore[arg-type]
       assert any("ingester.py --force" in i for i in issues)
   ```

9. Test: New fields have default values for backward compatibility
   ```python
   def test_new_fields_have_defaults(self) -> None:
       """New fields should have default values for backward compatibility."""
       from db.models import RagConsistencyReport
       
       report = RagConsistencyReport(
           chunks=1, fts=1, vec=1, orphan_vec_count=0,
           fts_gap=0, fts_orphan_count=0, embed_failed=0,
           affected_chunk_ids=None, affected_doc_ids=None,
           affected_orphan_chunk_ids=None, affected_orphan_urls=None,
       )
       assert report.documents_without_chunks_count == 0
       assert report.chunks_without_vec_count == 0
       assert report.duplicate_chunk_index_count == 0
       assert report.url_level_mismatches is None
   ```

### Method

- Add new test functions following existing patterns using _FakeSQLiteHelper
- Use in-memory SQLite database to simulate each scenario
- Verify both count assertions and issue string assertions

### Details

1. `test_documents_without_chunks_detected()`:
   - Create document without inserting any chunks
   - Verify documents_without_chunks_count == 1
   - Verify [WARNING] prefix and "Documents without chunks" message

2. `test_chunks_without_vectors_detected()`:
   - Create chunk without inserting into chunks_vec
   - Verify chunks_without_vec_count == 1
   - Verify [CRITICAL] prefix and "Chunks without vector" message

3. `test_duplicate_chunk_index_detected()`:
   - Insert two chunks with same chunk_index value
   - Verify duplicate_chunk_index_count == 1
   - Verify [CRITICAL] prefix and "Duplicate chunk_index" message

4. `test_url_level_mismatches_detected()`:
   - Create document with chunk + vector, then remove FTS entry
   - Verify url_level_mismatches dict contains the URL
   - Verify "Affected URLs" appears in issue summary

5. `test_existing_checks_still_work()`:
   - Run existing orphan_vec and fts_gap scenarios
   - Verify they still produce expected results

6. `test_is_consistent_false_on_new_failures()`:
   - Trigger a new failure condition
   - Verify is_consistent() returns False

7. `test_is_consistent_true_when_all_pass()`:
   - Create fully consistent state
   - Verify is_consistent() returns True and all new counts are 0

8. `test_url_mismatch_includes_repair_guidance()`:
   - Trigger URL-level mismatch
   - Verify "ingester.py --force" appears in issue summary

9. `test_new_fields_have_defaults()`:
   - Construct RagConsistencyReport without new fields
   - Verify defaults are applied correctly

## Compatibility considerations

- Existing tests may expect "failure" status for LLM exceptions — update assertions to match new "fallback" behavior
- New tests must pass alongside existing tests
- Backward compatibility test ensures old code can construct RagConsistencyReport without new fields

## Security considerations

- No security implications from this change

## Rollback considerations

- If the change causes issues, remove the new test functions

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `rag_consistency.py` | Unit — mock DB results for each new check | `pytest tests/test_rag_consistency* -v` | All pass |
| `rag_consistency.py` | Integration — verify full report with mixed failures | `pytest tests/test_rag_consistency* -v` | All pass |
| `models.py` | Unit — verify new fields are optional defaults | `pytest tests/test_models* -v` | All pass |
| Full suite | Regression | `uv run pytest -v` | All pass |

## Out of scope

- Changes to SQLite schema
- Changes to embedding service
- Changes to RRF fusion logic
- Changes to augment formatting

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260730-071318_require.md
- Source plan: plans/20260730-080052_plan.md
- Source implementation procedure: N/A
- Generated at: 20260730-095051
- Related target files: tests/test_rag_consistency.py
