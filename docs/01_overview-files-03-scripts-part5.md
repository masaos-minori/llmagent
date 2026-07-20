---
title: "Scripts File Structure: MCP: shell/rag-pipeline/cicd/mdq/git (Part 5/5)"
category: overview
tags:
  - scripts
  - agent
  - mcp-server
  - file-structure
related:
  - 01_overview-files-03-scripts-part1.md
  - 01_overview-files-03-scripts-part2.md
  - 01_overview-files-03-scripts-part3.md
  - 01_overview-files-03-scripts-part4.md
  - 01_overview.md
---


# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:


``` text
│   │   ├─ shell/                           # シェル MCP サーバ (:8009)
│   │   │   ├─ server.py                    # シェル MCP サーバ
│   │   │   ├─ service.py                   # シェルサービス
│   │   │   ├─ tools.py                     # シェルツール
│   │   │   ├─ subprocess_runner.py         # シェルサブプロセスランナー
│   │   │   ├─ service_static_helpers.py    # シェル静的ヘルパー
│   │   │   ├─ models.py                    # シェルデータモデル
│   │   │   └─ __init__.py                  # シェル MCP パッケージ初期化
│   │   ├─ rag_pipeline/                    # RAG パイプライン MCP サーバ (:8010)
│   │   │   ├─ server.py                    # RAG MCP サーバ
│   │   │   ├─ service.py                   # RAG サービス
│   │   │   ├─ tools.py                     # RAG ツール
│   │   │   ├─ models.py                    # RAG データモデル
│   │   │   ├─ document_manager.py          # RAG ドキュメントマネージャ
│   │   │   └─ __init__.py                  # RAG MCP パッケージ初期化
│   │   ├─ cicd/                            # GitHub Actions CI/CD MCP サーバ (:8012)
│   │   │   ├─ server.py                    # CI/CD MCP サーバ
│   │   │   ├─ service.py                   # CI/CD サービス
│   │   │   ├─ tools.py                     # CI/CD ツール
│   │   │   ├─ models.py                    # CI/CD データモデル
│   │   │   ├─ service_init.py              # CI/CD サービス初期化
│   │   │   ├─ service_business.py          # CI/CD ビジネスロジックサービス
│   │   │   ├─ service_defs.py              # CI/CD サービス定義
│   │   │   ├─ service_guards.py            # CI/CD セキュリティガード
│   │   │   ├─ service_github_actions.py    # CI/CD GitHub Actions サービス
│   │   │   ├─ service_github_actions_composite.py  # CI/CD GitHub Actions コンポジットサービス
│   │   │   ├─ service_github_actions_job.py        # CI/CD GitHub Actions ジョブサービス
│   │   │   ├─ exception_handlers.py        # CI/CD 例外ハンドラ
│   │   │   └─ __init__.py                  # CI/CD MCP パッケージ初期化
│   │   ├─ mdq/                             # Markdown Context Compression Engine MCP サーバ (:8013)
│   │   │   ├─ server.py                    # MDQ MCP サーバ
│   │   │   ├─ service.py                   # MDQ サービス
│   │   │   ├─ tools.py                     # MDQ ツール
│   │   │   ├─ models.py                    # MDQ データモデル
│   │   │   ├─ indexer.py                   # MDQ インデクサ
│   │   │   ├─ search.py                    # MDQ 検索
│   │   │   ├─ parser.py                    # MDQ パーザ
│   │   │   ├─ audit_target.py              # MDQ 監査ターゲット
│   │   │   ├─ auth.py                      # MDQ 認証
│   │   │   ├─ db_schema.py                 # MDQ データベーススキーマ
│   │   │   ├─ db_fts.py                    # MDQ FTS データベース
│   │   │   ├─ db_grep.py                   # MDQ grep データベース
│   │   │   ├─ health_check.py              # MDQ ヘルスチェック
│   │   │   ├─ index_delete.py              # MDQ インデックス削除
│   │   │   ├─ __main__.py                  # MDQ CLI エントリポイント
│   │   │   └─ __init__.py                  # MDQ MCP パッケージ初期化
│   │   └─ git/                             # ローカル git 操作 MCP サーバ (:8014)
│   │       ├─ server.py                    # Git MCP サーバ
│   │       ├─ service.py                   # Git サービス
│   │       ├─ tools.py                     # Git ツール
│   │       ├─ models.py                    # Git データモデル
│   │       ├─ git_security.py              # Git セキュリティ
│   │       ├─ format_output.py             # Git 出力フォーマット
│   │       └─ __init__.py                  # Git MCP パッケージ初期化
```

## Related Documents

- `01_overview-files-03-scripts-part1.md`
- `01_overview-files-03-scripts-part2.md`
- `01_overview-files-03-scripts-part3.md`
- `01_overview-files-03-scripts-part4.md`

## Keywords

scripts
agent
mcp-server
file-structure
