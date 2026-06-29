## 1. Goal
- Harden MDQ SQLite connection and transaction management to make concurrent reads during indexing safe, reduce "database locked" errors, and provide FTS5 consistency check/rebuild operations.

## 2. Scope
- **In-Scope**:
  - `_init_db()` in `service.py`: apply WAL mode and busy_timeout at DB-init time
  - `_get_db_connection()` in `service.py`: verify isolation level
  - `_index_single_file()` in `indexer.py`: wrap DELETE + INSERT sequence in an explicit write transaction; make it atomic-replace per document
  - `refresh_paths()` in `indexer.py`: ensure `conn.commit()` is inside proper transaction scope
  - `_delete_file_from_index()` in `indexer.py`: remove trigger drop/recreate pattern; use proper FTS delete inside transaction
  - `fts_consistency_check()` in `service.py`: add integrity_check PRAGMA call
  - `fts_rebuild()` in `service.py`: verify it uses explicit BEGIN/COMMIT
  - Tests: add/extend unit tests for concurrent read safety, transaction atomicity, FTS consistency, and rebuild path
- **Out-of-Scope**:
  - DB schema changes (no column/table additions)
  - Embedding/vector table handling
  - `_migrate_from_legacy()` (legacy path not production-critical)
  - Summary cache logic

## 3. Requirements
### Functional
- All write operations in MDQ use explicit `BEGIN IMMEDIATE` ... `COMMIT` transactions
- WAL mode and busy_timeout applied at DB initialization time, not just in `_get_db_connection()`
- `_delete_file_from_index()` uses direct FTS delete instead of fragile trigger drop/recreate pattern
- `fts_consistency_check()` includes `PRAGMA integrity_check` on FTS table
- `fts_rebuild()` wrapped in explicit transaction with row count reporting
- Cache invalidation via `evict_server("mdq")` after write tool execution

### Non-functional
- Reduce "database locked" errors during concurrent indexing/search operations
- Ensure atomicity: partial index writes leave DB in consistent state
- No connection pooling; each operation opens and closes its own connection

## 4. Architecture
### Concurrency Model
- SQLite WAL mode separates reader and writer lock — WAL readers are never blocked by a writer
- `BEGIN IMMEDIATE` blocks read connections during indexing (safe in WAL mode)
- Single `ToolExecutor` instance per session; asyncio.Lock in `MdqService` sufficient for intra-process serialization
- SQLite WAL mode + `busy_timeout=5000ms` is the production guard against inter-process races

### Component Boundaries
```
MdqMCPServer (server.py)
  └── MdqService (service.py)
        ├── _init_db()          → WAL/busy_timeout on bare connect
        ├── _get_db_connection() → WAL/busy_timeout + isolation_level=None
        ├── _index_single_file() → BEGIN IMMEDIATE ... COMMIT (atomic replace)
        ├── refresh_paths()      → transaction-scope commit
        ├── _delete_file_from_index() → FTS delete inside transaction
        ├── fts_consistency_check() → PRAGMA integrity_check on chunks_fts
        └── fts_rebuild()       → BEGIN IMMEDIATE ... COMMIT with row counts
        └── Indexer (indexer.py)
              ├── _index_single_file() → atomic replace per document
              ├── refresh_paths()      → transaction-scope commit
              └── _delete_file_from_index() → FTS delete inside transaction
```

## 5. Module Design
### Dependency Graph
```
scripts/mcp/mdq/server.py (MCP server)
  └── scripts/mcp/mdq/service.py (MdqService — DB connection + indexing coordination)
        └── scripts/mcp/mdq/indexer.py (Indexer — per-document operations)
```

No changes to dependency direction. `search.py` uses `_get_db_connection()` for read-only queries; no change needed.

## 6. Interface Design
### New/Modified Methods

```python
# service.py
class MdqService:
    def _init_db(self) -> None:
        # NEW: apply WAL mode and busy_timeout on bare sqlite3.connect()
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.commit()
        conn.close()

    def _get_db_connection(self) -> sqlite3.Connection:
        # MODIFIED: add isolation_level=None for explicit transaction control
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def fts_consistency_check(self) -> tuple[str, int, int]:
        # MODIFIED: add PRAGMA integrity_check on chunks_fts
        # Returns (status, chunks_count, fts_count) or ("INCONSISTENT", chunks_count, fts_count)

    def fts_rebuild(self) -> str:
        # MODIFIED: wrap in BEGIN IMMEDIATE ... COMMIT; report row counts

# indexer.py
class Indexer:
    def _index_single_file(self, doc_path: Path) -> None:
        # MODIFIED: move conn.commit() outside per-section loop; use BEGIN IMMEDIATE
        with self.service._get_db_connection() as conn:
            with conn.begin_immediate():
                conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
                for section in sections:
                    conn.execute("INSERT INTO chunks ...", ...)
                # commit on exit

    def refresh_paths(self, paths: list[Path]) -> None:
        # MODIFIED: ensure index_state update committed atomically with file indexing

    def _delete_file_from_index(self, doc_id: str) -> None:
        # MODIFIED: replace trigger drop/recreate with direct FTS delete
        with self.service._get_db_connection() as conn:
            with conn.begin_immediate():
                rowids = conn.execute("SELECT id FROM chunks WHERE doc_id = ?", (doc_id,)).fetchall()
                for rowid in rowids:
                    conn.execute("INSERT INTO chunks_fts(chunks_fts, rowid) VALUES('delete', ?)", (rowid[0],))
                conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
                # commit on exit
```

### ToolExecutor Integration

```python
# tool_executor.py
class ToolExecutor:
    def evict_server(self, server_key: str) -> int:
        """Evict cache entries for all tools belonging to a server."""
        tool_names = get_all_mcp_tool_names(server_key)
        count = 0
        for key in list(self._cache.keys()):
            if key.startswith(tuple(f"{tn}:" for tn in tool_names)):
                del self._cache[key]
                count += 1
        return count

# tool_constants.py
MDQ_WRITE_TOOLS: frozenset[str] = frozenset({"index_paths", "refresh_index", "fts_rebuild"})

# tool_executor.py (modifying _SIDE_EFFECT_TOOLS)
_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"}) | MDQ_WRITE_TOOLS
```

## 7. Data Model & Serialization
No changes to data models. Existing `chunks`, `chunks_fts`, `documents`, `index_state` tables remain unchanged.

## 8. Error Handling & Resource Lifecycle
### Failure Modes
- `isolation_level=None` breaks existing callers relying on implicit transactions → audit all `_get_db_connection()` callers; if risk is high, keep autocommit and use `conn.execute("BEGIN IMMEDIATE")` explicitly only in write paths
- `BEGIN IMMEDIATE` blocks read connections during indexing → safe in WAL mode (WAL readers never blocked by writer)
- Removing trigger drop/recreate requires fetching rowids before deletion → fetch with `SELECT id FROM chunks WHERE doc_id = ?`; use in manual FTS delete; test with multi-chunk documents
- `fts_rebuild` locks the FTS table exclusively → document as maintenance operation; should not be called during active search traffic

### Resource Lifecycle
- All connections opened and closed per-operation (no pooling)
- WAL mode is persistent on DB file — set once, survives restarts
- `begin_immediate()` context manager auto-ROLLBACK on `Exception` (not `BaseException`)

## 9. Configuration
- `config/agent.toml` `[tool_safety_tiers]`: replace `mdq = "WRITE_DANGEROUS"` with per-tool entries:
  - `search_docs = "READ_ONLY"`, `get_chunk = "READ_ONLY"`, `outline = "READ_ONLY"`, `stats = "READ_ONLY"`, `grep_docs = "READ_ONLY"`
  - `index_paths = "WRITE_DANGEROUS"`, `refresh_index = "WRITE_DANGEROUS"`, `fts_rebuild = "WRITE_DANGEROUS"`
  - `fts_consistency_check = "ADMIN"`
- `common.toml` `sqlite_vec_so` path: use `config_loader` to read instead of hardcoded path in `service.py`

## 10. Test Strategy
### Unit Tests
- `test_mdq_service.py`: WAL mode check (`PRAGMA journal_mode` returns "wal"), `fts_consistency_check` with inconsistent FTS, `fts_rebuild` restoring consistency
- `test_mdq_incremental_refresh.py`: `_index_single_file` atomicity (inject error after first section insert; verify no partial document), `_delete_file_from_index` verifying chunks and FTS rows both removed
- `tool_executor`: `evict_server("mdq")` only evicts MDQ entries, non-MDQ entries remain
- `tool_constants`: `index_paths` in `_SIDE_EFFECT_TOOLS`, `is_side_effect("index_paths") == True`

### Integration Tests
- Concurrent `index_paths` calls on same service → operations serialized (asyncio.Lock)
- `search_docs` while `_is_indexing=True` → result contains `[WARNING: Index is being updated...]`
- `classify_risk(cfg, "search_docs", {})` == NONE; `classify_risk(cfg, "index_paths", {})` == MEDIUM

## 11. Implementation Plan
### Phase 1: Preparation / Behavior Lock
- Read existing tests (`test_mdq_service.py`, `test_mdq_incremental_refresh.py`) to understand coverage
- Add behavior-lock tests for `_index_single_file` atomicity
- Run baseline: `uv run pytest tests/test_mdq_service.py tests/test_mdq_incremental_refresh.py`

### Phase 2: Core Logic Implementation
- `service.py`: Set WAL mode and busy_timeout on bare `sqlite3.connect()` in `_init_db()`
- `service.py`: Add `isolation_level=None` to `_get_db_connection()` for explicit transaction control
- `indexer.py`: Move `conn.commit()` outside per-section loop; wrap DELETE + INSERT in `BEGIN IMMEDIATE` ... `COMMIT`
- `indexer.py`: Ensure `refresh_paths()` commits atomically
- `indexer.py`: Replace trigger drop/recreate with direct FTS delete in `_delete_file_from_index()`
- `service.py`: Add `PRAGMA integrity_check` to `fts_consistency_check()`
- `service.py`: Wrap `fts_rebuild()` in `BEGIN IMMEDIATE` ... `COMMIT`; add row counts
- `tool_constants.py`: Define `MDQ_WRITE_TOOLS` frozenset
- `tool_executor.py`: Import `MDQ_WRITE_TOOLS`; union into `_SIDE_EFFECT_TOOLS`; add `evict_server()` method
- `tool_runner.py`: Call `ctx.executor.evict_server("mdq")` after successful MDQ write tool execution
- `config/agent.toml`: Replace `mdq = "WRITE_DANGEROUS"` with per-tool tier entries

### Phase 3: Validation & Verification
- Run full mdq test suite: `uv run pytest tests/test_mdq_service.py tests/test_mdq_incremental_refresh.py tests/test_mdq_error_taxonomy.py tests/test_mdq_schema_migration.py -v`
- Run lint/type check: `uv run ruff check scripts/mcp/mdq/ && uv run mypy scripts/mcp/mdq/`
- Run full test suite: `uv run pytest`

## 12. Risks / Open Questions
- **Risk**: Changing `isolation_level=None` (autocommit mode) breaks existing callers → **Mitigation**: Audit all `_get_db_connection()` callers; if risk is high, keep autocommit and use `conn.execute("BEGIN IMMEDIATE")` explicitly only in write paths
- **Risk**: `fts_consistency_check` classified as `ADMIN` may surprise users who treat it as a read operation → **Mitigation**: Reclassifying as `READ_ONLY` is also defensible; defer to operator preference; document in config comment
- **UNK-01**: Whether `_init_db()` needs WAL mode at all (schema creation only) → **Resolution**: WAL is set globally on the DB file — setting it once is sufficient; verify `_get_db_connection()` is always called before any read path
- **UNK-02**: Whether `_delete_file_from_index()` trigger drop pattern causes issues in concurrent scenarios → **Resolution**: Add a test that calls refresh_paths with concurrent search; observe locking behavior
- **UNK-03**: Whether existing tests cover `fts_consistency_check` / `fts_rebuild` methods → **Resolution**: Read `test_mdq_service.py` before implementing; avoid duplicating existing tests
