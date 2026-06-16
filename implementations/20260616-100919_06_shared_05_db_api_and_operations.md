# Implementation: docs/06_shared_05_db_api_and_operations.md

## Goal

Create the DB API reference covering the full SQLiteHelper method set, store.py Protocol
definitions and implementations, maintenance.py functions, ToolResultStore, and MemoryStore.

## Scope

- Content from: `07_ref-sqlite.md` full API (SQLiteHelper methods, store.py, maintenance.py,
  ToolResultStore, MemoryStore, memory tables)
- Content from: `07_spec_db.md` §10-13 (public interfaces, error handling, validation, issues)
- Output: `docs/06_shared_05_db_api_and_operations.md`
- Not covered: schema DDL (→ 04), architecture overview (→ 04)

## Assumptions

- SQLiteHelper methods: open, execute, executemany, fetchall, commit, close,
  begin_immediate, begin_exclusive, health_check, checkpoint, vacuum
- store.py has 4 Protocols + 4 SQLite implementations + 2 helper functions
- maintenance.py functions: 7 total
- ToolResultStore:引数なしコンストラクタ; store/get/list_recent 3 メソッド

## Implementation

### Target file

`docs/06_shared_05_db_api_and_operations.md`

### Procedure

1. SQLiteHelper API method table: method | signature summary | key behavior notes
   - open(): load_vec=None behavior; PRAGMA order; returns self
   - execute(): tuple vs dict params; RuntimeError when conn=None
   - executemany(): batch INSERT/UPDATE; same error conditions
   - fetchall(): shorthand for execute+fetchall
   - commit(): OperationalError re-raised after log
   - close(): idempotent; swallows close exceptions
   - begin_immediate() / begin_exclusive(): contextmanager; auto ROLLBACK
   - health_check(): PRAGMA quick_check; returns DbHealthMetrics dict
   - checkpoint(): mode table (PASSIVE/FULL/RESTART/TRUNCATE)
   - vacuum(): requires transaction-outside call
2. Embedding helper functions: get_embedding_dims(), get_embedding_bytes(),
   validate_embedding_blob() — error conditions
3. store.py Protocols: VectorStore, DocumentStore, SessionStore, MemoryDeleteStore
   — method tables for each; @runtime_checkable note
4. store.py implementations: SQLiteVectorStore(db), SQLiteDocumentStore(db),
   SQLiteSessionStore(db), SQLiteMemoryDeleteStore(db) — constructor + delegation notes
5. maintenance.py: function table with full signatures and return types;
   RetentionConfig dataclass; RecoveryResult dataclass + action values table
6. ToolResultStore (db/tool_results.py): constructor; store/get/list_recent signatures;
   ToolResultRow fields; list_recent reverse sort implementation note
7. MemoryStore (agent/memory/store.py): all 11 methods with signatures

### Method

- Method tables: method | signature | description (3-col)
- Separate subsections per class/module
- Error handling table from spec §11

### Details

- list_recent: ORDER BY id DESC LIMIT ? then reversed() — returns ascending by id
- begin_immediate vs begin_exclusive: exclusive used for VACUUM/DDL only
- MemoryDeleteStore.delete_memories_before(older_than_days) → MemoryDeleteResult(deleted=N)
- prune_old_memories: no try/except — exceptions propagate (spec §13)

## Validation plan

- File exists at `docs/06_shared_05_db_api_and_operations.md`
- All SQLiteHelper methods documented (11 methods)
- All 4 Protocols with method tables
- maintenance.py all 7 functions with return types
- ToolResultStore 3 methods documented
- MemoryStore 11 methods documented
