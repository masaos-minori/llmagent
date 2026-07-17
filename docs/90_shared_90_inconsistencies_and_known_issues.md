---
title: "Shared/DB Inconsistencies and Known Issues"
category: shared
tags:
  - shared
  - db
  - inconsistency
  - known issue
  - bug
  - documentation gap
  - design concern
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_03_overview-constraints-and-reference.md
  - 90_shared_02_01_types_and_protocols-core-types.md
  - 90_shared_03_01_runtime_and_execution-config-and-logging.md
source:
  - 90_shared_90_inconsistencies_and_known_issues.md
---

# Shared/DB の不整合と既知の問題

本ファイルは、`shared/` および `db/` レイヤーにおけるドキュメント間の既知の不整合、実装上の不具合、
未文書化の領域、未実装の機能、未定義の挙動をすべて記録する。

各項目は以下の形式に従う:
- **種別:** `ドキュメント不整合` / `実装上の不具合` / `未文書化` / `未実装` / `未定義` / `確認が必要`

---

## `recover_corruption()` が実ページ破損時に `sqlite3.DatabaseError` を捕捉せず伝播する

- **種別:** `実装上の不具合`
- **影響範囲:** `db/recovery.py::_run_integrity_check()`, `db/recovery.py::recover_corruption()`
- **現在の挙動:** `_run_integrity_check()` の `except` 節は `(sqlite3.OperationalError, ValueError, RuntimeError)` のみを捕捉する。実際にページレベルで物理破損した SQLite ファイルに対しては、`SQLiteHelper.open()` 内の `PRAGMA journal_mode=WAL` 実行時に `sqlite3.DatabaseError` が送出されるが、`DatabaseError` は `OperationalError` のサブクラスではないため捕捉されず、`recover_corruption()` の呼び出し元まで未処理のまま伝播する。`_run_integrity_check()` 自身のdocstringが示す「開けない場合は `(None, error_detail)` を返す」という契約は、この破損パターンでは満たされない。`backup_path` の有無や `dry_run` の値に関わらず同じ経路で発生するため、`action="no_backup"` や dry-run 分岐（`_handle_dry_run()`）には到達しない。
- **裏付け:** `tests/integration/test_session_recovery.py` の `test_e02_recover_corruption_raises_uncaught_database_error`, `test_e03_recover_corruption_no_backup_raises_uncaught_database_error`, `test_e04_recover_corruption_dry_run_raises_before_mutation_check` が、`corrupt_wal_db` フィクスチャ（実際にバイト単位で破損させた WAL モード DB）に対する呼び出しで再現を確認済み。
- **Recommended action:** `_run_integrity_check()` の `except` 節に `sqlite3.DatabaseError`（または共通基底の `sqlite3.Error`）を追加し、`recover_corruption()` が破損時に常に `RecoveryResult` を返すようにする。
- **Notes for AI reference:** `recover_corruption()` の呼び出し元は、物理破損したファイルに対してこの関数が例外を送出しうる（`RecoveryResult` を返すとは限らない）ことを前提に扱うこと。

---

## Related Documents

- [90_shared_00_document-guide.md](90_shared_00_document-guide.md)
- [90_shared_01_03_overview-constraints-and-reference.md](90_shared_01_03_overview-constraints-and-reference.md)
- [90_shared_02_01_types_and_protocols-core-types.md](90_shared_02_01_types_and_protocols-core-types.md)
- [90_shared_03_01_runtime_and_execution-config-and-logging.md](90_shared_03_01_runtime_and_execution-config-and-logging.md)

## Keywords

inconsistency
known issue
bug
documentation gap
design concern
