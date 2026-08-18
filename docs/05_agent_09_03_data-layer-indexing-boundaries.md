---
title: "Agent Data Layer - Indexing and Boundaries"
category: agent
tags:
  - agent
  - data-layer
  - fts5
  - workflow-sqlite
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_09_03_data-layer-indexing-boundaries.md
---

# エージェントデータ層

- 状態と永続化 → [05_agent_04_01_state-and-persistence-state-model.md](05_agent_04_01_state-and-persistence-state-model.md)

## Purpose

DBアクセスにおけるコンテキストマネージャパターン、FTS5インデックス、ワークフローDBの役割について文書化する。

## Design Intent

### コンテキストマネージャパターン for DBアクセス

`SQLiteHelper`(エージェント/RAG層のあらゆる箇所で使用される):

```python
with SQLiteHelper().open(write_mode=True, row_factory=True) as db:
    db.execute(...)
```

- `write_mode=True` → WALモード + 外部キーを有効化する
- `row_factory=True` → カラム名でのアクセスを有効化する (`row["column"]`)
- クエリごとにオープンする (コネクションプールではない)。DB_PATH と SQLITE_VEC_SO は遅延初期化される

### FTS5インデックス

`rag.sqlite` 内のFTS5仮想テーブル `chunks_fts` は、トリガーによって同期される:
- `chunks_ai`(INSERT後): `chunks_fts(COALESCE(normalized_content, content))` へ挿入
- `chunks_au`(UPDATE後): 削除+再挿入
- `chunks_ad`(DELETE後): `chunks_fts` から削除

`/session rag-rebuild-fts` は `chunks` のデータからFTS5インデックスを破棄・再作成する。`SELECT COUNT(*) FROM chunks_fts` ≠ `SELECT COUNT(*) FROM chunks` の場合に使用する。

### ワークフロー用SQLite (`workflow.sqlite`)

`agent/workflow/state_store.py` によって管理される:

| Table | Contents |
|---|---|
| `tasks` | 1ターン試行ごとに1行 |
| `attempts` | タスク内のリトライ試行 |
| `processed_events` | 冪等性の強制 |
| `approvals` | 事後実行承認レコード |
| `artifacts` | ステージコールバックが生成するURI |

**Design judgment**: `config/workflows/default.json` が存在する場合に使用される。存在しない場合は起動に失敗する（ワークフロー必須）。

### メッセージ以外の永続化の境界

| Store | Role | LLMに可視か | Contents |
|---|---|---|---|
| `messages` | 会話フロー履歴(正本) | yes | LLMに渡されるメッセージシーケンス |
| `session_diagnostics` | 診断専用イベント | no | LLM転送エラー、ガードヒント |
| `workflow.artifacts` | ワークフローアーティファクト参照 | no | ワークフローステージコールバックが生成するURI |
| `audit.log` | 運用トレース | no | JSON-lines形式の監査イベント |

**Design judgment**: LLMに可視な会話フロー以外の目的で `messages` を使用することは禁止される — 診断、アーティファクト、監査のデータは上記の非messageストアに属する。

## Responsibility Boundary

- **正典**: `shared/sqlite_helper.py` (SQLiteHelper), `agent/workflow/state_store.py` (StateStore)
- **Schema**: `schema_sql.py` (権威)

## Key Constraints

- `messages` テーブルの有効なロール: `user` / `assistant` / `tool` / `system` — `diagnostic` **ではない**
- LLMに可視な会話フロー以外の目的で `messages` を使用することは禁止
- `workflow.sqlite` はワークフロー必須 — 設定ファイルが存在しない場合は起動に失敗する

## Operational Notes

- 不明

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_09_01_data-layer-session-db.md`
- `05_agent_09_02_data-layer-access-patterns.md`

## Keywords

FTS5 index
workflow.sqlite
non-message persistence boundaries
context manager pattern
