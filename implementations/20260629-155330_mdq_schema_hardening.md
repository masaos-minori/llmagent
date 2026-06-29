# Implementation: Harden MDQ SQLite schema to production quality

## Goal

Harden the MDQ SQLite schema to production quality by fixing schema inconsistencies, adding FTS/stale counts to `stats()`, and correcting the `health()` endpoint that still references the legacy `sections` table.

## Scope

- **In-Scope**:
  - Fix `chunks` DDL in `service.py`: consolidate `id INTEGER PK AUTOINCREMENT` + `chunk_id TEXT UNIQUE` so that FTS5 rowid join is unambiguous and the requirement's stable `chunk_id` is the canonical primary key
  - Add `fts_count` and `stale_count` to `stats()` in `service.py`
  - Fix `health()` in `server.py` to reference `documents`/`chunks`/`chunks_fts` tables and triggers (`chunks_ai`, `chunks_ad`, `chunks_au`) instead of `sections`/`sections_fts`
  - Fix `_delete_file_from_index()` in `indexer.py`: replace fragile DROP/RECREATE trigger pattern with proper FTS5 content-table deletion (trigger fires automatically when `chunks` row is deleted)
  - Ensure migration path in `_migrate_from_legacy()` also creates correct triggers
  - Add or update tests in `test_mdq_schema_migration.py` and `test_mdq_service.py` to cover `stats()` FTS/stale counts and `health()` schema checks
- **Out-of-Scope**:
  - Hierarchy-aware parser replacement (separate requirement)
  - `token_count` computation (requires tokenizer integration; schema column already present)
  - Embedding/vector table changes
  - `chunk_summaries` table changes
  - Ingestion CLI / deployment changes

## Verification Results

### 1. Current state: `chunks` DDL has redundant `id` column

**File**: `scripts/mcp/mdq/service.py` — `_init_db()`
```sql
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id TEXT UNIQUE NOT NULL,
    ...
)
```

- Both `id INTEGER PK AUTOINCREMENT` and `chunk_id TEXT UNIQUE` exist
- This is redundant — `chunk_id` should be the canonical primary key
- Test fixture in `test_mdq_schema_migration.py` uses `chunk_id TEXT PRIMARY KEY` (no `id` column)
- Schema mismatch between test and production code

### 2. Current state: `stats()` missing FTS/stale counts

**File**: `scripts/mcp/mdq/service.py` — `stats()` method
- Returns document_count and chunk_count only
- Missing: fts_count (FTS5 row count), stale_count (documents with mtime > indexed_at)

### 3. Current state: `health()` references legacy tables

**File**: `scripts/mcp/mdq/server.py` — `health()` method
- References `sections` table instead of `chunks`
- References `sections_fts` instead of `chunks_fts`
- References `sections_ai/ad/au` triggers instead of `chunks_ai/ad/au`

### 4. Current state: `_delete_file_from_index()` has fragile trigger pattern

**File**: `scripts/mcp/mdq/indexer.py` — `_delete_file_from_index()` (lines ~278)
- Drops `chunks_ad` trigger before DELETE
- Recreates it after DELETE
- This prevents FTS cleanup during the delete window — FTS rows become orphaned

### 5. Health endpoint already fixed in separate plan

**File**: `scripts/mcp/mdq/server.py`
- The `health()` fix (sections → chunks) was already implemented in plan 20260629-154219
- `_check_stale_documents()` was rewritten for new schema
- No additional changes needed to server.py for this plan

### 6. UNK-01: `stats()` stale count unit mismatch

**File**: `service.py:584` — `indexed_at REAL NOT NULL`
**File**: `indexer.py:41` — `mtime_ns` stored as INTEGER nanoseconds

- `mtime_ns > indexed_at * 1e9` comparison needed (nanoseconds vs seconds)
- Resolution: use `mtime_ns > CAST(indexed_at * 1e9 AS INTEGER)` for minimal change

## Implementation

### Target file: `scripts/mcp/mdq/service.py`

#### Procedure

Consolidate DDL, add FTS/stale counts to stats(), ensure migration path is correct.

#### Details

**In `_init_db()` — consolidate chunks DDL:**
```sql
-- Before:
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id TEXT UNIQUE NOT NULL,
    ...
)
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, content) VALUES(new.rowid, new.content);
END;

-- After:
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    ...
)
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, content) VALUES(new.rowid, new.content);
END;
```

**In `_migrate_from_legacy()` — update chunks DDL:**
- Same change: `chunk_id TEXT PRIMARY KEY` instead of `id INTEGER PK AUTOINCREMENT` + `chunk_id TEXT UNIQUE`

**Add schema version detection in `_init_db()`:**
```python
# Check for old schema (has id column)
old_schema = self._db.execute("PRAGMA table_info(chunks)").fetchone()
if old_schema and old_schema["name"] == "id":
    # Rebuild with new schema
    self._db.execute("DROP TABLE IF EXISTS chunks_fts")
    self._db.execute("DROP TABLE IF EXISTS chunks")
    # Recreate with chunk_id TEXT PRIMARY KEY
    ...
```

**In `stats()` — add FTS and stale counts:**
```python
# Add after existing document_count query:
fts_count = conn.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0]
stale_count = conn.execute(
    "SELECT COUNT(*) FROM documents WHERE mtime_ns > CAST(indexed_at * 1e9 AS INTEGER)"
).fetchone()[0]

# Update return string to include fts_count and stale_count
```

### Target file: `scripts/mcp/mdq/indexer.py`

#### Procedure

Remove DROP/RECREATE trigger pattern in `_delete_file_from_index()`.

#### Details

**In `_delete_file_from_index()` — remove trigger manipulation:**
```python
# Before:
conn.execute("DROP TRIGGER IF EXISTS chunks_ad")
# ... delete operations ...
conn.execute("""
    CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
        DELETE FROM chunks_fts WHERE rowid = old.rowid;
    END;
""")

# After (just delete the chunk — FTS5 auto-sync trigger handles cleanup):
# No trigger manipulation needed — FTS5 with content=chunks will auto-delete
```

**Note**: If using external-content FTS5 (`content='chunks'`), the `chunks_ad` trigger is still needed for proper deletion. The fix is to NOT drop/recreate it — leave it in place. The DELETE operation will automatically fire the existing trigger.

### Target file: `scripts/mcp/mdq/search.py`

#### Procedure

Update FTS JOIN to use new schema (rowid instead of id).

#### Details

**In search.py — update FTS JOIN:**
```python
# Before:
f.rowid = c.id

# After (if chunk_id TEXT PK):
f.rowid = c.rowid

# Or if using content-table FTS5 approach:
c.chunk_id = f.chunk_id  -- if content='chunks' content_rowid='rowid'
```

### Target file: `tests/test_mdq_schema_migration.py`

#### Procedure

Update fixture to match new DDL.

#### Details

**In test fixture — change chunks creation:**
```python
# Before:
conn.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chunk_id TEXT UNIQUE NOT NULL,
        ...
    )
""")

# After:
conn.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id TEXT PRIMARY KEY,
        ...
    )
""")
```

### Target file: `tests/test_mdq_service.py`

#### Procedure

Add tests for stats() FTS/stale counts.

#### Details

**Append to TestServiceStats:**
```python
def test_stats_returns_fts_count(self) -> None:
    """stats() includes fts_count."""
    # Index a file first, then check stats
    ...

def test_stats_returns_stale_count(self) -> None:
    """stats() includes stale_count for documents with mtime > indexed_at."""
    ...
```

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `service.py` DDL | Unit test: create DB, verify table columns via PRAGMA table_info(chunks) | `tests/test_mdq_schema_migration.py` | chunk_id is PK, no id column |
| `service.py` stats() | Unit test: insert docs/chunks, call stats, verify FTS count and stale count present | `tests/test_mdq_service.py` | stats() output contains fts_count and stale_count |
| `search.py` FTS JOIN | Unit test: index a file, search, verify results returned | `tests/test_mdq_service.py::TestSearch` | Search returns correct chunks |
| `indexer.py` delete | Unit test: index file, delete file, call _delete_file_from_index, verify chunks + FTS rows gone | `tests/test_mdq_incremental_refresh.py` | chunks and FTS rows removed without trigger error |
| `server.py` health | Already fixed in plan 20260629-154219 — no additional changes needed | N/A | Health endpoint uses correct tables |
| Full test suite | Regression check | `uv run pytest tests/ -x -q` | All tests pass |
| Lint + type check | Ruff + mypy | `uv run ruff check scripts/mcp/mdq/ && uv run mypy scripts/mcp/mdq/` | No errors |

## Risks & Mitigations

- **Risk**: Removing `id` column breaks `search.py` FTS JOIN (`f.rowid = c.id`) silently at runtime → **Mitigation**: Fix search.py in the same PR; add integration test that actually runs a search
- **Risk**: Existing production `mdq.sqlite` has `id` column schema — migration detection must be robust → **Mitigation**: Add explicit `PRAGMA table_info(chunks)` check in `_init_db()` to detect old schema and trigger rebuild
- **Risk**: `chunks_fts` external-content table is out of sync after trigger removal in `_delete_file_from_index()` → **Mitigation**: Add `fts_consistency_check` assertion in deletion test; existing `fts_consistency_check()` tool can be used as post-condition
- **Risk**: `health()` fix changes the degraded response conditions — production monitoring may rely on specific error strings → **Mitigation**: Keep same JSON structure; only update table name checks (already done in plan 20260629-154219)
- **Risk**: `stats()` stale count uses unit-mismatched comparison (`mtime_ns` INTEGER nanoseconds vs `indexed_at` REAL seconds) → **Mitigation**: Use `mtime_ns > CAST(indexed_at * 1e9 AS INTEGER)` and add a unit test with known values to verify
