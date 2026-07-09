---
title: "ファイル構成（ビルド・モデル・ランタイム）"
category: overview
tags:
  - overview
  - file-structure
related:
  - 01_overview.md
  - 01_overview-arch-process.md
source:
  - 01_overview-files.md
---

├─ llama.cpp/                                 # llama.cpp ソース・ビルド成果物
├─ models/
│   ├─ Qwen3.6-Instruct-Q4_K_M.gguf           # チャット/コード生成用 LLM (MQE・再ランク兼用, :8001)
│   └─ multilingual-E5-small.gguf             # 埋込用 LLM (384 次元, :8003)

├─ models/
│   ├─ Qwen3.6-Instruct-Q4_K_M.gguf           # チャット/コード生成用 LLM (MQE・再ランク兼用, :8001)
│   └─ multilingual-E5-small.gguf             # 埋込用 LLM (384 次元, :8003)
├─ rag-src/                           # クロール済みテキスト (yyyymmddhhmmss-{slug}.json)
│   ├─ chunk/                         # チャンク分割済みファイル ({stem}-{idx:04d}.json)
│   └─ registered/                    # DB 投入済みファイル (ingester.py が移動)

├─ sqlite-vec/
│   └─ vec0.so                        # SQLite ベクトル検索拡張 (ロード可能拡張モジュール)
├─ venv/                              # Python 仮想環境
│   └─ requirements.txt              # Python 依存パッケージ一覧

├─ venv/                              # Python 仮想環境
│   └─ requirements.txt              # Python 依存パッケージ一覧
├─ config/
│   ├─ workflows/                           # ワークフロー定義ファイル群
│   │   └─ default.json                     # デフォルトワークフロー定義
│   ├─ agent.toml                          # 共通設定 (DB パス・埋込 URL)
│   ├─ agent.toml                           # エージェント全体設定
│   ├─ rag_pipeline.toml                    # 取込パイプライン全体設定 (対象 URL・チャンクサイズ・ストップワード)
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

   └─ logs/                                    # 各サービスのログファイル出力先
/etc/conf.d/
   └─ github-mcp                         # GITHUB_TOKEN (Personal Access Token) 設定
```


/etc/conf.d/
   └─ github-mcp                         # GITHUB_TOKEN (Personal Access Token) 設定
```
## Related Documents

- `01_overview.md`
- `01_overview-arch-process.md`

## Keywords

file-structure
directory
layout
configuration
scripts
shared
database
event-bus
