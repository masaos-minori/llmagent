---
title: "Agent Data Layer - Session DB"
category: agent
tags:
  - agent
  - data-layer
  - session-sqlite
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_09_01_data-layer-session-db.md
---

# エージェントデータ層

- 状態と永続化 → [05_agent_04_01_state-and-persistence-state-model-part1.md](05_agent_04_01_state-and-persistence-state-model-part1.md)

## Purpose

セッションDBの責任範囲、データ所有権の境界、およびRAG層との責任境界について文書化する。

## Design Intent

### データベースの責任分割

| Database | Owner | Responsibility |
|---|---|---|
| `session.sqlite` | Agent layer | セッション、メッセージ、メモリ、診断 |
| `rag.sqlite` | RAG layer | ドキュメント、チャンク、ベクトル |
| `mdq.sqlite` | MCP (mdq-mcp) | Markdownドキュメントのインデックス化とコンテキスト圧縮 |
| `workflow.sqlite` | Workflow engine | タスク、試行、処理済みイベント、承認、アーティファクト |

**Design judgment**: `session_diagnostics` は `messages` と分離されている — 診断イベントはLLMに可視ではないため、会話履歴とは別管理とする。

### SessionMessageRepository vs SQLiteSessionStore の責任分割

`SessionMessageRepository` が担うもの:
- ロール検証 (`user` / `assistant` / `tool` / `system`)
- strict_modeの動作 (スキップ時に `RuntimeError` を発生)
- セッション不在時の保存回避
- `content=None` の正規化
- tool_callsのJSONエンコード/デコード

`SQLiteSessionStore` が担うもの:
- 単純なDBのINSERT/LIST操作
- スキーマに準拠した永続化
- 最小限の検証のみ

**Design judgment**: 検証・エンコードロジックを `SQLiteSessionStore` に重複させてはならない。これは薄いDBアダプタであり、ロール検証もcontentの正規化もJSONエンコードも行わない。これらの関心事はすべて `SessionMessageRepository` に属する。

### セッション保持ポリシー

`db/maintenance.py` の `purge_old_sessions()` が、`RetentionConfig`に基づき古いセッションを年齢基準→件数基準の順で削除する。`sessions` 削除は `ON DELETE CASCADE` により `messages` にも伝播する。

### メモリテーブルの所有権

`use_memory_layer=True` の場合、メモリサブシステムはJSONLとSQLiteの両方を使用する:

| Storage | Path | Contents |
|---|---|---|
| JSONL | `{memory_jsonl_dir}/memories.jsonl` | インポート/エクスポートおよび災害復旧用の追記専用アーカイブ |
| SQLite: `memories` | `session.sqlite` | 現在のメモリ状態の正本 |
| SQLite: `memories_fts` | 同じDB | メモリ内容に対するFTS5インデックス |
| SQLite: `memory_links` | 同じDB | メモリ間の多対多リンク |
| SQLite: `memories_vec` | 同じDB | 任意のKNN埋め込み |

**Design judgment**: SQLiteのメモリテーブルが現在のメモリ状態の正本である。JSONLはインポート/エクスポートおよび災害復旧用の追記専用アーカイブとして保持される。削除およびpin/unpin状態の変更はJSONLから再生されない。

### session_diagnostics の役割

- 診断イベント(LLM転送エラー、ガードヒント、部分完了)を保存
- `messages` テーブルとは分離されており、`fetch_messages()` から参照されることはない
- `save()` は挿入前に `_filter_sensitive_fields()` を無条件に適用し、機微フィールドをフィルタリング
- `encrypt=True` で暗号化可能だが、`fetch()` に復号処理は実装されていない
- `_purge_old_diagnostics()` で保持ポリシー (既定30日) を適用

**Design judgment**: 機微フィールドのフィルタリングは暗号化とは独立して適用される。暗号化キーが未設定の場合でもフィルタリングは有効。

## Responsibility Boundary

- **正典**: `shared/tool_executor.py`, `agent/diagnostic_store.py`, `db/maintenance.py`
- **Schema**: `schema_sql.py` (詳細なスキーマ定義の権威)

## Key Constraints

- `messages` テーブルの有効なロール: `user` / `assistant` / `tool` / `system` — `diagnostic` **ではない**
- 診断イベントは `session_diagnostics` テーブルにのみ永続化される
- 検証・エンコードロジックを `SQLiteSessionStore` に重複させてはならない
- JSONLは追記専用アーカイブ — 削除や状態変更は再生されない

## Operational Notes

- 不明

## Known Limitations

- 暗号化された `session_diagnostics` の行は `fetch()` で復号されない

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_09_02_data-layer-access-patterns.md`
- `05_agent_09_03_data-layer-indexing-boundaries.md`

## Keywords

session.sqlite
session_diagnostics
SessionMessageRepository
SQLiteSessionStore
session retention
