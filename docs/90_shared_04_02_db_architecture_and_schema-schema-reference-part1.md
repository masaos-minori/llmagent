---
title: "DB Architecture and Schema - Schema Reference (Part 1)"
category: shared
tags:
  - shared
  - db
  - rag-sqlite
  - session-sqlite
  - workflow-sqlite
  - timestamp-policy
related:
  - 90_shared_00_document-guide.md
  - 90_shared_04_01_db_architecture_and_schema-overview-and-config.md
  - 90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md
source:
  - 90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md
---

# DB Architecture and Schema

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)
- DB API → [90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md)

## 5. `rag.sqlite` スキーマ

### `documents` table

Document metadata: doc_id (INTEGER PK AUTOINCREMENT), url (TEXT UNIQUE NOT NULL), title (TEXT nullable), lang (TEXT NOT NULL CHECK ja/en), fetched_at (TEXT NOT NULL DEFAULT strftime('%Y-%m-%dT%H:%M:%SZ', 'now') — ISO-8601 UTC Z-suffix), etag (TEXT nullable), last_modified (TEXT nullable), chunking_strategy (TEXT NOT NULL DEFAULT 'text'). Timestamp format corrected in db/schema_sql.py _RAG_SCHEMA_TEMPLATE to use strftime('%Y-%m-%dT%H:%M:%SZ', 'now') instead of datetime('now'); all other tables' timestamp columns (created_at/updated_at etc) unified under same format.

### `chunks` table

Chunk metadata: chunk_id (INTEGER PK AUTOINCREMENT), doc_id (INTEGER NOT NULL FK → documents(doc_id) ON DELETE CASCADE), chunk_index (INTEGER NOT NULL), content (TEXT NOT NULL), normalized_content (TEXT nullable for English/code), chunk_type (TEXT NOT NULL DEFAULT 'text'), source_file (TEXT NOT NULL DEFAULT '').

### `chunks_fts` (FTS5 virtual table)

FTS5 virtual table for full-text search on chunk content. Uses COALESCE(new.normalized_content, new.content) for insertion/update triggers. Automatic synchronization via AFTER INSERT/AFTER UPDATE/AFTER DELETE triggers on chunks table. IMPORTANT: Do not manually synchronize chunks_fts after INSERT/UPDATE/DELETE — triggers handle it automatically.

### `chunks_vec` (sqlite-vec virtual table)

sqlite-vec virtual table for vector similarity search. Stores float32 little-endian BLOB. chunk_id INTEGER PRIMARY KEY, embedding FLOAT[DIMS] where DIMS replaced at runtime from embedding_dims config (default 384).
