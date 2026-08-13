## Goal
- Restructure `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md` and `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md` to remove overly detailed DDL text, column lists, FTS5 virtual table definitions, vec virtual table definitions, SQL equivalent trigger explanations, workflow table column lists, and schema version table column lists while explicitly preserving that db/schema_sql.py is the schema authority, meaning of rag/session/workflow DB, why session_diagnostics separated from messages, workflow_schema_version-based version management, FATAL policy on mismatch, and manual FTS sync prohibition.

## Scope
- **In-Scope**: 
  - `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
  - `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/DB chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and these chapters should describe "which DB is authoritative" and "what to watch for on change"
- FATAL policy on schema mismatch and manual FTS sync prohibition must not be weakened from correctness standpoint
- Existing internal links and cross-references must remain valid after editing

## Design decisions
### Part 1 (RAG Schema):
- Compress Section 5 documents table full column list (lines 28-37): replace with prose describing document metadata categories (identifier, URL tracking, language, fetch metadata, chunking strategy)
- Compress Section 5 chunks table full column list (lines 43-51): replace with prose describing chunk metadata categories (identifier, parent reference, content storage, type/source classification)
- Compress Section 5 chunks_fts FTS5 definition (lines 55-62): replace with prose describing FTS indexing purpose
- Compress Section 5 chunks_fts trigger table (lines 66-71): replace with prose describing automatic synchronization behavior
- Compress Section 5 chunks_vec vec0 definition (lines 77-83): replace with prose describing vector storage purpose
- Preserve: ISO-8601 UTC Z-suffix timestamp format policy, manual FTS sync prohibition, sqlite-vec used only for RAG, db/schema_sql.py as schema authority

### Part 2 (Session + Workflow Schemas):
- Compress Section 6 sessions table full column list (lines 28-32): replace with prose describing session metadata
- Compress Section 6 messages table full column list (lines 36-44): replace with prose describing message metadata categories (identifier, session reference, role/content, tool association, timestamp)
- Compress Section 6 memories table full column list (lines 48-64): replace with prose describing memory metadata categories (identifier, type, source context, content, importance/pinning, timestamps)
- Compress Section 6 memories_fts FTS5 definition (lines 68-75): replace with prose describing FTS search columns
- Compress Section 6 memories_vec vec0 definition (line 82): replace with prose describing vector retrieval purpose
- Compress Section 6 memory_links table (lines 88-95): replace with prose describing link structure
- Compress Section 6 session_diagnostics table (lines 99-109): replace with prose describing diagnostic metadata
- Compress Section 7 tasks table full column list (lines 119-129): replace with prose describing task metadata categories
- Compress Section 7 approvals table full column list (lines 133-142): replace with prose describing approval metadata categories
- Compress Section 7 workflow_schema_version table (lines 148-161): replace with prose describing version management approach
- Compress Section 7a timestamp format policy (lines 167-175): replace with prose describing timestamp convention
- Preserve: session_diagnostics separated from messages rationale, workflow_schema_version-based version management, FATAL policy on mismatch, manual FTS sync prohibition, ISO-8601 UTC Z-suffix timestamp policy

## Alternatives considered
- Remove Section 5 entirely: rejected — RAG schema is fundamental data model decision
- Replace all tables with prose: rejected — tabular format for schema reference is efficient for lookup
- Merge Sections 6 and 7 into one: rejected — different conceptual domains (conversation state vs workflow execution)

## Implementation
### Target files
- `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md`
- `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which schema design judgments are scattered across sections

2. **Phase 2: Core Logic Implementation**
   - Part 1: Compress or remove Section 5 documents table full column list (lines 28-37)
   - Part 1: Compress or remove Section 5 chunks table full column list (lines 43-51)
   - Part 1: Compress or remove Section 5 chunks_fts FTS5 definition (lines 55-62)
   - Part 1: Compress or remove Section 5 chunks_fts trigger table (lines 66-71)
   - Part 1: Compress or remove Section 5 chunks_vec vec0 definition (lines 77-83)
   - Part 2: Compress or remove Section 6 sessions table full column list (lines 28-32)
   - Part 2: Compress or remove Section 6 messages table full column list (lines 36-44)
   - Part 2: Compress or remove Section 6 memories table full column list (lines 48-64)
   - Part 2: Compress or remove Section 6 memories_fts FTS5 definition (lines 68-75)
   - Part 2: Compress or remove Section 6 memories_vec vec0 definition (line 82)
   - Part 2: Compress or remove Section 6 memory_links table (lines 88-95)
   - Part 2: Compress or remove Section 6 session_diagnostics table (lines 99-109)
   - Part 2: Compress or remove Section 7 tasks table full column list (lines 119-129)
   - Part 2: Compress or remove Section 7 approvals table full column list (lines 133-142)
   - Part 2: Compress or remove Section 7 workflow_schema_version table (lines 148-161)
   - Part 2: Compress or remove Section 7a timestamp format policy (lines 167-175)
   - Preserve: session_diagnostics separated from messages rationale, workflow_schema_version-based version management, FATAL policy on mismatch, manual FTS sync prohibition, ISO-8601 UTC Z-suffix timestamp policy

3. **Phase 3: Deployment & Verification**
   - Confirm FATAL policy on schema mismatch not weakened
   - Confirm manual FTS sync prohibition clearly stated
   - Confirm cross-references to `scripts/db/schema_sql.py` exist
   - Validate internal Markdown links and cross-references
   - Confirm compliance with post-edit chapter structure template from `memo-doc-shared-review.md`

### Method
- Table reduction: convert full-field tables to category-level descriptions
- Code block removal: replace inline SQL definitions with prose summaries of field semantics
- Pseudo-code removal: replace procedural pseudo-code with behavioral descriptions
- Prose compression: convert field-by-field enumeration to grouped descriptions by purpose

### Details
#### Part 1 (RAG Schema):
- Section 5 (documents): replace column list with prose: "Document metadata: doc_id (INTEGER PK AUTOINCREMENT), url (TEXT UNIQUE NOT NULL), title (TEXT nullable), lang (TEXT NOT NULL CHECK ja/en), fetched_at (TEXT NOT NULL DEFAULT strftime('%Y-%m-%dT%H:%M:%SZ', 'now') — ISO-8601 UTC Z-suffix), etag (TEXT nullable), last_modified (TEXT nullable), chunking_strategy (TEXT NOT NULL DEFAULT 'text'). Timestamp format corrected in db/schema_sql.py _RAG_SCHEMA_TEMPLATE to use strftime('%Y-%m-%dT%H:%M:%SZ', 'now') instead of datetime('now'); all other tables' timestamp columns (created_at/updated_at etc) unified under same format."
- Section 5 (chunks): replace column list with prose: "Chunk metadata: chunk_id (INTEGER PK AUTOINCREMENT), doc_id (INTEGER NOT NULL FK → documents(doc_id) ON DELETE CASCADE), chunk_index (INTEGER NOT NULL), content (TEXT NOT NULL), normalized_content (TEXT nullable for English/code), chunk_type (TEXT NOT NULL DEFAULT 'text'), source_file (TEXT NOT NULL DEFAULT '')."
- Section 5 (chunks_fts): replace FTS5 definition with prose: "FTS5 virtual table for full-text search on chunk content. Uses COALESCE(new.normalized_content, new.content) for insertion/update triggers. Automatic synchronization via AFTER INSERT/AFTER UPDATE/AFTER DELETE triggers on chunks table. IMPORTANT: Do not manually synchronize chunks_fts after INSERT/UPDATE/DELETE — triggers handle it automatically."
- Section 5 (chunks_fts triggers): replace trigger table with prose: "Triggers maintain chunks_fts consistency: chunks_ai (AFTER INSERT ON chunks inserts row using COALESCE(normalized_content, content)), chunks_au (AFTER UPDATE ON chunks deletes old row then inserts new), chunks_ad (AFTER DELETE ON chunks deletes row using COALESCE(old.normalized_content, old.content)), chunks_vec_ad (AFTER DELETE ON chunks removes corresponding chunks_vec entry)."
- Section 5 (chunks_vec): replace vec0 definition with prose: "sqlite-vec virtual table for vector similarity search. Stores float32 little-endian BLOB. chunk_id INTEGER PRIMARY KEY, embedding FLOAT[DIMS] where DIMS replaced at runtime from embedding_dims config (default 384)."

#### Part 2 (Session + Workflow Schemas):
- Section 6 (sessions): replace column list with prose: "Session metadata: session_id (INTEGER PK AUTOINCREMENT), created_at (TEXT NOT NULL DEFAULT strftime('%Y-%m-%dT%H:%M:%SZ', 'now')), title (TEXT nullable)."
- Section 6 (messages): replace column list with prose: "Message metadata: message_id (INTEGER PK AUTOINCREMENT), session_id (INTEGER FK → sessions(session_id) ON DELETE CASCADE), role (TEXT NOT NULL), content (TEXT NOT NULL), tool_calls (TEXT JSON string nullable), tool_call_id (TEXT nullable — tool call association ID for tool-role messages, persisted/restored by SessionMessageRepository, NULL for non-tool messages), created_at (TEXT NOT NULL DEFAULT strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))."
- Section 6 (memories): replace column list with prose: "Memory metadata: memory_id (TEXT PK UUID v4), memory_type (TEXT CHECK semantic/episodic), source_type (TEXT NOT NULL DEFAULT 'conversation'), session_id (INTEGER nullable), turn_id (TEXT nullable), project (TEXT NOT NULL DEFAULT ''), repo (TEXT NOT NULL DEFAULT ''), branch (TEXT NOT NULL DEFAULT ''), content (TEXT NOT NULL), summary (TEXT NOT NULL DEFAULT ''), tags (TEXT NOT NULL DEFAULT '[]' JSON array), importance (REAL NOT NULL DEFAULT 0.5), pinned (INTEGER NOT NULL DEFAULT 0), created_at (TEXT NOT NULL ISO-8601), updated_at (TEXT NOT NULL ISO-8601)."
- Section 6 (memories_fts): replace FTS5 definition with prose: "FTS5 virtual table for BM25 full-text search via FtsRetriever.search() on content, summary, tags columns. memory_id UNINDEXED excluded from FTS index (used for filtering not searching)."
- Section 6 (memories_vec): replace with prose: "sqlite-vec virtual table for KNN search via VectorRetriever.knn_search(). memory_id TEXT PRIMARY KEY, embedding FLOAT[384]. Written only when embed_enabled=True and embedding generation succeeds."
- Section 6 (memory_links): replace with prose: "Many-to-many memory relationship table. src_id TEXT NOT NULL part of PK, dst_id TEXT NOT NULL part of PK, no foreign keys (uses INSERT OR IGNORE for idempotency). Records near-duplicate memory pairs for deduplication."
- Section 6 (session_diagnostics): replace with prose: "Diagnostic event logging separate from messages table. id INTEGER PK AUTOINCREMENT, session_id INTEGER FK → sessions(session_id) ON DELETE CASCADE, kind TEXT NOT NULL, content TEXT NOT NULL, workflow_id TEXT nullable, task_id TEXT nullable, created_at TEXT NOT NULL DEFAULT strftime('%Y-%m-%dT%H:%M:%SZ', 'now'). Index: idx_session_diagnostics_session ON session_diagnostics(session_id). Separated from messages because diagnostic events have different lifecycle and query patterns than conversation messages."
- Section 7 (tasks): replace column list with prose: "Workflow task metadata: task_id (TEXT PK UUID4), session_id (TEXT), workflow_id (TEXT UUID4 for this workflow run), turn_number (INTEGER), workflow_version (TEXT NOT NULL), status (TEXT pending/running/pending_approval/completed/failed/halted), idempotency_key (TEXT UNIQUE session_id:turn_number), created_at (TEXT ISO-8601 UTC), updated_at (TEXT ISO-8601 UTC)."
- Section 7 (approvals): replace column list with prose: "Approval metadata: approval_id (TEXT PK UUID4), task_id (TEXT NOT NULL FK → tasks(task_id) ON DELETE CASCADE), stage_id (TEXT nullable), status (TEXT pending/approved/rejected), reason (TEXT nullable), created_at (TEXT ISO-8601 UTC), resolved_at (TEXT nullable), workflow_id (TEXT NOT NULL DEFAULT '')."
- Section 7 (workflow_schema_version): replace with prose: "Append-only log — one row per version ever applied. version TEXT NOT NULL e.g. 1.0.0, applied_at TEXT NOT NULL ISO-8601 UTC DEFAULT strftime('%Y-%m-%dT%H:%M:%SZ', 'now'). Current version is row with maximum applied_at. create_workflow_schema() inserts new row only when latest recorded version differs from WORKFLOW_SCHEMA_VERSION constant (in scripts/db/schema_sql.py), keeping repeated runs idempotent. Schema version mismatch: both agent/repl_health.py::check_workflow_schema() (agent startup) and deploy/setup_services.sh pre-flight block compare latest workflow_schema_version.version against WORKFLOW_SCHEMA_VERSION constant, fail with [FATAL]/RuntimeError naming both expected and found versions if they differ (including when no row exists yet — e.g. workflow.sqlite created before this table existed). Recovery: re-run deploy/init_db.sh (or call create_workflow_schema() directly) to bring schema up to expected version; _WORKFLOW_MIGRATIONS and version-recording insert are both idempotent so re-running always safe."
- Section 7a (timestamp format): replace with prose: "All SQLite schema DEFAULT timestamps use strftime('%Y-%m-%dT%H:%M:%SZ', 'now') for consistency. Tables using this format: session_diagnostics.created_at (Z suffix), documents.fetched_at, sessions.created_at, messages.created_at, memories.created_at, memories.updated_at (Z suffix), Event Bus events.published_at (Z suffix). Python-side timestamp generation (for workflow tables without DEFAULT): datetime.now(UTC).isoformat() produces ISO-8601 with +00:00 suffix (e.g. 2024-01-01T00:00:00+00:00)."
- Remove Related Documents and Keywords sections from both parts — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/db/schema_sql.py`, `scripts/db/create_schema.py`, `scripts/db/store_protocols.py`, `scripts/db/store_impl.py`, `scripts/db/store.py`, `scripts/db/maintenance.py`, `scripts/db/helper.py`, `scripts/db/config.py`, `scripts/agent/factory.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/repl_health.py`, `deploy/setup_services.sh`, `deploy/init_db.sh` must remain valid after restructuring
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
| FATAL-on-Mismatch Policy | Manual | Explicitly preserved |
| Manual FTS Sync Prohibition | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/db/schema_sql.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Source code changes
- Test modifications
- Cross-chapter structural changes beyond these two files
- Auto-generation of documentation (future work)

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-211521_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-095000
- Related target files: docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md, docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md
