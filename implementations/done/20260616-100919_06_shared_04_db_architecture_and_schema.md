# Implementation: docs/06_shared_04_db_architecture_and_schema.md

## Goal

Create the DB architecture and schema reference covering SQLiteHelper constructor targets,
DbConfig, WAL configuration, and all table schemas for rag.sqlite, session.sqlite,
and workflow.sqlite.

## Scope

- Content from: `07_spec_db.md` §1-9 (purpose, scope, background, prerequisites, constraints,
  features, I/O, flows, data specs)
- Content from: `07_ref-sqlite.md` constructor/target table (includes "workflow" target)
- Output: `docs/06_shared_04_db_architecture_and_schema.md`
- Not covered: SQLiteHelper API methods (→ 05), maintenance functions (→ 05)

## Assumptions

- Three DB targets: rag / session / workflow (workflow only documented in 07_ref-sqlite.md)
- WAL mode and busy_timeout applied to all connections
- sqlite-vec loaded only for target="rag"
- common.toml non-integration is a known issue (see 90)

## Implementation

### Target file

`docs/06_shared_04_db_architecture_and_schema.md`

### Procedure

1. Architecture overview: 3 DB files, separation rationale, WAL + busy_timeout
2. SQLiteHelper target table:
   | target | DB file | config key | tables |
   - rag / session / workflow (3 rows)
3. DbConfig dataclass: all 6 fields with defaults; note embed_url does not exist;
   note __post_init__ validates parent dir
4. DB initialization flow: create_schema.py sequence; _build_rag_schema_sql(dims) / _build_session_schema_sql(dims);
   executescript(); migration code deleted
5. SQLiteHelper.open() PRAGMA sequence: vec load → WAL → synchronous → busy_timeout → FK(write_mode)
6. rag.sqlite schema: documents, chunks, chunks_fts (FTS5 DDL), chunks_vec (vec0 DDL with DIMS);
   note triggers chunks_ai/chunks_ad/chunks_au/chunks_vec_ad (undocumented in spec)
7. session.sqlite schema: sessions, messages, notes, tool_results, memories,
   memories_fts, memories_vec, memory_links
8. workflow.sqlite schema: tasks, attempts, processed_events, artifacts (from 07_ref-sqlite.md)
9. Vector search flow: validate_embedding_blob → chunks_vec KNN → JOIN chunks/documents

### Method

- Schema sections use column tables (name | type | constraints)
- Virtual table DDL shown verbatim for FTS5 and vec0
- Highlight "workflow" target as only in ref file (gap noted for 90)

### Details

- chunks_fts: content='chunks', content_rowid='chunk_id', tokenize='unicode61'
- chunks_vec: float[DIMS] where DIMS = embedding_dims from config (default 384)
- workflow.sqlite: tasks/attempts use idempotency_key for dedup; CASCADE on task deletion
- memories_vec: float[384] embedding; only written when embed_enabled=True

## Validation plan

- File exists at `docs/06_shared_04_db_architecture_and_schema.md`
- All 3 DB targets documented (rag / session / workflow)
- All schemas: 4 rag tables + 8 session tables + 4 workflow tables
- DbConfig all 6 fields present
- PRAGMA sequence in open() documented
