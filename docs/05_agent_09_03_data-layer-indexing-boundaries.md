---
title: "Agent Data Layer - Indexing and Boundaries"
category: agent
tags:
  - agent
  - data-layer
  - fts5
  - workflow-sqlite
  - persistence-boundaries
related:
  - 05_agent_00_document-guide.md
  - 05_agent_09_01_data-layer-session-db.md
  - 05_agent_09_02_data-layer-access-patterns.md
source:
  - 05_agent_09_01_data-layer-session-db.md
---

# エージェントデータ層

- 状態と永続化 → [05_agent_04_01_state-and-persistence-state-model-part1.md](05_agent_04_01_state-and-persistence-state-model-part1.md)

## Context Manager Pattern for DB Access(DBアクセスにおけるコンテキストマネージャパターン)

`SQLiteHelper`(エージェント/RAG層のあらゆる箇所で使用される):

```python
with SQLiteHelper().open(write_mode=True, row_factory=True) as db:
    db.execute(...)
```

- `write_mode=True` → WALモード + 外部キーを有効化する
- `row_factory=True` → カラム名でのアクセスを有効化する(`row["column"]`)
- クエリごとにオープンする(コネクションプールではない)。DB_PATH と SQLITE_VEC_SO は遅延初期化される

---

## FTS5 Index (`chunks_fts`)(FTS5インデックス)

`rag.sqlite` 内のFTS5仮想テーブル `chunks_fts` は、トリガーによって同期される:
- `chunks_ai`(INSERT後): `chunks_fts(COALESCE(normalized_content, content))` へ挿入
- `chunks_au`(UPDATE後): 削除+再挿入
- `chunks_ad`(DELETE後): `chunks_fts` から削除

`/db rag rebuild-fts` は `chunks` のデータからFTS5インデックスを破棄・再作成する。
`SELECT COUNT(*) FROM chunks_fts` ≠ `SELECT COUNT(*) FROM chunks` の場合に使用する。

---

## Workflow SQLite (`workflow.sqlite`)(ワークフロー用SQLite)

`agent/workflow/state_store.py` によって管理される。

| Table | Contents |
|---|---|
| `tasks` | 1ターン試行ごとに1行。status: `pending → running → [pending_approval →] completed \| halted \| failed` |
| `attempts` | タスク内のリトライ試行。status: `running \| completed \| failed` |
| `processed_events` | 冪等性の強制。ステージの重複実行を防止する |
| `approvals` | 承認ゲート。status: `pending → approved \| rejected` |
| `artifacts` | ステージコールバックが生成するURI |

`config/workflows/default.json` が存在する場合に使用される。存在しない場合は起動に失敗する（ワークフロー必須）。

---

## Non-Message Persistence Boundaries(メッセージ以外の永続化の境界)

| Store | Role | LLMに可視か | Contents |
|---|---|---|---|
| `messages` | 会話フロー履歴(正本) | yes | LLMに渡されるメッセージシーケンス。大きな出力は要約のみを保存 |
| `session_diagnostics` | 診断専用イベント | no | LLM転送エラー、ガードヒント。`DiagnosticStore.save()` によって書き込まれる |
| `workflow.artifacts` | ワークフローアーティファクト参照 | no | ワークフローステージコールバックが生成するURI。`workflow.sqlite` に保存 |
| `audit.log` | 運用トレース | no | JSON-lines形式の監査イベント(`turn_start`、`turn_end`、MCP呼び出し)。[04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md) を参照 |

LLMに可視な会話フロー以外の目的で `messages` を使用することは禁止される — 診断、
アーティファクト、監査のデータは上記の非messageストアに属する。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_09_01_data-layer-session-db.md`
- `05_agent_09_02_data-layer-access-patterns.md`

## Keywords

FTS5 index
chunks_fts
workflow.sqlite
non-message persistence boundaries
