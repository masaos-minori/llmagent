---
title: "Scripts File Structure: MCP: web-search/file/github (Part 4/5)"
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
  - 01_overview-files-03-scripts-part5.md
  - 01_overview.md
---


# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:


```
│   ├─ mcp_servers/                           # MCP サーバパッケージ
│   │   └─ __init__.py                      # MCP パッケージ初期化
│   │   ├─ models.py                        # /v1/call_tool 統合エンドポイント共通 Pydantic モデル
│   │   ├─ server.py                        # MCP サーバ HTTP 起動共通基底クラス
│   │   ├─ audit.py                         # MCP ツール実行監査ログ (JSON-lines 1 行/実行)
│   │   ├─ dispatch.py                      # dispatch_tool(): DispatchResult を返すツールルーティングヘルパー
│   │   ├─ health_response.py               # make_health_response(): /health エンドポイント共通レスポンス生成
│   │   ├─ tool_validators.py               # @register_validator: git_commit / git_push / trigger_workflow / shell_run 等の入力バリデータ
│   │   ├─ web_search/                      # Web 検索 MCP サーバ (DuckDuckGo, :8004)
│   │   │   ├─ server.py                    # Web 検索 MCP サーバ
│   │   │   ├─ tools.py                     # Web 検索ツール
│   │   │   ├─ models.py                    # Web 検索データモデル
│   │   │   ├─ search_provider.py           # Web 検索プロバイダ
│   │   │   ├─ formatters.py                # Web 検索フォーマッタ
│   │   │   └─ __init__.py                  # Web 検索パッケージ初期化
│   │   ├─ file/                            # ファイル MCP サーバ群 (:8005/:8007/:8008)
│   │   │   ├─ read_server.py               # ファイル読込 MCP サーバ (:8005)
│   │   │   ├─ write_server.py              # ファイル書込 MCP サーバ (:8007)
│   │   │   ├─ delete_server.py             # ファイル削除 MCP サーバ (:8008)
│   │   │   ├─ read_service.py              # ファイル読込サービス
│   │   │   ├─ write_service.py             # ファイル書込サービス
│   │   │   ├─ delete_service.py            # ファイル削除サービス
│   │   │   ├─ read_tools.py                # ファイル読込ツール
│   │   │   ├─ write_tools.py               # ファイル書込ツール
│   │   │   ├─ delete_tools.py              # ファイル削除ツール
│   │   │   ├─ read_business.py             # ファイル読込ビジネスロジック
│   │   │   ├─ read_security.py             # ファイル読込セキュリティ
│   │   │   ├─ read_static_helpers.py       # ファイル読込静的ヘルパー
│   │   │   ├─ read_models.py               # ファイル読込データモデル
│   │   │   ├─ write_models.py              # ファイル書込データモデル
│   │   │   ├─ delete_models.py             # ファイル削除データモデル
│   │   │   ├─ write_formatter.py           # ファイル書込フォーマッタ
│   │   │   ├─ delete_formatter.py          # ファイル削除フォーマッタ
│   │   │   ├─ common.py                    # ファイル共通ユーティリティ
│   │   │   └─ __init__.py                  # ファイル MCP パッケージ初期化
│   │   ├─ github/                          # GitHub MCP サーバ (:8006)
│   │   │   ├─ server.py                    # GitHub MCP サーバ
│   │   │   ├─ server_common.py             # GitHub MCP サーバ共通
│   │   │   ├─ server_file.py               # GitHub ファイル操作
│   │   │   ├─ server_issues.py             # GitHub イシュー操作
│   │   │   ├─ server_pull_requests.py      # GitHub PR 操作
│   │   │   ├─ server_repository.py         # GitHub リポジトリ操作
│   │   │   ├─ service_business.py          # GitHub ビジネスロジックサービス
│   │   │   ├─ service_dispatch.py          # GitHub サービスディスパッチ
│   │   │   ├─ service_file.py              # GitHub ファイルサービス
│   │   │   ├─ service_issues.py            # GitHub イシューサービス
│   │   │   ├─ service_pull_requests.py     # GitHub PR サービス
│   │   │   ├─ service_repository.py        # GitHub リポジトリサービス
│   │   │   ├─ service_init.py              # GitHub サービス初期化
│   │   │   ├─ service_security.py          # GitHub セキュリティサービス
│   │   │   ├─ tools.py                     # GitHub ツール
│   │   │   ├─ tools_file.py                # GitHub ファイルツール
│   │   │   ├─ tools_issues.py              # GitHub イシューツール
│   │   │   ├─ tools_pull_requests.py       # GitHub PR ツール
│   │   │   ├─ tools_repository.py          # GitHub リポジトリツール
│   │   │   ├─ models.py                    # GitHub データモデル
│   │   │   ├─ models_base.py               # GitHub 基本データモデル
│   │   │   ├─ models_config.py             # GitHub 設定データモデル
│   │   │   ├─ models_file.py               # GitHub ファイルデータモデル
│   │   │   ├─ models_issues.py             # GitHub イシューデータモデル
│   │   │   ├─ models_pull_requests.py      # GitHub PR データモデル
│   │   │   ├─ models_repository.py         # GitHub リポジトリデータモデル
│   │   │   ├─ formatter.py                 # GitHub フォーマッタ
│   │   │   ├─ mapper.py                    # GitHub マッパー
│   │   │   ├─ exception_handlers.py        # GitHub 例外ハンドラ
│   │   │   └─ __init__.py                  # GitHub MCP パッケージ初期化
```

## Related Documents

- `01_overview-files-03-scripts-part1.md`
- `01_overview-files-03-scripts-part2.md`
- `01_overview-files-03-scripts-part3.md`
- `01_overview-files-03-scripts-part5.md`

## Keywords

scripts
agent
mcp-server
file-structure
