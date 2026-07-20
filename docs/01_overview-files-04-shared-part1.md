---
title: "Shared Infrastructure File Structure: venv/db/ + scripts/db/ (Part 1/2)"
category: overview
tags:
  - shared
  - db
  - sqlite
  - file-structure
related:
  - 01_overview-files-04-shared-part2.md
  - 01_overview.md
---


# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:


``` text
/opt/llm/
├─ venv/                              # Python 仮想環境
│   └─ requirements.txt              # Python 依存パッケージ一覧
├─ db/
│   ├─ rag.sqlite                     # RAG ベクトル DB (documents/chunks/chunks_vec/chunks_fts) — see 90_shared_04 §3-§6
│   ├─ session.sqlite                 # エージェントセッション + メッセージ — see 90_shared_04 §2
│   └─ workflow.sqlite                # タスク追跡 + イベント処理 — see 90_shared_04 §7
├─ scripts/
│   ├─ db/                                  # DB 層パッケージ
│   │   ├─ __init__.py                      # モジュール初期化
│   │   ├─ create_schema.py                 # SQLite スキーマ初期化
│   │   ├─ schema_sql.py                    # build_rag_schema_sql / build_session_schema_sql / build_workflow_schema_sql
│   │   ├─ helper.py                        # 接続管理 (WAL / busy_timeout)
│   │   ├─ maintenance.py                   # 運用ポリシー
│   │   ├─ config.py                        # DbConfig データクラス・SQLite パスビルダ
│   │   ├─ models.py                        # WalCheckpointCounts / PurgeCounts / DbHealthMetrics / DocumentRow / SessionRow / MessageRow
│   │   ├─ store.py                         # Protocol 抽象レイヤー
│   │   ├─ store_protocols.py               # VectorStore / DocumentStore / SessionStore Protocol 定義
│   │   ├─ store_impl.py                    # SQLiteVectorStore / SQLiteDocumentStore / SQLiteSessionStore 実装
│   │   ├─ rag_consistency.py               # RAG インデックス整合性チェック
│   │   ├─ rotation.py                      # データベースローテーション
│   │   └─ recovery.py                      # コーrupted DB リカバリ
```

## Related Documents

- `01_overview-files-04-shared-part2.md`

## Keywords

shared
db
sqlite
file-structure
