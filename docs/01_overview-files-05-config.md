---
title: "Configuration File Structure"
category: overview
tags:
  - configuration
  - toml
  - agent-toml
  - mcp-server-config
  - rag-config
  - file-structure
related:
  - 01_overview-files-01-build.md
  - 01_overview-files-02-rag.md
  - 01_overview-files-06-misc.md
  - 01_overview.md
---

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:

``` text
/opt/llm/
├─ config/
│   ├─ workflows/                           # ワークフロー定義ファイル群
│   │   └─ default.json                     # デフォルトワークフロー定義
│   ├─ agent.toml                           # エージェント全体設定 (DB パス・埋込 URL 含む)
│   ├─ crawler.toml                         # クローラ設定
│   ├─ chunk_splitter.toml                  # チャンク分割設定
│   ├─ ingester.toml                        # インジェスター設定
│   ├─ web_search_mcp_server.toml           # Web 検索 MCP サーバ設定 (:8004)
│   ├─ file_read_mcp_server.toml            # ファイル読込 MCP サーバ設定 (:8005, 許可ディレクトリ)
│   ├─ github_mcp_server.toml               # GitHub MCP サーバ設定 (:8006)
│   ├─ file_write_mcp_server.toml           # ファイル書込 MCP サーバ設定 (:8007)
│   ├─ file_delete_mcp_server.toml          # ファイル削除 MCP サーバ設定 (:8008)
│   ├─ shell_mcp_server.toml                # シェル MCP サーバ設定 (:8009, 許可コマンド)
│   ├─ rag_pipeline_mcp_server.toml         # RAG パイプライン MCP サーバ設定 (:8010)
│   ├─ cicd_mcp_server.toml                 # CI/CD MCP サーバ設定 (:8012)
│   ├─ mdq_mcp_server.toml                  # MDQ MCP サーバ設定 (:8013)
│   ├─ git_mcp_server.toml                  # Git MCP サーバ設定 (:8014)
│   └─ eventbus.toml                        # Event Bus サーバ設定 (:8015)
```

## Related Documents

- `01_overview-files-01-build.md`
- `01_overview-files-02-rag.md`
- `01_overview-files-03-scripts-part1.md`
- `01_overview-files-04-shared-part1.md`
- `01_overview-files-06-misc.md`

## Keywords

configuration
toml
agent-toml
mcp-server-config
rag-config
file-structure
