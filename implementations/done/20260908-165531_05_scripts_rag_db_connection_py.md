# Implementation Procedure: Refactor RAG Pipeline DB Connection Management

## Goal

Create `RagDatabaseConnection` context manager wrapping the SQLiteHelper open/close lifecycle currently inline in `augment()`, reducing `pipeline.py` complexity and isolating database connection handling.

## Scope

- Create `scripts/rag/db_connection.py` with `RagDatabaseConnection` context manager
- Update `augment()` to use `RagDatabaseConnection` instead of inline `SQLiteHelper` construction
- Update test files that directly assign private SQLite attributes
- Create unit tests for open/close lifecycle and exception handling

## Assumptions

- The Issue states `__init__` "stores five SQLite-related attributes" but names only four (`_rag_db_path`, `_sqlite_vec_so`, `_sqlite_timeout`, `_sqlite_busy_timeout_ms`); direct code reading confirms exactly these four exist — uses four, not five.
- `RagDatabaseConnection` wraps the `SQLiteHelper(...).open(row_factory=True)` construction confirmed in `augment()` at `scripts/rag/pipeline.py:468-478`.

## Design decisions

1. **Context manager protocol** — `__enter__` opens, `__exit__` closes; ensures deterministic resource cleanup.
2. **Accept same parameters as current inline construction** — `_rag_db_path`, `_sqlite_vec_so`, `_sqlite_timeout`, `_sqlite_busy_timeout_ms`.

## Alternatives considered

- Making `RagDatabaseConnection` a simple wrapper without context manager: rejected because explicit close is needed for deterministic cleanup.
- Using dependency injection for `SQLiteHelper`: rejected because it would require changing `RagPipeline.__init__` signature (backward-compatibility constraint).

## Implementation

### Target file

`scripts/rag/db_connection.py`

### Procedure

1. Create `scripts/rag/db_connection.py` with a module docstring referencing `pipeline.py` as the source of the DB connection logic.
2. Define `RagDatabaseConnection` class implementing context manager protocol:
   - `__init__(self, rag_db_path, sqlite_vec_so, sqlite_timeout, sqlite_busy_timeout_ms)`
   - `__enter__(self)` → opens `SQLiteHelper(rag_db_path, row_factory=True)`, sets timeout/busy-timeout
   - `__exit__(self, exc_type, exc_val, exc_tb)` → closes connection
3. Update `augment()` to use `with RagDatabaseConnection(...) as conn:` instead of inline `SQLiteHelper(...).open(row_factory=True)`.
4. Update `tests/rag/test_pipeline_http_result_kind.py` and `tests/rag/test_rag_http_mode.py` to construct/patch the new structure instead of directly assigning moved private attributes (per UNK-01's preferred resolution: rewrite tests directly).
5. Create `tests/rag/test_db_connection.py` covering open/close lifecycle and exception handling.

### Method

Context manager extraction: wrap existing `SQLiteHelper` open/close pattern in `__enter__`/`__exit__`, verify parameter list matches current inline construction.

### Details

- Current DB connection location in source: `scripts/rag/pipeline.py:468-478`
- Parameters: `_rag_db_path`, `_sqlite_vec_so`, `_sqlite_timeout`, `_sqlite_busy_timeout_ms`
- Uses `row_factory=True` for dict-like row access
- Exception handling during open must propagate errors; `__exit__` must ensure cleanup even on failure

## Compatibility considerations

- `augment()`'s behavior must remain identical; only the connection management changes.
- Test files that directly assign `pipeline._rag_db_path`/`_sqlite_vec_so`/`_sqlite_timeout`/`_sqlite_busy_timeout_ms`/`_augment_refiner` must be updated (REQ-007).

## Security considerations

- Database path and credentials are handled securely; no new secrets exposed.

## Rollback considerations

- Revert: remove `db_connection.py`, restore inline `SQLiteHelper` construction in `augment()`, revert test file changes.
- Low risk: the context manager can be removed cleanly; rollback restores original structure.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/db_connection.py` | Unit | `uv run pytest tests/rag/test_db_connection.py -v` | `open`/`close` lifecycle and exception handling correct |

## Completion criteria

- `RagDatabaseConnection` context manager exists in `scripts/rag/db_connection.py`.
- `augment()` uses `RagDatabaseConnection` instead of inline construction.
- Test files pass against the new structure.
- `tests/rag/test_db_connection.py` passes with ≥80% branch coverage.
- No regression in existing pipeline integration tests.

## Out of scope

- Migrating DB abstraction layer.
- Adding connection pooling.
- Changing SQLite connection parameters.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `scripts/rag/db_connection.py` with `RagDatabaseConnection` | Completed | — | — | File exists; context manager defined |
| 2 | Update `augment()` to use `RagDatabaseConnection` | Completed | — | — | Updated in prior cycle |
| 3 | Update test files (REQ-007) | Completed | — | — | Test files updated in prior cycle |
| 4 | Create `tests/rag/test_db_connection.py` | Completed | — | — | Test file exists |
| 5 | Run validation sequence | Completed | — | — | Validation passed in prior cycle |

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
- **Requirement ID**: REQ-005 — create `RagDatabaseConnection` context manager, update test files
- **Source issue**: issues/20260908-105318_refactor_rag_pipeline_complexity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-165531_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-165531
- **Related target files**: scripts/rag/db_connection.py
