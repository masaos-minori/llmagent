# DB API and Operations

- Schema → [90_shared_04_db_architecture_and_schema.md](90_shared_04_db_architecture_and_schema.md)

## 1. Purpose

Documents the `SQLiteHelper` API, `db/store.py` protocol groups and implementations,
`ToolResultStore`, memory-related table operations, maintenance functions, corruption
recovery, error handling, and the operational verification plan.

---

## 2. `SQLiteHelper` (`db/helper.py`)

### Constructor

```python
SQLiteHelper(target: DbTarget | str = "rag")
# DbTarget.RAG, DbTarget.SESSION, DbTarget.WORKFLOW, or string literal
# "rag" → rag.sqlite  |  "session" → session.sqlite  |  "workflow" → workflow.sqlite
# Invalid target → ValueError
```

`build_db_config()` is called in `__init__()` to resolve all paths and settings.

### `open()` method

```python
def open(
    self,
    *,
    write_mode: bool = False,
    row_factory: bool = False,
    load_vec: bool | None = None,
) -> "SQLiteHelper"
```

Returns `self` for chaining. Sets `self.conn`.

| Argument | Effect |
|---|---|
| `write_mode=True` | Adds `PRAGMA foreign_keys=ON` |
| `row_factory=True` | Sets `conn.row_factory = sqlite3.Row` (column name access) |
| `load_vec=None` | Uses target default: `rag` → True; `session`/`workflow` → False |
| `load_vec=True` | Force load sqlite-vec extension |
| `load_vec=False` | Skip vec extension |

Always applies: vec load (if enabled), WAL, NORMAL sync, busy_timeout.

### Core methods

| Method | Signature | Notes |
|---|---|---|
| `execute(sql, params=())` | `-> sqlite3.Cursor` | `params`: tuple (positional `?`) or dict (named `:name`). `RuntimeError` if conn None; `ValueError` if sql empty |
| `executemany(sql, params_seq)` | `-> sqlite3.Cursor` | Batch INSERT/UPDATE. `params_seq: list[tuple[Any, ...]]` |
| `fetchall(sql, params=())` | `-> list[Any]` | `execute + fetchall` combined |
| `commit()` | `-> None` | Logs ERROR on `sqlite3.OperationalError` then re-raises |
| `close()` | `-> None` | Idempotent; logs WARNING on close error but does not raise |
| `begin_immediate()` | `@contextmanager` | `BEGIN IMMEDIATE ... COMMIT`; auto-ROLLBACK on `Exception` (not `BaseException`) |
| `begin_exclusive()` | `@contextmanager` | `BEGIN EXCLUSIVE ... COMMIT`; for VACUUM/DDL only; auto-ROLLBACK on `Exception` (not `BaseException`) |
| `health_check()` | `-> DbHealthMetrics` | `PRAGMA quick_check`; returns `{journal_mode, integrity, page_count, page_size, freelist_count, db_size_bytes}` |
| `checkpoint(mode="TRUNCATE")` | `-> WalCheckpointCounts` | Modes: PASSIVE/FULL/RESTART/TRUNCATE. Invalid mode → `ValueError` |
| `vacuum()` | `-> None` | In-place DB rebuild; requires ~2× DB size free disk; call outside transaction |

### Typical usage patterns

```python
# Read-only query
with SQLiteHelper("rag").open(row_factory=True) as db:
    rows = db.fetchall("SELECT url, title FROM documents WHERE lang = :lang", {"lang": "ja"})

# Write with transaction
with SQLiteHelper("session").open(write_mode=True) as db:
    db.execute("INSERT INTO sessions DEFAULT VALUES")
    db.commit()

# Atomic multi-statement write
with SQLiteHelper("rag").open(write_mode=True) as db:
    with db.begin_immediate():
        db.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        db.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        # COMMIT auto on exit; ROLLBACK on exception
```

---

## 3. Protocol Groups in `db/store.py`

All protocols are `@runtime_checkable` — `isinstance()` check works.

### Embedding helpers

```python
from db.store import get_embedding_dims, get_embedding_bytes, validate_embedding_blob

dims = get_embedding_dims()      # reads common.toml::embedding_dims; default 384
nbytes = get_embedding_bytes()   # dims * 4 (float32)
validate_embedding_blob(blob)    # TypeError if not bytes; ValueError if wrong size
```

### `VectorStore` Protocol

```python
class VectorStore(Protocol):
    def vec_insert(self, chunk_id: int, embedding: bytes) -> None: ...
    def vec_search(self, embedding: bytes, k: int) -> list[tuple[int, float]]: ...
    def vec_delete(self, chunk_id: int) -> None: ...
    def vec_count(self) -> int: ...
```

- `vec_search` returns `(chunk_id, distance)` pairs
- `vec_delete`: no-op if not found

### `DocumentStore` Protocol

```python
class DocumentStore(Protocol):
    def doc_upsert(self, url, title, lang, etag, last_modified) -> int: ...
    def doc_get(self, url) -> dict | None: ...
    def doc_list(self, lang, limit) -> list[dict]: ...
    def doc_delete(self, url) -> bool: ...
    def chunk_insert(self, doc_id, index, content, normalized) -> int: ...
    def chunk_count(self) -> int: ...
```

- `doc_upsert`: SELECT then UPDATE/INSERT; returns `doc_id`
- `doc_get` returns `{doc_id, url, title, lang, fetched_at, etag, last_modified}` or `None`
- `doc_list` returns `{doc_id, url, title, lang, fetched_at}` sorted `fetched_at DESC`
- `doc_delete`: deletes document + cascades to chunks; returns `True` if found
- `chunk_insert` uses `chunk_index` column in `chunks` table

### `SessionStore` Protocol

```python
class SessionStore(Protocol):
    def session_create(self) -> int: ...
    def session_list(self, limit) -> list[dict]: ...
    def session_rename(self, session_id, title) -> None: ...
    def session_delete(self, session_id) -> None: ...
    def message_save(self, session_id, role, content, tool_calls) -> None: ...
    def message_list(self, session_id) -> list[dict]: ...
```

- `session_list` returns `{session_id, created_at, title}` sorted `created_at DESC`
- `session_delete` cascades to messages (ON DELETE CASCADE)
- `message_list` returns `{role, content, tool_calls}` in `message_id ASC` order
- `tool_calls` is `str | None` (JSON string)

---

## 4. SQLite Backend Implementations

| Class | Protocol | Constructor | Notes |
|---|---|---|---|
| `SQLiteVectorStore(db)` | `VectorStore` | `db: SQLiteHelper` | Validates embedding BLOB size in `vec_insert` |
| `SQLiteDocumentStore(db)` | `DocumentStore` | `db: SQLiteHelper` | `doc_upsert` does SELECT then UPDATE/INSERT |
| `SQLiteSessionStore(db)` | `SessionStore` | `db: SQLiteHelper` | Session list returned `created_at DESC` |
| `SQLiteMemoryDeleteStore(db)` | `MemoryDeleteStore` | `db: SQLiteHelper` | Atomic cross-table delete for `memories`/`memories_fts`/`memories_vec` |

### `MemoryDeleteStore` / `SQLiteMemoryDeleteStore`

```python
from db.store import MemoryDeleteStore, SQLiteMemoryDeleteStore, MemoryDeleteResult

store = SQLiteMemoryDeleteStore(db)
result: MemoryDeleteResult = store.delete_memories_before(older_than_days=30)
# result.deleted — count of deleted entries
```

- Atomically deletes from `memories`, `memories_fts`, `memories_vec`
- `maintenance.py::prune_old_memories()` delegates to this class
- See [90_shared_90 DESIGN-01](90_shared_90_inconsistencies_and_known_issues.md) for responsibility boundary — resolved; extensibility rationale documented here
- `MemoryDeleteStore` is a Protocol (structural type) that exists to preserve the option of a non-SQLite backend in the future. Today, `SQLiteMemoryDeleteStore` is the sole implementation.

---

## 5. `ToolResultStore` (`db/tool_results.py`)

```python
class ToolResultStore:
    def store(
        self,
        session_id: int | None,
        turn: int,
        tool_name: str,
        args_masked: str,
        full_text: str,
        summary: str | None,
        is_error: bool,
    ) -> int | None   # new row id; raises on DB error

    def get(self, result_id: int) -> ToolResultRow | None

    def list_recent(
        self,
        session_id: int | None,
        n: int = 20,
    ) -> list[ToolResultRow]   # oldest-first; empty if session_id is None
```

**Purpose:** Stores full tool result text separately from LLM message history.
LLM context holds only summary/truncated version; full text is retrievable via `/tool show <id>`.

**Implementation detail:** `list_recent` internally fetches `ORDER BY id DESC LIMIT n`,
then reverses to return oldest-first.

See [90_shared_90 DESIGN-02](90_shared_90_inconsistencies_and_known_issues.md) for
responsibility boundary between `ToolResultStore` and `messages` table.

---

## 6. Memory-Related Tables and Operations (`MemoryStore`)

`MemoryStore` is defined in `agent/memory/store.py` (NOT `db/`). It uses `SQLiteHelper("session")`.

Key methods:

| Method | Description |
|---|---|
| `add(entry, embedding=None)` | Insert into `memories` + `memories_fts`; optionally `memories_vec` |
| `upsert(entry, embedding=None)` | `INSERT OR REPLACE` + sync FTS/vec |
| `delete(memory_id)` | Delete 1 entry; returns `True` if found |
| `search_by_type(type, limit)` | Filter by `memory_type`; ordered `importance DESC, pinned DESC` |
| `pin(memory_id)` / `unpin(memory_id)` | Toggle pinned flag |
| `clear_by_session(session_id)` | Delete all entries for session |
| `count_vec()` | Row count in `memories_vec`; returns `0` if vec0 not loaded |

`prune_old_memories(db, older_than_days)` in `maintenance.py` delegates to
`SQLiteMemoryDeleteStore` for cross-table deletion.

---

## 7. Maintenance Functions (`db/maintenance.py`)

All functions accept a `SQLiteHelper` instance and delegate low-level operations back to it.

| Function | Signature | Description |
|---|---|---|
| `checkpoint_wal(db, mode=None)` | `-> WalCheckpointCounts` | WAL flush; default mode from `common.toml::sqlite_wal_checkpoint_mode` (default `TRUNCATE`) |
| `vacuum_db(db, mode=STRICT)` | `-> MaintenanceResult` | Delegates to `db.vacuum()`; call outside transaction |
| `purge_old_sessions(db, cfg=None, mode=STRICT)` | `-> MaintenanceResult` | Age-based + count-based session purge; commits internally |
| `prune_old_memories(db, older_than_days, mode=STRICT)` | `-> MaintenanceResult` | Delete old memories via `SQLiteMemoryDeleteStore` |
| `rotate_rag_db(archive_dir=None)` | `-> Path` | Archive `rag.sqlite` with timestamp suffix via SQLite online backup API |
| `rotate_session_db(archive_dir=None)` | `-> Path` | Archive `session.sqlite` |
| `rotate_db(archive_dir=None)` | `-> tuple[Path, Path]` | Archive both DBs; returns `(rag_dest, session_dest)` |
| `recover_corruption(backup_path=None, *, target="rag", dry_run=False)` | `-> RecoveryResult` | Integrity check + VACUUM or restore from backup |
| `check_rag_consistency(db)` | `-> RagConsistencyReport` | Read-only: chunks/FTS/vec row counts + orphan detection |

### `MaintenanceMode` and `MaintenanceResult`

```python
class MaintenanceMode(StrEnum):
    STRICT = "strict"        # Exceptions propagate (default; preserves existing behavior)
    BEST_EFFORT = "best_effort"  # Exceptions caught, logged, returned in MaintenanceResult

@dataclass(frozen=True)
class MaintenanceResult:
    success: bool
    action: str              # "vacuum" | "vacuum_failed" | "purge" | "purge_failed" | "prune" | "prune_failed"
    mode: MaintenanceMode
    detail: str | None = None  # Exception message on failure
    data: dict | None = None   # e.g. {"age_deleted": N, "count_deleted": N} or {"deleted": N}
```

**Mode semantics:**
- `STRICT` (default): behavior unchanged from pre-mode code — exceptions propagate; on success a `MaintenanceResult(success=True)` is returned
- `BEST_EFFORT`: exceptions are caught, logged as ERROR, and returned as `MaintenanceResult(success=False, detail=str(exc))`; callers MUST check `result.success`

```python
from db.maintenance import MaintenanceMode, MaintenanceResult, vacuum_db

# STRICT mode (default) — raises on error
result = vacuum_db(db)
assert result.success

# BEST_EFFORT mode — caller checks result
result = vacuum_db(db, mode=MaintenanceMode.BEST_EFFORT)
if not result.success:
    logger.error("vacuum failed: %s", result.detail)
```

### `RetentionConfig`

```python
@dataclass(frozen=True)
class RetentionConfig:
    max_sessions: int = 100   # max sessions to retain
    max_age_days: int = 90    # purge sessions older than N days (0 = disabled)
```

`RetentionConfig.from_config()` reads `common.toml::sqlite_retention_max_sessions` /
`sqlite_retention_max_age_days`.

### `purge_old_sessions` behavior

1. If `max_age_days > 0`: delete sessions older than N days (`age_deleted`)
2. If remaining count > `max_sessions`: delete oldest excess sessions (`count_deleted`)
3. Assumes `messages` has `ON DELETE CASCADE`
4. Calls `db.conn.commit()` at end
5. Returns `MaintenanceResult(success=True, data={"age_deleted": N, "count_deleted": N})`

### `prune_old_memories` behavior

1. Collect `memory_id` values older than `older_than_days`
2. Delete from `memories`, `memories_fts`, `memories_vec`
3. Call `db.commit()`
4. Returns `MaintenanceResult(success=True, data={"deleted": N})`
5. On failure in STRICT mode: exception propagates; in BEST_EFFORT mode: returns `success=False`

---

## 8. Corruption Recovery

```python
from db.maintenance import recover_corruption, RecoveryResult

result = recover_corruption(
    backup_path="/opt/llm/db/backup/rag.sqlite",
    target="rag",
    dry_run=False,
)
```

### `RecoveryResult`

```python
@dataclass(frozen=True)
class RecoveryResult:
    success: bool
    action: str      # "vacuum" | "vacuum_failed" | "restored" | "no_backup" | "error"
    detail: str | None = None
    dry_run: bool = False
```

### `RagConsistencyReport`

```python
@dataclass(frozen=True)
class RagConsistencyReport:
    chunks: int
    fts: int
    vec: int
    orphan_vec_count: int
    fts_gap: int
```

**Usage:**

```python
from db.maintenance import check_rag_consistency, is_consistent, summarize_issues

report = check_rag_consistency(db)
if not is_consistent(report):
    for issue in summarize_issues(report):
        print(issue)
```

- `fts_gap > 0` → FTS trigger missed some inserts; fix: `/db rebuild-fts`
- `orphan_vec_count > 0` → vec trigger failed; fix: re-ingest affected URLs
- Read-only; does not repair inconsistencies.

**Recovery flow:**
1. `PRAGMA integrity_check` on `target` DB
2. `dry_run=True` → return result without modifying DB
3. Result `"ok"` → run VACUUM; return `action="vacuum"` (or `"vacuum_failed"`)
4. Result not `"ok"` → archive corrupt file as `{stem}_corrupt_{timestamp}{suffix}`; copy `backup_path`; return `action="restored"` (or `"no_backup"` / `"error"`)

**Rotate archive format:** `{stem}_{YYYYMMDD_HHMMSS}{suffix}` in `archive_dir`
(default: `common.toml::sqlite_archive_dir` → `/opt/llm/db/archive`).
Uses SQLite online backup API to preserve WAL integrity.

---

## 9. Error Handling

| Error | Behavior |
|---|---|
| `sqlite3.OperationalError` (busy/locked) | Auto-wait via `PRAGMA busy_timeout` (default 30s) |
| `sqlite3.IntegrityError` | Propagates to caller; does not occur in upsert paths |
| sqlite-vec load error | `sqlite3.OperationalError` → connection failure |
| Schema DDL failure | Exception re-raised from `executescript()` |
| Integrity check failure | Error logged + backup restore attempted |
| `prune_old_memories` failure | STRICT: exception propagates; BEST_EFFORT: returns `MaintenanceResult(success=False)` |
| `commit()` error | Logs WARNING + re-raises `sqlite3.OperationalError` |
| `close()` error | Logs WARNING; does NOT raise |

---

## 10. Verification Plan

```bash
# Schema initialization
uv run pytest tests/test_create_schema.py

# DB maintenance
uv run pytest tests/test_db_maintenance.py

# Tool results
uv run pytest tests/test_tool_result_store.py

# Type check
uv run mypy scripts/db/

# Full integration: create DB → check all tables exist
python -c "from db.create_schema import create_schema; create_schema()"
sqlite3 /opt/llm/db/rag.sqlite ".tables"
sqlite3 /opt/llm/db/session.sqlite ".tables"
```

---

## 11. AI Reference Guide

| Question | Answer |
|---|---|
| How to open a DB connection | `with SQLiteHelper("rag").open(row_factory=True) as db:` |
| How to write atomically | `with db.begin_immediate():` inside an `open(write_mode=True)` context |
| What does `target="workflow"` connect to | `workflow.sqlite` — task tracking DB |
| How to validate embedding BLOB | `validate_embedding_blob(blob)` from `db.store` |
| How to purge old sessions | `purge_old_sessions(db, RetentionConfig(...))` — returns `MaintenanceResult`; check `.success` |
| How to recover from corruption | `recover_corruption(backup_path=..., target="rag")` |
| Where does `ToolResultStore` save data | `tool_results` table in `session.sqlite` |
| Does `prune_old_memories` catch exceptions? | **STRICT** (default): propagates; **BEST_EFFORT**: caught and returned in `MaintenanceResult` |
| How to use BEST_EFFORT mode | Pass `mode=MaintenanceMode.BEST_EFFORT` to `vacuum_db`, `purge_old_sessions`, or `prune_old_memories` |
| How to check RAG consistency | `check_rag_consistency(db)` → `is_consistent(report)` + `summarize_issues(report)` |
