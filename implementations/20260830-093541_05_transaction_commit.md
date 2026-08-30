## Goal

Isolate atomic commit logic from `ingester.py` into `scripts/rag/ingestion/transaction_commit.py`, creating `TransactionManager` as the single source of truth for transactional chunk commits.

## Scope

- Create `scripts/rag/ingestion/transaction_commit.py` with `TransactionManager` class
- Move `_commit_url_transaction` method to `TransactionManager.commit()`
- Update imports in `ingester.py` to use `TransactionManager`
- Write tests in `tests/test_ingester_transaction_commit.py`

## Assumptions

- `DocumentManager` remains as-is (already extracted in Issue #001/#002)
- `PreparedChunk` DTO remains in `ingester.py` (consumed by transaction commit downstream)
- `SQLiteHelper` is passed via dependency injection rather than owned by `TransactionManager`
- `floats_to_blob` utility is called internally by `TransactionManager`
- `dataclasses.replace` is used to update `doc_id` on prepared chunks after insertion

## Design decisions

- `TransactionManager` owns the BEGIN IMMEDIATE transaction boundary — it's the single source of truth for commit integrity
- `commit()` accepts all parameters needed for the transaction (doc_id, url, title, lang, etag, last_modified, chunking_strategy, fetched_at, force, replace, prepared_chunks)
- Transaction rollback is implicit via context manager (`with db.begin_immediate():`)
- File routing (`_move_to_registered`) happens AFTER commit success — outside the transaction boundary

## Alternatives considered

- **Two-phase commit pattern**: Would separate document insertion from chunk insertion but adds unnecessary complexity for SQLite. Rejected — single BEGIN IMMEDIATE is sufficient.
- **Separate DocumentCommit and ChunkCommit phases**: Would allow finer-grained rollback but couples caller to internal state. Rejected — atomicity requires single boundary.
- **Returning a `CommitResult` typed dict**: Would be cleaner than void return but adds ceremony. Deferred until proven necessary.

## Implementation

### Target file

`scripts/rag/ingestion/transaction_commit.py`

### Procedure

1. Create `scripts/rag/ingestion/transaction_commit.py` with the `TransactionManager` class definition
2. Copy `_commit_url_transaction` method body into `TransactionManager.commit(...)`
3. Preserve `with db.begin_immediate():` transaction boundary
4. Preserve conditional document insertion (`if doc_id is None or replace:`)
5. Preserve `doc_mgr.delete_existing_document(doc_id)` call when replacing
6. Preserve `self._insert_document(db, url, title, lang, etag, last_modified, chunking_strategy, fetched_at)` call
7. Preserve `cursor.lastrowid` retrieval and error check
8. Preserve `dataclasses.replace(pc, doc_id=new_doc_id)` for chunk doc_id updates
9. Preserve `self._insert_chunks_batch(db, prepared_chunks)` call
10. Preserve `self._move_to_registered(prepared_paths)` call after commit
11. Update `ingester.py` import: replace inline method with `TransactionManager` instantiation
12. Replace all `self._commit_url_transaction(...)` calls with `self.txn_manager.commit(...)`
13. Remove `_commit_url_transaction` method from `RagIngester`
14. Remove unused imports: `dataclasses` (if no longer referenced after removal)

### Method

```python
class TransactionManager:
    def __init__(
        self,
        db: SQLiteHelper,
        doc_mgr: DocumentManager,
    ) -> None: ...

    def commit(
        self,
        url: str,
        doc_id: int | None,
        prepared_chunks: list[PreparedChunk],
        prepared_paths: list[Path],
        force: bool,
        replace: bool,
        title: str,
        lang: str,
        *,
        etag: str | None,
        last_modified: str | None,
        chunking_strategy: str,
        fetched_at: str,
    ) -> None:
        """Atomically commit all database changes for a URL inside BEGIN IMMEDIATE transaction."""
        # Copy body of RagIngester._commit_url_transaction verbatim
```

### Details

- `PreparedChunk` is imported from `rag.models_data` (unchanged)
- `DocumentManager` is imported from `rag.ingestion.document_manager` (unchanged)
- `SQLiteHelper` is injected via constructor (new dependency)
- `dataclasses.replace` is imported from `dataclasses` (unchanged)
- SQL: `"INSERT INTO documents (url, title, lang, etag, last_modified, chunking_strategy, fetched_at) VALUES (?, ?, ?, ?, ?, ?, ?)"` — unchanged
- SQL: `"INSERT INTO chunks (doc_id, chunk_index, content, normalized_content, chunk_type, source_file) VALUES (?, ?, ?, ?, ?, ?)"` — unchanged
- SQL: `"INSERT INTO chunks_vec (chunk_id, embedding) VALUES (?, ?)"` — unchanged
- `db.begin_immediate()` context manager — preserved
- `doc_mgr.delete_existing_document(doc_id)` — preserved
- `cursor.lastrowid` access and `RuntimeError("Failed to retrieve lastrowid after insertion")` — preserved
- `dataclasses.replace(pc, doc_id=new_doc_id)` — preserved
- `self._insert_chunks_batch(db, prepared_chunks)` — preserved
- `self._move_to_registered(prepared_paths)` — preserved (after commit, not inside transaction)

## Compatibility considerations

- Public API: `RagIngester.__init__` signature changes — callers must now pass a `TransactionManager` instance instead of raw config dict
- Backward compatibility: `RagIngester` constructor should accept both `config: dict | None` (legacy) and `txn_manager: TransactionManager` (new) with deprecation warning for legacy mode
- `PreparedChunk` remains in `ingester.py` as shared type
- `SQLiteHelper` lifecycle stays with `RagIngester` (owns the connection)
- `DocumentManager` lifecycle stays with `RagIngester` (owned by caller)

## Security considerations

- No new secrets or credentials introduced
- SQL uses parameterized queries exclusively (no string interpolation)
- Transaction boundary ensures atomicity — partial writes are impossible
- Error messages do not leak sensitive data (only path names and first 60 chars of content)

## Rollback considerations

- Revert: restore `_commit_url_transaction` method in `RagIngester`
- Revert: remove `TransactionManager` class from `transaction_commit.py`
- Revert: restore original imports in `ingester.py`
- Revert: restore original `RagIngester.__init__` parameter
- Safe rollback: no database schema changes, no file system changes during refactoring

## Validation plan

1. Run `uv run pytest tests/test_ingester_transaction_commit.py -v`
2. Verify `ingester.py` line count reduced by ~35 lines
3. Verify no import errors: `python -c "from rag.ingestion import ingester"`
4. Verify cyclomatic complexity of `ingest_all` and `ingest_url_group` unchanged (still high — Phase 8 will reduce)
5. Mutation testing: `uv run mutmut run --paths-to-mutate=scripts/rag/ingestion/transaction_commit.py`

## Completion criteria

- [ ] `TransactionManager` class exists in `scripts/rag/ingestion/transaction_commit.py`
- [ ] `commit()` method preserves BEGIN IMMEDIATE transaction boundary
- [ ] All SQL statements preserved identically
- [ ] All `db.execute()` calls preserved with identical parameters
- [ ] `cursor.lastrowid` error handling preserved
- [ ] `dataclasses.replace(pc, doc_id=new_doc_id)` preserved
- [ ] `self._move_to_registered(prepared_paths)` called after commit (not inside transaction)
- [ ] `RagIngester` delegates to `TransactionManager` for all commit operations
- [ ] Tests pass: `uv run pytest tests/test_ingester_transaction_commit.py -v`
- [ ] No import errors across the project
- [ ] `ingester.py` line count reduced by at least 35 lines

## Out of scope

- Moving `PreparedChunk` DTO to this module (stays in `ingester.py`)
- Changing transaction isolation level (deferred)
- Adding distributed transaction support (deferred)
- Implementing soft-delete for documents (deferred)
- Adding migration logic for chunk schema changes (deferred)
- Moving `IngestionFailureReason` enum to this module (stays in `rag.exceptions`)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement TransactionManager class in scripts/rag/ingestion/transaction_commit.py | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005 — Extract transaction commit module
- **Source issue**: [refactor] Separate ingester.py into multiple modules by concern (3/3)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-181706_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260830-093541
- **Related target files**: scripts/rag/ingestion/transaction_commit.py
