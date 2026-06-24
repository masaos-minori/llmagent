# Implementation Procedure: docs/06_eventbus_*.md (8 files) + routing.md

## Goal

`scripts/eventbus/` 実装から 8 本の Event Bus ドキュメントを生成する。

## Scope

**In (新規 8 ファイル):**
- `docs/06_eventbus_00_document-guide.md`
- `docs/06_eventbus_01_system-overview.md`
- `docs/06_eventbus_02_http_api_and_runtime.md`
- `docs/06_eventbus_03_persistence_schema_and_replay.md`
- `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- `docs/06_eventbus_05_configuration_deploy_and_operations.md`
- `docs/06_eventbus_06_reference_api.md`
- `docs/06_eventbus_90_inconsistencies_and_known_issues.md`
- `routing.md` — Event Bus ルーティングエントリ追加

**Out:** ランタイムコードの変更

## Assumptions

1. 一次情報源: `scripts/eventbus/*.py`, `scripts/eventbus/schema.sql`
2. 差異は明示 (隠さない)
3. 言語: 日本語

## Procedure

### Phase 1: ソースファイル読み込み

以下を順に読む:
1. `scripts/eventbus/app.py`
2. `scripts/eventbus/config.py`
3. `scripts/eventbus/db.py`
4. `scripts/eventbus/dlq.py`
5. `scripts/eventbus/offsets.py`
6. `scripts/eventbus/schema.sql`
7. `scripts/eventbus/__init__.py` (存在する場合)

### Phase 2: 8 ドキュメント作成

各ファイルの内容の最低要件:

| ファイル | 必須セクション |
|---|---|
| 00_document-guide.md | 目的、読む順番、AI ルーティング、正規情報源ルール |
| 01_system-overview.md | 目的、アーキテクチャ、能力/限界、セキュリティモデル |
| 02_http_api_and_runtime.md | 全エンドポイント、リクエスト/レスポンス、障害動作 |
| 03_persistence_schema_and_replay.md | SQLite、WAL、events テーブル、フィールド意味、JSONL |
| 04_dlq_offsets_and_delivery_semantics.md | DLQ、オフセット、at-least-once、信頼性限界 |
| 05_configuration_deploy_and_operations.md | 設定フィールド、デプロイ、検証ステータス |
| 06_reference_api.md | モジュール別 API リファレンス |
| 90_inconsistencies_and_known_issues.md | スキーマ差異、reserved フィールド、未確認事項 |

### Phase 3: routing.md 更新

```markdown
| Event Bus (overview) | docs/06_eventbus_01_system-overview.md |
| Event Bus (HTTP API) | docs/06_eventbus_02_http_api_and_runtime.md |
| Event Bus (persistence) | docs/06_eventbus_03_persistence_schema_and_replay.md |
| Event Bus (DLQ/offsets) | docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md |
| Event Bus (config/ops) | docs/06_eventbus_05_configuration_deploy_and_operations.md |
| Event Bus (API ref) | docs/06_eventbus_06_reference_api.md |
| Event Bus (issues) | docs/06_eventbus_90_inconsistencies_and_known_issues.md |
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| 8ファイル存在 | `ls docs/06_eventbus_*.md \| wc -l` | 8 |
| routing.md 更新 | `grep "eventbus" routing.md` | 7+ エントリ |
| コード変更なし | `git diff scripts/` | no changes |
