---
title: "Agent Data Layer - Session DB"
category: agent
tags:
  - agent
  - data-layer
  - session-sqlite
  - rag-sqlite
  - sqlite-databases
related:
  - 05_agent_00_document-guide.md
  - 05_agent_09_02_data-layer-access-patterns.md
  - 05_agent_09_03_data-layer-indexing-boundaries.md
source:
  - 05_agent_09_01_data-layer-session-db.md
---

# エージェントデータ層

- 状態と永続化 → [05_agent_04_01_state-and-persistence-state-model.md](05_agent_04_01_state-and-persistence-state-model.md)

## Purpose(目的)

エージェント層で使用されるSQLiteテーブル構造、データ所有権の境界、
およびエージェント層とRAG層の間の責任境界を文書化する。

---

## SQLite Databases(SQLiteデータベース)

| Database | Path | Owner | Purpose |
|---|---|---|---|
| `session.sqlite` | `/opt/llm/db/session.sqlite` | Agent layer | セッション、メッセージ |
| `rag.sqlite` | `/opt/llm/db/rag.sqlite` | RAG layer | ドキュメント、チャンク、ベクトル |
| `mdq.sqlite` | `/opt/llm/db/mdq.sqlite` | MCP (mdq-mcp) | Markdownドキュメントのインデックス化とコンテキスト圧縮 |
| `workflow.sqlite` | `/opt/llm/db/workflow.sqlite` | Workflow engine | タスク、試行、処理済みイベント、承認、アーティファクト |

---

## session.sqlite Tables(session.sqlite のテーブル)

| Table | Purpose |
|---|---|
| `sessions` | セッションのメタデータ |
| `messages` | 会話履歴(LLMに可視) |
| `memories` | インデックス化されたメモリエントリ |
| `memories_fts` | メモリ内容に対するFTS5インデックス |
| `memory_links` | メモリ間の多対多リンク |
| `memories_vec` | 任意のKNN埋め込み |
| `session_diagnostics` | 診断イベント(LLM転送エラー、ガードヒント) |

### `sessions` table

| Column | Type | Description |
|---|---|---|
| `session_id` | INTEGER PK | 自動増分 |
| `created_at` | TEXT | ISO-8601形式のタイムスタンプ |
| `title` | TEXT | セッションタイトル(最大50文字)。最初のターンでLLMが生成する |

### `messages` table

| Column | Type | Description |
|---|---|---|
| `message_id` | INTEGER PK | 自動増分 |
| `session_id` | INTEGER FK | → `sessions(session_id)` ON DELETE CASCADE |
| `role` | TEXT | `user` / `assistant` / `tool` / `system` — `diagnostic` **ではない** |
| `content` | TEXT | メッセージのテキスト内容 |
| `tool_calls` | TEXT | JSON形式でシリアライズされたtool_calls(assistantロールのみ) |
| `tool_call_id` | TEXT | ツール呼び出しの応答関連付けID(toolロールのみ) |
| `created_at` | TEXT | 行作成時のタイムスタンプ |

**有効なロール:** `user`、`assistant`、`tool`、`system`。診断イベントは `messages` テーブルには保存されない。`DiagnosticStore.save()` を通じて `session_diagnostics` テーブルにのみ永続化される。

### `session_diagnostics` table

診断イベント(LLM転送エラー、ガードヒント、部分完了)を保存する。`messages` テーブルとは分離されており、`fetch_messages()` から参照されることはない。

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | 自動増分 |
| `session_id` | INTEGER | 関連するセッション(セッション確立前のイベントの場合はNULLの可能性あり) |
| `kind` | TEXT | イベント種別(`llm_transport_error`、`guard_hint` など) |
| `content` | TEXT | 診断ペイロード |
| `workflow_id` | TEXT | 任意のワークフローID |
| `task_id` | TEXT | 任意のタスクID |
| `created_at` | TEXT | 行作成時のタイムスタンプ |

### SessionMessageRepository vs SQLiteSessionStore

| Component | Role | Validation | Persistence |
|---|---|---|---|
| `SessionMessageRepository` | 会話メッセージのビジネスロジック層 | ロール検証、strict_mode、スキップカウンタ、content=Noneの正規化、tool_callsのJSONエンコード/デコード | セッション依存の永続化 |
| `SQLiteSessionStore` | DBアダプタ層 | スキーマ整合性のみ | 単純なDB操作(INSERT/LIST) |

`SessionMessageRepository` が担うもの:
- ロール検証(`user` / `assistant` / `tool` / `system`)
- strict_modeの動作(スキップ時に `RuntimeError` を発生)
- セッション不在時の保存回避(スキップカウンタ)
- `content=None` の正規化
- tool_callsのJSONエンコード/デコード

`SQLiteSessionStore` が担うもの:
- 単純なDBのINSERT/LIST操作
- スキーマに準拠した永続化
- 最小限の検証のみ

**規約:** 検証・エンコードロジックを `SQLiteSessionStore` に重複させてはならない。これは薄いDBアダプタであり、ロール検証もcontentの正規化もJSONエンコードも行わない。これらの関心事はすべて `SessionMessageRepository` に属する。

共有層の責任境界の見方については
[90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md) を参照。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_09_02_data-layer-access-patterns.md`
- `05_agent_09_03_data-layer-indexing-boundaries.md`

## Keywords

session.sqlite
sessions table
messages table
session_diagnostics
rag.sqlite
