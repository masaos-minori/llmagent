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
---


# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:


``` text
│   ├─ mcp_servers/                           # MCP サーバパッケージ
│   │   └─ __init__.py                      # MCP パッケージ初期化
│   │   ├─ models.py                        # /v1/call_tool 統合エンドポイント共通 Pydantic モデル
│   │   ├─ server.py                        # MCP サーバ HTTP 起動共通基底クラス
│   │   ├─ audit.py                         # MCP ツール実行監査ログ (JSON-lines 1 行/実行)
│   │   ├─ dispatch.py                      # dispatch_tool(): DispatchResult を返すツールルーティングヘルパー
│   │   ├─ health_response.py               # make_health_response(): /health エンドポイント共通レスポンス生成
│   │   ├─ tool_validators.py               # @register_validator: git_commit / git_push / trigger_workflow / shell_run 等の入力バリデータ
│   │   ├─ web_search/                      # Web 検索 MCP サーバ (DuckDuckGo, :8004)
│   │   │   # 各サービス固有のファイル (例: web_search_server.py 等) は、
│   │   │   # mcp_servers/ の共有基盤の上に構築されています。詳細は
│   │   │   # scripts/mcp_servers/web_search/ を直接参照してください。
│   │   ├─ github/                          # GitHub MCP サーバ (:8006)
│   │   │   # 各ドメイン (file/issues/PR/repo) ごとの実装は、
│   │   │   # mcp_servers/ の共有基盤の上に構築されています。詳細は
│   │   │   # scripts/mcp_servers/github/ を直接参照してください。
```

## Related Documents

- `01_overview-files-03-scripts-part1.md`
- `01_overview-files-03-scripts-part2.md`
- `01_overview-files-03-scripts-part3.md`
- `01_overview-files-03-scripts-part5.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure
