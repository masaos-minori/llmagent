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

## 移行ノート

- 移行日: 2026-07-23
- 移行元フォーマット: 既存のバレット形式（Type, Impact scope, Statement A/B, Current safe interpretation, Recommended action, Notes for AI reference）
- 移行先フォーマット: 共通テンプレート（17フィールド）
- 注: 既存のエントリ内容は維持。不足フィールドは「未確認」で埋める。

# Shared/DB の不整合と既知の問題

本ファイルは、`shared/` および `db/` レイヤーにおけるドキュメント間の既知の不整合、実装上の不具合、
未文書化の領域、未実装の機能、未定義の挙動をすべて記録する。

各項目は以下の形式に従う:
- **種別:** `ドキュメント不整合` / `実装上の不具合` / `未文書化` / `未実装` / `未定義` / `確認が必要`

---

### SHARED-001: recover_corruption() が実ページ破損時に sqlite3.DatabaseError を捕捉せず伝播する

- **ID**: SHARED-001
- **Title**: recover_corruption() が実ページ破損時に sqlite3.DatabaseError を捕捉せず伝播する
- **Status**: open
- **Severity**: High
- **Area**: Shared/DB
- **Type**: implementation-bug
- **Source**: db/recovery.py::_run_integrity_check(), db/recovery.py::recover_corruption()
- **Owner**: Unassigned
- **First Found**: 未確認
- **Target**: db/recovery.py
- **Related**: tests/integration/test_session_recovery.py
- **Summary**: _run_integrity_check() が sqlite3.DatabaseError を捕捉せず、recover_corruption() が RecoveryResult を返さない
- **Current Description**: except 節が (sqlite3.OperationalError, ValueError, RuntimeError) のみを捕捉。DatabaseError は OperationalError のサブクラスではないため捕捉されない
- **Observed Implementation**: PRAGMA journal_mode=WAL 実行時に sqlite3.DatabaseError が送出され、recover_corruption() の呼び出し元まで未処理のまま伝播
- **Impact**: 物理破損したファイルに対して recover_corruption() が例外を送出しうる
- **Recommended Action**: _run_integrity_check() の except 節に sqlite3.DatabaseError（または共通基底の sqlite3.Error）を追加
- **Resolution Notes**: 完了待ち

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
