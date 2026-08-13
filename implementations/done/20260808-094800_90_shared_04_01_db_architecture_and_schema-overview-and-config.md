## Goal
- Restructure `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md` to remove overly detailed directory structures, field definitions, constructor details, argument explanations, mechanical PRAGMA enumerations, and begin_immediate/begin_exclusive implementation details while explicitly preserving why DB files are split, SQLiteHelper's role, sqlite-vec used only for RAG, operational meaning of WAL/busy_timeout/foreign_keys, and db_path override necessity.

## Scope
- **In-Scope**: 
  - `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/DB chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should be authoritative reference for DB architecture decisions
- Existing internal links and cross-references must remain valid after editing

## Design decisions
### Part 1 (DB Architecture Overview):
- Compress Section 2 db/ directory structure (lines 33-42): replace with prose describing module responsibilities at conceptual level
- Compress Section 2 DB file table (lines 46-51): replace with prose describing DB separation rationale and per-process isolation policy
- Compress Section 3 DbConfig full dataclass definition (lines 64-74): replace with prose describing configuration categories (paths, timeouts, dimensions, extension)
- Compress Section 4 SQLiteHelper constructor details (lines 87-94): replace with prose describing target resolution logic
- Compress Section 4 open() connection setup steps (lines 100-107): replace with prose describing connection lifecycle at conceptual level
- Compress Section 4a SQLiteHelper db_path override (line 109-111): replace with prose describing override purpose
- Compress Section 4b open() additional options (lines 113-119): replace with prose describing optional parameters
- Compress Section 4c transaction helpers (lines 121-122): replace with prose describing transaction semantics
- Preserve: DB file split rationale, sqlite-vec used only for RAG, WAL/busy_timeout/foreign_keys operational meaning, db_path override necessity, Event Bus out of scope note

## Alternatives considered
- Remove Section 2 entirely: rejected — DB layer structure is fundamental architecture decision
- Replace all tables with prose: rejected — tabular format for DB file mapping is efficient for reference
- Merge Sections 3 and 4 into one: rejected — different conceptual domains (config vs runtime)

## Implementation
### Target files
- `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which DB architecture design judgments are scattered across sections

2. **Phase 2: Core Logic Implementation**
   - Part 1: Compress or remove Section 2 db/ directory structure (lines 33-42)
   - Part 1: Compress or remove Section 2 DB file table (lines 46-51)
   - Part 1: Compress or remove Section 3 DbConfig full dataclass definition (lines 64-74)
   - Part 1: Compress or remove Section 4 SQLiteHelper constructor details (lines 87-94)
   - Part 1: Compress or remove Section 4 open() connection setup steps (lines 100-107)
   - Part 1: Compress or remove Section 4a SQLiteHelper db_path override (lines 109-111)
   - Part 1: Compress or remove Section 4b open() additional options (lines 113-119)
   - Part 1: Compress or remove Section 4c transaction helpers (lines 121-122)
   - Preserve: DB file split rationale, sqlite-vec used only for RAG, WAL/busy_timeout/foreign_keys operational meaning, db_path override necessity, Event Bus out of scope note

3. **Phase 3: Deployment & Verification**
   - Confirm DB file split rationale not weakened
   - Confirm sqlite-vec = RAG only constraint clearly stated
   - Confirm cross-references to `scripts/db/config.py`, `scripts/db/helper.py` exist
   - Validate internal Markdown links and cross-references
   - Confirm compliance with post-edit chapter structure template from `memo-doc-shared-review.md`

### Method
- Table reduction: convert full-field tables to category-level descriptions
- Code block removal: replace inline Python definitions with prose summaries of field semantics
- Pseudo-code removal: replace procedural pseudo-code with behavioral descriptions
- Prose compression: convert field-by-field enumeration to grouped descriptions by purpose

### Details
#### Part 1 (DB Architecture Overview):
- Section 2 (db/ directory): replace directory tree with prose: "db/ contains helper.py (connection lifecycle, PRAGMA, vec extension), create_schema.py (DDL creation idempotent for rag/session/workflow/eventbus schemas), store_protocols.py (MemoryDeleteStore, VectorStore protocol definitions), store_impl.py (SQLite implementations of store protocols), store.py (re-export stub public API surface for db.store imports), maintenance.py (WAL checkpoint, VACUUM, purge, rotate, recover)."
- Section 2 (DB files): replace table with prose: "Four DB files exist: rag.sqlite (agent.toml::rag_db_path, documents/chunks/chunks_fts/chunks_vec tables), session.sqlite (agent.toml::session_db_path, sessions/messages/memories/memories_fts/memories_vec/memory_links/session_diagnostics tables), workflow.sqlite (agent.toml::workflow_db_path, tasks/attempts/processed_events/artifacts/approvals tables), eventbus.sqlite (agent.toml::eventbus_db_path, events table). DB files separated because RAG indexing and conversation state have different access patterns; rag.sqlite writes heavily during ingestion and reads during query; session.sqlite appends heavily during conversations; separation avoids WAL contention."
- Section 3 (DbConfig): replace dataclass listing with prose: "Frozen dataclass for DB configuration. rag_db_path (path to rag.sqlite), session_db_path (path to session.sqlite), workflow_db_path (default /opt/llm/db/workflow.sqlite), eventbus_db_path (default /opt/llm/db/eventbus.sqlite), sqlite_vec_so (path to vec0.so, empty = vec extension not needed), sqlite_timeout (sqlite3.connect() timeout seconds >= 1), sqlite_busy_timeout_ms (PRAGMA busy_timeout ms default 30000), embedding_dims (embedding vector dimension default 384). __post_init__ validates all path fields non-empty, sqlite_timeout >= 1, embedding_dims >= 1, parent directories exist (DB files themselves created on first open). No embed_url field exists. Built by build_db_config() in db/config.py. agent.toml loaded via ConfigLoader().load_all() (_BASE_CONFIG_FILES index 0 included)."
- Section 4 (SQLiteHelper constructor): replace with prose: "SQLiteHelper manages connection lifecycle. Constructor accepts target parameter resolving to specific DB file: DbTarget.RAG → rag.sqlite, DbTarget.SESSION → session.sqlite, DbTarget.WORKFLOW → workflow.sqlite, DbTarget.EVENTBUS → eventbus.sqlite (Event Bus DDL only; no runtime integration yet). DbTarget is StrEnum defined in db/helper.py (RAG/SESSION/WORKFLOW/EVENTBUS); target parameter accepts enum member or same-named string literal."
- Section 4 (open() connection setup): replace numbered list with prose: "Connection setup per open() call: load sqlite-vec extension (rag target only), then enable_load_extension(False); set PRAGMA journal_mode=WAL; set PRAGMA synchronous=NORMAL; set PRAGMA busy_timeout=30000 (from agent.toml::sqlite_busy_timeout_ms); set PRAGMA foreign_keys=ON (when write_mode=True). sqlite-vec loaded only when target='rag'; session and workflow targets do not load vec."
- Section 4a (db_path override): replace with prose: "SQLiteHelper.__init__() accepts db_path keyword argument. When specified, completely bypasses build_db_config() (= agent.toml reading) and uses passed db_path/sqlite_vec_so/sqlite_timeout/sqlite_busy_timeout_ms directly (db/helper.py SQLiteHelper.__init__). This route serves callers like MCP servers that want self-contained DB path specification without agent.toml dependency. When db_path not specified, resolves path from build_db_config() result based on target as before."
- Section 4b (open() additional options): replace with prose: "open() accepts additional options beyond write_mode/row_factory: load_vec bool|None=None follows target defaults (True only for rag); explicit True/False overrides default; reuse_connection bool=False skips reconnection when True and existing self.conn present (also skips close() in __exit__, allows connection reuse)."
- Section 4c (transaction helpers): replace with prose: "SQLiteHelper provides context managers begin_immediate()/begin_exclusive() wrapping BEGIN IMMEDIATE/BEGIN EXCLUSIVE. Both attempt ROLLBACK on normal exception (suppress sqlite3.OperationalError), then re-raise original exception. Do not catch BaseException (KeyboardInterrupt/SystemExit). begin_exclusive() reserved for operations requiring exclusive lock (VACUUM, schema change) per db/helper.py docstring."
- Remove Related Documents and Keywords sections — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/db/config.py`, `scripts/db/helper.py`, `scripts/db/create_schema.py`, `scripts/db/store_protocols.py`, `scripts/db/store_impl.py`, `scripts/db/store.py`, `scripts/db/maintenance.py` must remain valid after restructuring
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
| DB File Split Rationale | Manual | Explicitly preserved |
| sqlite-vec = RAG Only Constraint | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/db/config.py / scripts/db/helper.py |
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
- Source plan: plans/20260807-211418_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-094800
- Related target files: docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md
