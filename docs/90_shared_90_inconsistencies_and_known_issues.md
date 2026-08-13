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

Migration date: 2026-07-23; Source format: existing bullet format (Type, Impact scope, Statement A/B, Current safe interpretation, Recommended action, Notes for AI reference); Destination format: common template (17 fields); Note: existing entry content preserved; missing fields filled with 'unconfirmed'.

# Shared/DB の不整合と既知の問題

本ファイルは、`shared/` および `db/` レイヤーにおけるドキュメント間の既知の不整合、実装上の不具合、
未文書化の領域、未実装の機能、未定義の挙動をすべて記録する。

各項目は以下の形式に従う:
- **種別:** `ドキュメント不整合` / `実装上の不具合` / `未文書化` / `未実装` / `未定義` / `確認が必要`

---

### SHARED-001: recover_corruption() が実ページ破損時に sqlite3.DatabaseError を捕捉せず伝播する

recover_corruption() は実ページ破損時に sqlite3.DatabaseError を捕捉せず伝播する。Status: open / Severity: High / Type: implementation-bug。影響: 物理的に破損したファイルに対して例外が発生する可能性がある。対応: _run_integrity_check() の except 節に sqlite3.DatabaseError（または共通基底 sqlite3.Error）を追加。

---


