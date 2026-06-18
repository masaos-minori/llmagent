# Implementation: workflow.sqlite を全docs で first-class DB として扱う (req 72)

## Goal

workflow.sqlite を rag.sqlite / session.sqlite と並列に全関連ドキュメントへ追記し、
DOCMISS-01 を RESOLVED にする。

## Changes

### `docs/01_overview-files.md`
- db/ 配下に session.sqlite と workflow.sqlite を追加 (schema参照付き)

### `docs/02_deployment.md`
- §3.0 「プラットフォーム DB 概要」を新設: 3 DB のパス・設定キー・用途テーブル

### `docs/05_agent_04_state-and-persistence.md`
- 末尾に「Platform Databases」セクションを追加: 3 DB の 3 行テーブル

### `docs/05_agent_07_cli-and-commands.md`
- /db コマンドテーブル後に注記追加: /db は rag.sqlite 対象; session/workflow は SQLiteHelper 経由

### `docs/05_agent_10_operations-and-observability.md`
- DB verification セクションを 3 DB 分に拡張 (session.sqlite・workflow.sqlite の確認コマンド追加)

### `docs/05_agent_90_inconsistencies_and_known_issues.md`
- DOCMISS-01 エントリを新規追加 (RESOLVED、5 ドキュメントへの追記を記録)

### `docs/06_shared_90_inconsistencies_and_known_issues.md`
- DOCMISS-01 の recommended action を "None" に変更; 解決範囲を記述
