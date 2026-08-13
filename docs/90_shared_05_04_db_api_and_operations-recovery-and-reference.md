---
title: "DB API and Operations - Recovery and Reference"
category: shared
tags:
  - shared
  - db
  - corruption-recovery
  - error-handling
  - verification
  - ai-reference
related:
  - 90_shared_00_document-guide.md
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
  - 90_shared_05_02_db_api_and_operations-protocol-and-backend.md
  - 90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md
source:
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
---

# DB API and Operations

- Schema → [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md)

## 9. Corruption Recovery

`from db.recovery import recover_corruption; from db.models import RecoveryResult; result = recover_corruption(backup_path='/opt/llm/db/backup/rag.sqlite', target='rag', dry_run=False).` `target` assumes only `'rag'` (default) or `'session'`; implementation uses two-way branch checking `target=='rag'` to determine `db_path` for display purposes, so passing `'workflow'` or `'eventbus'` causes fallback to `session_db_path` on display while actual DB connection resolved by string (`'workflow'`/`'eventbus'`) passed to `SQLiteHelper(target)`; both mismatching, do not pass anything other than `'rag'`/`'session'` to target (Explicit in code — `db/recovery.py::recover_corruption`). `RecoveryResult`(dataclass frozen=True): `success` bool, `action` str (`'vacuum'|'vacuum_failed'|'restored'|'no_backup'|'error'`), `detail` str|None, `dry_run` bool=False.

---

## 10. エラーハンドリング

`sqlite3.OperationalError`(busy/locked): automatic wait via PRAGMA busy_timeout (default 30 seconds); `sqlite3.IntegrityError`: propagates to caller; does not occur in upsert path; sqlite-vec load error: `sqlite3.OperationalError` → connection failure; schema DDL failure: exception re-thrown from executescript(); integrity check failure: log error + attempt restore from backup; prune_old_memories failure: STRICT — exception propagates; BEST_EFFORT — returns MaintenanceResult(success=False); commit() error: WARNING logged + sqlite3.OperationalError re-thrown; close() error: WARNING logged only; no exception thrown.

---

## 11. DB再作成手順

Schema change requires DB recreation — migration feature does not exist. Step 1: Archive — execute rotate_all_dbs() to archive all three production DBs. Step 2: Delete — manually delete DB files; paths resolved from agent.toml rag_db_path/session_db_path/workflow_db_path/eventbus_db_path keys (db/config.py::DbConfig); create_schema() also recreates eventbus.sqlite, so include /opt/llm/db/eventbus.sqlite if deleting (Explicit in code — `db/create_schema.py`). Step 3: Recreate — execute create_schema() to initialize empty DBs. Important notes: recreated DB is empty — existing records not automatically migrated; create_schema() is wrapper calling create_rag_schema()→create_session_schema()→create_workflow_schema()→create_eventbus_schema() unconditionally sequentially; each schema DDL protected by IF NOT EXISTS so idempotent even against existing files (Explicit in code — `db/create_schema.py`); condition 'initialize only if eventbus.sqlite does not exist' does not exist in implementation; if only one DB needs recreation use individual functions: create_rag_schema(), create_session_schema(), create_workflow_schema(), create_eventbus_schema().

---

## 12. 検証計画

Schema initialization: pytest tests/test_create_schema.py; DB maintenance: pytest tests/test_db_maintenance.py; Type check: mypy scripts/db/; Full integration: create DB → check all tables exist — python -c 'from db.create_schema import create_schema; create_schema()'; sqlite3 /opt/llm/db/rag.sqlite '.tables'; sqlite3 /opt/llm/db/session.sqlite '.tables'.

---

## 13. AIリファレンスガイド

Open DB connection: with SQLiteHelper('rag').open(row_factory=True) as db:. Write atomically: open(write_mode=True) context within with db.begin_immediate():. What does target='workflow' connect to: workflow.sqlite — task tracking DB. How to validate embedding BLOB: db.store's validate_embedding_blob(blob). How to purge old sessions: purge_old_sessions(db, RetentionConfig(...)) — returns MaintenanceResult; check .success. How to recover from corruption: recover_corruption(backup_path=..., target='rag'). Does prune_old_memories catch exceptions: STRICT (default) — propagates; BEST_EFFORT — caught and stored in MaintenanceResult. How to use BEST_EFFORT mode: pass mode=MaintenanceMode.BEST_EFFORT to vacuum_db, purge_old_sessions, prune_old_memories. How to verify RAG consistency: check_rag_consistency(db) → is_consistent(report) + summarize_issues(report).


