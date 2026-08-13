## Goal
- Restructure `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` to remove overly detailed migration list names, ALTER TABLE details, duplicate column name error handling implementation details, RAG consistency function internal judgment expressions, AI reference table, overly detailed trust source lists, and numerical thresholds stated as decisions while explicitly preserving schema initialization/migration policy, rag/session/eventbus have no compatibility migrations, workflow.sqlite only has incremental migrations, mdq.sqlite has separate legacy schema detection mechanism, schema change criteria, data loss risk when DB recreation needed, single-node SQLite scaling limits, numerical thresholds expressed as estimates, and migration warning signal checklist.

## Scope
- **In-Scope**: 
  - `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/DB chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should describe migration/scaling/schema change policy
- Numerical thresholds are estimates requiring per-environment validation
- Existing internal links and cross-references must remain valid after editing

## Design decisions
### Part 1 (Migration Policy):
- Compress Section 8a workflow.sqlite incremental migration list names (line 40): replace with prose describing migration purpose
- Compress Section 8a apply_workflow_migrations() duplicate column name error swallowing detail (line 41): replace with prose describing idempotency behavior
- Compress Section 8b RAG consistency function internal judgment expression (line 49): replace with prose describing consistency check purpose
- Compress Section 8c mdq.sqlite legacy schema detection mechanism (lines 53-61): replace with prose describing auto-detection behavior
- Compress Section 9 constraints table (lines 67-76): replace with prose describing operational constraints
- Compress Section 9a AI reference table (lines 82-89): replace with prose descriptions where tabular format adds no reference value beyond what's already described in other sections
- Compress Section 10 source of truth list (lines 95-104): replace with prose describing authoritative sources
- Compress Section 11 numerical threshold values (lines 116-164): replace with prose describing scaling concerns at conceptual level
- Preserve: schema initialization/migration policy, rag/session/eventbus no compatibility migrations, workflow.sqlite only has incremental migrations, mdq.sqlite separate legacy schema detection, schema change criteria, data loss risk when DB recreation needed, single-node SQLite scaling limits, numerical thresholds as estimates, migration warning signal checklist

## Alternatives considered
- Remove Section 8 entirely: rejected — migration policy is fundamental architecture decision
- Replace all tables with prose: rejected — tabular format for constraints/source of truth is efficient for reference
- Remove Section 11 scaling limits entirely: rejected — scaling signals are operational guidance

## Implementation
### Target files
- `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which migration/scaling design judgments are scattered across sections

2. **Phase 2: Core Logic Implementation**
   - Part 1: Compress or remove Section 8a workflow.sqlite incremental migration list names (line 40)
   - Part 1: Compress or remove Section 8a apply_workflow_migrations() duplicate column name error swallowing detail (line 41)
   - Part 1: Compress or remove Section 8b RAG consistency function internal judgment expression (line 49)
   - Part 1: Compress or remove Section 8c mdq.sqlite legacy schema detection mechanism (lines 53-61)
   - Part 1: Compress or remove Section 9 constraints table (lines 67-76)
   - Part 1: Compress or remove Section 9a AI reference table (lines 82-89)
   - Part 1: Compress or remove Section 10 source of truth list (lines 95-104)
   - Part 1: Compress or remove Section 11 numerical threshold values (lines 116-164)
   - Preserve: schema initialization/migration policy, rag/session/eventbus no compatibility migrations, workflow.sqlite only has incremental migrations, mdq.sqlite separate legacy schema detection, schema change criteria, data loss risk when DB recreation needed, single-node SQLite scaling limits, numerical thresholds as estimates, migration warning signal checklist

3. **Phase 3: Deployment & Verification**
   - Confirm migration vs recreation criteria not weakened
   - Confirm data-loss warnings clearly stated
   - Confirm numerical thresholds explicitly expressed as estimates
   - Confirm cross-references to `scripts/db/rag_consistency.py` and related modules exist
   - Validate internal Markdown links and cross-references
   - Confirm compliance with post-edit chapter structure template from `memo-doc-shared-review.md`

### Method
- Table reduction: convert full-field tables to category-level descriptions
- Code block removal: replace inline Python definitions with prose summaries of field semantics
- Pseudo-code removal: replace procedural pseudo-code with behavioral descriptions
- Prose compression: convert field-by-field enumeration to grouped descriptions by purpose

### Details
#### Part 1 (Migration Policy):
- Section 8a (workflow.sqlite migrations): replace with prose: "workflow.sqlite has dedicated incremental migration mechanism via db/schema_sql.py. _WORKFLOW_MIGRATIONS is list of (migration_id, ALTER TABLE ... ADD COLUMN SQL) pairs adding columns like error_kind/error_detail to attempts, workflow_id/attempt_number to artifacts etc. apply_workflow_migrations(conn) applies list sequentially; sqlite3.OperationalError containing 'duplicate column name' swallowed (already applied, logged); other errors re-raised. create_workflow_schema() calls apply_workflow_migrations() after base table creation then records WORKFLOW_SCHEMA_VERSION (currently '1.0.0') in workflow_schema_version table. On newly created DBs these migrations are effectively no-op (swallowed as duplicate column name since _WORKFLOW_SCHEMA already includes those columns); they function for existing old DBs to add incremental columns."
- Section 8b (RAG consistency): replace with prose: "db/rag_consistency.py::check_rag_consistency() compares row counts between chunks/chunks_fts (via chunks_fts_docsize internal table) /chunks_vec, returns RagConsistencyReport (db/models.py). is_consistent() considers consistent when fts_gap == 0 and fts_orphan_count == 0 and orphan_vec_count == 0 and vec == chunks. summarize_issues() generates [WARNING]/[CRITICAL] prefixed messages with recovery commands (/session rag-rebuild-fts, ingester.py --force) for each detected inconsistency."
- Section 8c (mdq.sqlite): replace with prose: "scripts/mcp_servers/mdq/db_schema.py::create_production_tables() (lines 21-44) is third schema update pattern different from rag/session/eventbus and workflow, auto-executed on every MDQ service startup (no explicit migration command needed). Trigger: called every MDQ service startup. Detection: PRAGMA table_info(chunks) checks first column of chunks table, determines if old schema (id INTEGER PRIMARY KEY + chunk_id TEXT UNIQUE). Action: when old schema detected, unconditionally DROP chunks/chunks_fts tables and associated triggers, then CREATE TABLE IF NOT EXISTS recreates with current schema (chunk_id TEXT PRIMARY KEY). Contrast: unlike 8a workflow.sqlite version-managed columns and explicit ALTER TABLE migration list — inspects schema shape on every startup, silently rebuilds if outdated. Data loss note: DROP on old schema detection is unconditional, existing chunks/chunks_fts data lost after recreation. rag.sqlite/session.sqlite/eventbus.sqlite chunks_vec/memories_vec (db/schema_sql.py) unrelated to MDQ schema/hybrid search cleanup work, unaffected."
- Section 9 (constraints): replace with prose: "SQLite version 3.35+ required; sqlite-vec path /opt/llm/sqlite-vec/vec0.so (from agent.toml::sqlite_vec_so); WAL mode on all connections (PRAGMA journal_mode=WAL); busy_timeout 30,000 ms default (agent.toml::sqlite_busy_timeout_ms); embedding dimension 384 default (agent.toml::embedding_dims); float format float32 little-endian BLOB; single-node only (no distributed/replica support); agent.toml loading included in ConfigLoader().load_all() at index 0 — see 90_shared_03 §2a Config Ownership for ownership table."
- Section 9a (AI reference): replace with prose: "rag.sqlite schema location: this doc §5; session.sqlite schema location: this doc §6; SQLiteHelper supports workflow.sqlite: yes (target='workflow', not documented in spec, see §4); embedding dimension set via agent.toml::embedding_dims (default 384); schema initializer: create_schema() — idempotent DDL-only initialization, not migration; DB triggers documented: chunks_fts auto-sync triggers (§5), memories_fts auto-sync triggers (§6)."
- Section 10 (source of truth): replace with prose: "DDL source: db/schema_sql.py; schema initialization entry point: db/create_schema.py::create_schema(); deploy initialization entry point: deploy/init_db.sh; DB connection helper: db/helper.py::SQLiteHelper; DB files: rag.sqlite, session.sqlite, workflow.sqlite, eventbus.sqlite; Event Bus schema (DDL only): scripts/eventbus/schema.sql; mdq.sqlite schema/auto-update source: scripts/mcp_servers/mdq/db_schema.py::create_production_tables() (see §8c); deleted entry point: db/workflow_schema.py — removed in plan 54."
- Section 11 (scaling limits): replace with prose: "Current RAG architecture uses single-node SQLite, suitable for team-scale deployments with moderate corpus size and infrequent concurrent writes. Scaling signals: corpus size — chunks table exceeding ~500k rows causes KNN scan time in chunks_vec to increase linearly with corpus size; at this scale begin monitoring /rag search latency; DB file size exceeding ~10GB increases VACUUM time, backup duration, WAL checkpoint latency, /db vacuum may take minutes instead of seconds; write concurrency — multiple RagIngester processes writing to same rag.sqlite serialized at WAL layer, ingestion throughput becomes bottleneck when SQLite write serialization is constraint factor; signal: WAL file grows faster than checkpoint can shrink it, monitor via /db health; FTS5 search latency — signal: /rag search consistently exceeds 500ms, FTS5 BM25 scales with document count so search speed may degrade on very large corpora; operational complexity — backup and point-in-time recovery become complex with file size growth, sharing same DB file across multiple environments unsupported (SQLite is single-file), repair of /session rag-consistency issues becomes harder as scale grows. Migration checklist — consider architecture review when 2+ of: p95 KNN search latency exceeds 1 second, DB file size exceeds 20GB, WAL checkpoints consistently exceed 30 seconds, ingestion queue depth consistently exceeds 10k unprocessed chunk files, multiple teams or processes require concurrent write access. Evaluate: vector search — dedicated vector database (approximate nearest neighbor, distributed index) outperforms sqlite-vec at scale exceeding 1M vectors; full-text search — inverted index search services handle larger corpora with lower latency; hybrid store — relational DB + vector extension (e.g. pgvector compatible) enables write concurrency scaling while maintaining SQL semantics. NOTE: All above numerical thresholds are planned estimates not guaranteed by benchmarks. Actual limits depend on hardware, embedding dimensions, query patterns, corpus characteristics. Verify each threshold in individual deployment environment before treating as deterministic."
- Remove Related Documents and Keywords sections — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/db/rag_consistency.py`, `scripts/db/create_schema.py`, `scripts/db/schema_sql.py`, `scripts/db/helper.py`, `scripts/db/config.py`, `scripts/db/store_protocols.py`, `scripts/db/store_impl.py`, `scripts/db/store.py`, `scripts/db/maintenance.py`, `scripts/mcp_servers/mdq/db_schema.py`, `scripts/eventbus/schema.sql`, `deploy/init_db.sh`, `deploy/setup_services.sh`, `scripts/agent/factory.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/repl_health.py` must remain valid after restructuring
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
| Migration vs Recreation Criteria | Manual | Explicitly preserved |
| Data-Loss Warnings | Manual | Explicitly preserved |
| Thresholds as Estimates | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/db/rag_consistency.py / related modules |
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
- Source plan: plans/20260807-211633_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-095200
- Related target files: docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md
