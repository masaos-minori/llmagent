## Goal
- Restructure `docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` to remove overly detailed method tables, constructor signatures, open() argument tables, typical usage example code, and apply_connection_pragmas call site lists while explicitly preserving db.store as public API surface, store_protocols/store_impl as internal boundaries, responsibility division when extending DB store, SQLiteHelper operational role, raw sqlite3 connection PRAGMA application special case, transaction helper purpose, and VACUUM/DDL as exclusive operations.

## Scope
- **In-Scope**: 
  - `docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/DB chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should describe DB API boundary decisions as authoritative reference
- Existing internal links and cross-references must remain valid after editing

## Design decisions
### Part 1 (Module Boundaries):
- Compress Section 1a DB Store module boundaries table (lines 37-41): replace with prose describing import boundary rules
- Compress Section 1a DB store extension steps (lines 45-51): replace with prose describing extension pattern
- Compress Section 1a BAD/GOOD code examples (lines 53-59): replace with prose description of anti-pattern vs correct pattern
- Compress Section 2 constructor details (lines 67-83): replace with prose describing constructor parameters and their purposes
- Compress Section 2 open() argument table (lines 98-111): replace with prose describing open() parameter effects
- Compress Section 2 core methods table (lines 128-140): replace with prose describing each method's purpose and key behavior
- Compress Section 2 typical usage patterns (lines 144-160): replace with prose describing common usage patterns
- Compress Section 2 apply_connection_pragmas() call site list (line 124): replace with prose describing its purpose and callers
- Preserve: db.store is public API surface, store_protocols/store_impl are internal boundaries, responsibility division when extending DB store, SQLiteHelper operational role, raw sqlite3 connection PRAGMA application special case, transaction helper purpose, VACUUM/DDL as exclusive operations

## Alternatives considered
- Remove Section 1a entirely: rejected — module boundary decisions are fundamental architecture decision
- Replace all tables with prose: rejected — tabular format for module boundaries is efficient for reference
- Remove Section 2 entirely: rejected — SQLiteHelper operational role is critical for understanding DB access patterns

## Implementation
### Target files
- `docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which DB module boundary and helper design judgments are scattered across sections

2. **Phase 2: Core Logic Implementation**
   - Part 1: Compress Section 1a DB Store module boundaries table (lines 37-41)
   - Part 1: Compress Section 1a DB store extension steps (lines 45-51)
   - Part 1: Compress Section 1a BAD/GOOD code examples (lines 53-59)
   - Part 1: Compress Section 2 constructor details (lines 67-83)
   - Part 1: Compress Section 2 open() argument table (lines 98-111)
   - Part 1: Compress Section 2 core methods table (lines 128-140)
   - Part 1: Compress Section 2 typical usage patterns (lines 144-160)
   - Part 1: Compress Section 2 apply_connection_pragmas() call site list (line 124)
   - Preserve: db.store is public API surface, store_protocols/store_impl are internal boundaries, responsibility division when extending DB store, SQLiteHelper operational role, raw sqlite3 connection PRAGMA application special case, transaction helper purpose, VACUUM/DDL as exclusive operations

3. **Phase 3: Deployment & Verification**
   - Confirm db.store as public surface clearly stated
   - Confirm store_protocols/store_impl as internal boundaries clearly stated
   - Confirm cross-references to `scripts/db/store.py`, `scripts/db/store_protocols.py`, `scripts/db/store_impl.py`, `scripts/db/helper.py` exist
   - Validate internal Markdown links and cross-references
   - Confirm compliance with post-edit chapter structure template from `memo-doc-shared-review.md`

### Method
- Table reduction: convert full-field tables to category-level descriptions
- Code block removal: replace inline Python definitions with prose summaries of field semantics
- Pseudo-code removal: replace procedural pseudo-code with behavioral descriptions
- Prose compression: convert field-by-field enumeration to grouped descriptions by purpose

### Details
#### Part 1 (Module Boundaries):
- Section 1a (module boundaries): replace with prose: "DB store layer split into three modules with clear import boundaries. db/store.py is public API surface — re-exports protocols and embedding helpers; callers should import from here for stable contract. db/store_protocols.py is extension point — protocol definitions for storage contracts; implementers import this, callers rarely use directly. db/store_impl.py is SQLite implementation layer — concrete implementations of protocols; do not import directly except when intentionally working at protocol/implementation level. Rule: callers always import from db.store; direct imports from store_protocols.py or store_impl.py discouraged, only for intentional protocol/implementation work. Extension method: add new Protocol class to db/store_protocols.py (e.g. class NewStorageProtocol(Protocol): ...), implement protocol in db/store_impl.py (e.g. class NewStorageImpl(NewStorageProtocol): ...), export from db/store.py — callers import from db.store not internal modules. Anti-pattern: calling code importing directly from store_protocols.py or store_impl.py."
- Section 2 (constructor): replace with prose: "SQLiteHelper(target='rag', *, db_path=None, sqlite_vec_so='', sqlite_timeout=30, sqlite_busy_timeout_ms=30000). DbTarget.RAG/SESSION/WORKFLOW/EVENTBUS or string literal ('rag'→rag.sqlite, 'session'→session.sqlite, 'workflow'→workflow.sqlite, 'eventbus'→eventbus.sqlite); invalid target raises ValueError. build_db_config() called within __init__() to resolve all paths and settings; if db_path explicitly passed, build_db_config() fully bypassed and specified db_path/sqlite_vec_so/sqlite_timeout/sqlite_busy_timeout_ms used directly (allows MCP servers etc. to self-contain DB config without reading agent.toml). DB_PATH property provides read-only access to resolved DB path for instance."
- Section 2 (open()): replace with prose: "open(*, write_mode=False, row_factory=False, load_vec=None, reuse_connection=False) returns self for chaining, sets self.conn. write_mode=True adds PRAGMA foreign_keys=ON; row_factory=True sets conn.row_factory = sqlite3.Row (column-name access); load_vec=None uses target default (rag→True, session/workflow→False); load_vec=True forces sqlite-vec extension load; load_vec=False skips vec extension; reuse_connection=True skips reconnect if existing self.conn available, also skips close() in __exit__ (allows connection reuse). Always applied: vec load (if valid), WAL, NORMAL sync, busy_timeout. For reuse_connection details see 90_shared_04_01 §4b."
- Section 2 (core methods): replace with prose: "execute(sql, params=()) → sqlite3.Cursor: params tuple (positional ?) or dict (named :name); RuntimeError if conn None, ValueError if sql empty. executescript(sql_script) → None: executes multiple SQL statements, commits pending transactions before execution. executemany(sql, params_seq) → sqlite3.Cursor: batch INSERT/UPDATE, params_seq list[tuple[Any,...]]. fetchall(sql, params=()) → list[Any]: combine execute + fetchall. commit() → None: logs ERROR then re-raises sqlite3.OperationalError. close() → None: idempotent, WARNING logged on close error but no exception thrown. begin_immediate() → @contextmanager: BEGIN IMMEDIATE...COMMIT, auto ROLLBACK on Exception (not BaseException). begin_exclusive() → @contextmanager: BEGIN EXCLUSIVE...COMMIT, VACUUM/DDL only, auto ROLLBACK on Exception (not BaseException). health_check() → DbHealthMetrics: PRAGMA quick_check, returns {journal_mode, integrity, page_count, page_size, freelist_count, db_size_bytes}. checkpoint(mode='TRUNCATE') → WalCheckpointCounts: modes PASSIVE/FULL/RESTART/TRUNCATE, invalid mode raises ValueError. vacuum() → None: rebuilds DB in-place, requires ~2x DB size free disk space, call outside transaction."
- Section 2 (typical usage): replace with prose: "Read-only query: with SQLiteHelper('rag').open(row_factory=True) as db: rows = db.fetchall('SELECT url, title FROM documents WHERE lang = :lang', {'lang': 'ja'}). Write with transaction: with SQLiteHelper('session').open(write_mode=True) as db: db.execute('INSERT INTO sessions DEFAULT VALUES'); db.commit(). Atomic multi-statement write: with SQLiteHelper('rag').open(write_mode=True) as db: with db.begin_immediate(): db.execute('DELETE FROM chunks WHERE doc_id = ?', (doc_id,)); db.execute('DELETE FROM documents WHERE doc_id = ?', (doc_id,)); COMMIT auto on exit; ROLLBACK on exception."
- Section 2 (apply_connection_pragmas): replace with prose: "Module-level function exposing WAL/synchronous=NORMAL/busy_timeout/foreign_keys pragma application logic that SQLiteHelper.open() uses internally, allowing raw sqlite3.Connection to receive same pragmas without going through SQLiteHelper. Called directly by mcp_servers/mdq/db_schema.py, mcp_servers/mdq/service.py, mcp_servers/mdq/health_check.py, eventbus/db.py."
- Remove Related Documents and Keywords sections — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/db/store.py`, `scripts/db/store_protocols.py`, `scripts/db/store_impl.py`, `scripts/db/helper.py`, `scripts/db/config.py`, `scripts/db/schema_sql.py`, `scripts/mcp_servers/mdq/db_schema.py`, `scripts/mcp_servers/mdq/service.py`, `scripts/mcp_servers/mdq/health_check.py`, `scripts/eventbus/db.py` must remain valid after restructuring
- Internal Markdown links must be verified against actual file paths in `docs/90_shared_*` directories
- No change to source code contracts — document-only modification

## Security considerations
- N/A — document-only modification, no security-sensitive content affected

## Rollback considerations
- If restructuring causes link breakage, revert to original structure and apply targeted compression instead of full rewrite
- All removed details point to source files for verification

## Validation plan
| Check | Tool | Target |
|---|---|---|
| db.store-as-Public-Surface | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/db/store.py / scripts/db/store_protocols.py / scripts/db/store_impl.py / scripts/db/helper.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Source code changes
- Test modifications
- Cross-chapter structural changes beyond this file
- Auto-generation of documentation (future work)

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-211747_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-095400
- Related target files: docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
