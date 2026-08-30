## Goal

Isolate document CRUD operations from `ingester.py` into `scripts/rag/ingestion/document_persistence.py`, creating `DocumentStore` as the single source of truth for document persistence.

## Scope

- Create `scripts/rag/ingestion/document_persistence.py` with `DocumentStore` class
- Move `_get_or_create_document` method to `DocumentStore.get_or_create()`
- Move `_insert_document` method to `DocumentStore.insert()`
- Update imports in `ingester.py` to use `DocumentStore`
- Write tests in `tests/test_ingester_document_persistence.py`

## Assumptions

- `DocumentManager` remains as-is (already extracted in Issue #001/#002)
- `_VALID_LANGS` constant remains in `ingester.py` (not moved here)
- `SQLiteHelper` is passed via dependency injection rather than constructed internally
- `RagConsistencyReport` is not touched by this module
- Force/replacement logic is delegated to `DocumentManager.handle_existing_document()`

## Design decisions

- `DocumentStore` owns the lang validation and document row insertion logic — these are persistence concerns
- `get_or_create()` returns `(doc_id: int | None, skip: bool, replace: bool)` — same contract as current `_get_or_create_document`
- Lang validation (`_validate_lang`) is kept within `DocumentStore` since it's a persistence invariant
- `SQLiteHelper` is injected via constructor to avoid coupling to global config

## Alternatives considered

- **Lang validation in separate validator module**: Would isolate validation but couples it to persistence domain. Rejected — lang is a document property.
- **DocumentStore constructs its own SQLiteHelper**: Would simplify constructor but hides dependency. Rejected — DI is preferred.
- **Returning a `DocumentResult` typed dict**: Would be cleaner than tuple but adds ceremony. Deferred until proven necessary.

## Implementation

### Target file

`scripts/rag/ingestion/document_persistence.py`

### Procedure

1. Create `scripts/rag/ingestion/document_persistence.py` with the `DocumentStore` class definition
2. Copy `_validate_lang` method into `DocumentStore.validate_lang(lang: str) -> bool`
3. Copy `_get_or_create_document` method body into `DocumentStore.get_or_create(...)`
4. Copy `_insert_document` method body into `DocumentStore.insert(db: SQLiteHelper, url: str, title: str, lang: str, etag: str | None, last_modified: str | None, chunking_strategy: str, fetched_at: str) -> sqlite3.Cursor`
5. Preserve all SQL statements exactly as-is
6. Preserve `db.execute()` calls and `cursor.lastrowid` usage
7. Preserve `DocumentManager.handle_existing_document()` delegation
8. Update `ingester.py` import: replace inline methods with `DocumentStore` instantiation
9. Replace all `self._validate_lang(...)` calls with `self.doc_store.validate_lang(...)`
10. Replace all `self._get_or_create_document(...)` calls with `self.doc_store.get_or_create(...)`
11. Replace all `self._insert_document(...)` calls with `self.doc_store.insert(...)`
12. Remove `_validate_lang`, `_get_or_create_document`, `_insert_document` methods from `RagIngester`
13. Remove unused imports: `sqlite3` (if no longer referenced after removal)

### Method

```python
class DocumentStore:
    def __init__(
        self,
        db: SQLiteHelper,
        doc_mgr: DocumentManager,
    ) -> None: ...

    def validate_lang(self, lang: str) -> bool:
        """Return True when lang is a valid value."""
        return lang in _VALID_LANGS

    def get_or_create(
        self,
        url: str,
        title: str,
        lang: str,
        force: bool,
        *,
        etag: str | None = None,
        last_modified: str | None = None,
        chunking_strategy: str = "text",
        fetched_at: str,
    ) -> tuple[int | None, bool, bool]:
        """Register a URL in documents and return its doc_id and whether replacement is needed."""
        # Copy body of RagIngester._get_or_create_document verbatim

    def insert(
        self,
        db: SQLiteHelper,
        url: str,
        title: str,
        lang: str,
        etag: str | None,
        last_modified: str | None,
        chunking_strategy: str,
        fetched_at: str,
    ) -> sqlite3.Cursor:
        """Insert a document row and return the cursor."""
        # Copy body of RagIngester._insert_document verbatim
```

### Details

- `_VALID_LANGS` is imported from `ingester.py` (same frozenset)
- `DocumentManager` is imported from `rag.ingestion.document_manager` (unchanged)
- `SQLiteHelper` is imported from `db.helper` (unchanged)
- `sqlite3.Cursor` type hint preserved
- SQL: `"SELECT doc_id FROM documents WHERE url = ?"` — unchanged
- SQL: `"INSERT INTO documents (url, title, lang, etag, last_modified, chunking_strategy, fetched_at) VALUES (?, ?, ?, ?, ?, ?, ?)"` — unchanged
- `db.execute()` returns `sqlite3.Cursor` — preserved
- `cursor.lastrowid` access — preserved
- `doc_mgr.handle_existing_document(url, existing_doc_id, force, etag, last_modified, fetched_at, lambda u: u.startswith("file://"))` — preserved
- Error case: `ValueError(f"unsupported lang value: {lang!r} (must be one of {sorted(_VALID_LANGS)})")` — preserved

## Compatibility considerations

- Public API: `RagIngester.__init__` signature changes — callers must now pass a `DocumentStore` instance instead of raw config dict
- Backward compatibility: `RagIngester` constructor should accept both `config: dict | None` (legacy) and `doc_store: DocumentStore` (new) with deprecation warning for legacy mode
- `SQLiteHelper` lifecycle stays with `RagIngester` (owns the connection)
- `DocumentManager` lifecycle stays with `RagIngester` (owned by caller)

## Security considerations

- No new secrets or credentials introduced
- SQL uses parameterized queries exclusively (no string interpolation)
- Lang validation prevents injection of invalid values
- Error messages do not leak sensitive data (only path names and first 60 chars of content)

## Rollback considerations

- Revert: restore `_validate_lang`, `_get_or_create_document`, `_insert_document` methods in `RagIngester`
- Revert: remove `DocumentStore` class from `document_persistence.py`
- Revert: restore original imports in `ingester.py`
- Revert: restore original `RagIngester.__init__` parameter
- Safe rollback: no database schema changes, no file system changes during refactoring

## Validation plan

1. Run `uv run pytest tests/test_ingester_document_persistence.py -v`
2. Verify `ingester.py` line count reduced by ~40 lines
3. Verify no import errors: `python -c "from rag.ingestion import ingester"`
4. Verify cyclomatic complexity of `ingest_all` and `ingest_url_group` unchanged (still high — Phase 8 will reduce)
5. Mutation testing: `uv run mutmut run --paths-to-mutate=scripts/rag/ingestion/document_persistence.py`

## Completion criteria

- [ ] `DocumentStore` class exists in `scripts/rag/ingestion/document_persistence.py`
- [ ] `validate_lang()` method returns `bool` matching original contract
- [ ] `get_or_create()` method returns `(int | None, bool, bool)` matching original contract
- [ ] `insert()` method returns `sqlite3.Cursor` matching original contract
- [ ] All SQL statements preserved identically
- [ ] All `db.execute()` calls preserved with identical parameters
- [ ] `RagIngester` delegates to `DocumentStore` for all document operations
- [ ] Tests pass: `uv run pytest tests/test_ingester_document_persistence.py -v`
- [ ] No import errors across the project
- [ ] `ingester.py` line count reduced by at least 40 lines

## Out of scope

- Moving `RagConsistencyReport` to this module (stays in `db.models`)
- Changing `DocumentManager` behavior (deferred to later refactor)
- Adding migration logic for document schema changes (deferred)
- Implementing soft-delete for documents (deferred)
- Adding deduplication beyond current etag-based check (deferred)
- Moving `IngestionFailureReason` enum to this module (stays in `rag.exceptions`)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement DocumentStore class in scripts/rag/ingestion/document_persistence.py | Pending | — | — | |
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
- **Requirement ID**: REQ-003 — Extract document persistence module
- **Source issue**: [refactor] Separate ingester.py into multiple modules by concern (3/3)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-181706_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260830-093541
- **Related target files**: scripts/rag/ingestion/document_persistence.py
