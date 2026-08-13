## Goal

Rebuild the shared/DB schema reference chapter by compressing or removing implementation details such as full DDL text and column lists while explicitly preserving: db/schema_sql.py is schema source of truth, meaning of rag.sqlite/session.sqlite/workflow DBs, why session_diagnostics is separated from messages, workflow_schema_version-based version management, FATAL-on-mismatch policy, operational caution around RAG FTS auto-sync trigger, chunks_fts must not be manually synced.

## Scope

**In-Scope**: `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md` structure change only.

**Out-of-Scope**: Other shared/db related chapters (`docs/90_shared_*.md`), source code changes, tests.

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be maintained as the authoritative reference for DB source of truth and schema policies.
- This chapter focuses on design intent, not implementation details.
- Existing internal links and cross-references must remain valid after editing.

## Design decisions

- Compress full DDL text into high-level schema category references.
- Replace exhaustive column lists with "schema categories exist" statements.
- Retain explicit FATAL-on-mismatch policy and manual sync prohibition.

## Alternatives considered

- Full removal of all schema details: rejected because DB meaning boundaries become unclear without any concrete anchors.
- Keeping full DDL and column lists: rejected because they drift from reality as schemas evolve and add noise to the overview.

## Implementation

### Target file

`docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md`

### Procedure

1. Read current chapter content.
2. Identify complete session.sqlite table definitions and replace with high-level category references (e.g., "sessions table stores session metadata", "messages table stores conversation history").
3. Compress/remove complete column lists for each table — retain only primary keys, foreign key relationships, and critical constraints.
4. Compress/remove FTS5 virtual table definition — replace with "FTS5 virtual table for memories search".
5. Compress/remove sqlite-vec virtual table definition — replace with "sqlite-vec vector index for KNN retrieval".
6. Compress/remove workflow.sqlite complete table definitions — replace with high-level category references.
7. Compress/remove workflow_schema_version complete column list — retain only "append-only log, one row per version".
8. Compress/remove timestamp format policy detailed table — replace with "ISO-8601 timestamps used consistently; Z-suffix for SQLite defaults, +00:00 suffix for Python-generated timestamps".
9. Verify preservation of: db/schema_sql.py is schema source of truth, meaning of rag.sqlite/session.sqlite/workflow DBs, why session_diagnostics is separated from messages, workflow_schema_version-based version management, FATAL-on-mismatch policy, operational caution around RAG FTS auto-sync trigger, chunks_fts must not be manually synced.
10. Validate all internal Markdown links and cross-references.
11. Confirm compliance with `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.

### Method

Document compression via selective deletion of exhaustive DDL text and column lists while retaining structural schema ownership declarations that point to source modules.

### Details

- **Preserve**: db/schema_sql.py is schema source of truth (explicitly stated), meaning of rag.sqlite/session.sqlite/workflow DBs (separate files for separate concerns — rag for document storage, session for conversation state, workflow for task orchestration), why session_diagnostics is separated from messages (diagnostics track system-level events like tool invocations separately from user-facing conversation history), workflow_schema_version-based version management (append-only log, one row per version; current version = max(applied_at); create_workflow_schema() inserts only when latest recorded version differs from WORKFLOW_SCHEMA_VERSION constant), FATAL-on-mismatch policy (both agent/startup check_workflow_schema() and deploy/pre-flight compare latest workflow_schema_version.version against WORKFLOW_SCHEMA_VERSION constant; mismatch fails with [FATAL]/RuntimeError naming both versions; also applies when no row exists yet — e.g., workflow.sqlite created before this table existed), operational caution around RAG FTS auto-sync trigger (auto-sync triggers maintain consistency but require monitoring), chunks_fts must not be manually synced (prohibition statement preserved).
- **Compress/remove**: session.sqlite complete table definitions → replace with "tables: sessions, messages, memories, memories_fts, memories_vec, memory_links, session_diagnostics"; complete column lists → retain only PK/FK/critical constraint annotations; FTS5 virtual table definition → replace with "FTS5 virtual table for BM25 search on content/summary/tags"; sqlite-vec virtual table definition → replace with "sqlite-vec vector index for KNN retrieval on embedding[384]"; workflow.sqlite complete table definitions → replace with "tables: tasks, approvals, attempts, processed_events, artifacts, workflow_schema_version"; workflow_schema_version complete column list → replace with "columns: version(TEXT), applied_at(TEXT); append-only log"; timestamp format policy detailed table → replace with "SQLite DEFAULT uses strftime('%Y-%m-%dT%H:%M:%SZ', 'now'); Python datetime.now(UTC).isoformat() produces +00:00 suffix".
- **Verify**: cross-reference to scripts/db/schema_sql.py exists; FATAL-on-mismatch policy clear; manual FTS sync prohibition clear; internal Markdown links valid; template compliance.

## Compatibility considerations

N/A — document-only phase.

## Security considerations

N/A — document-only phase.

## Rollback considerations

N/A — document-only phase.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Db Schema Sql Py Is Schema Source Of Truth | Manual | Explicitly preserved |
| Meaning Of Rag Session Workflow Dbs | Manual | Explicitly preserved |
| Why Session Diagnostics Is Separated From Messages | Manual | Explicitly preserved |
| Workflow Schema Version Based Version Management | Manual | Explicitly preserved |
| Fatal On Mismatch Policy | Manual | Explicitly preserved |
| Operational Caution Around Rag Fts Auto Sync Trigger | Manual | Explicitly preserved |
| Chunks Fts Must Not Be Manually Synced | Manual | Explicitly preserved |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |

## Out of scope

Other shared/db related chapters, source code changes, tests.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-233938_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-131643
- Related target files: 90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md
