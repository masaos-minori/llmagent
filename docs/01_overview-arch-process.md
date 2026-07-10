---
title: "Process Architecture"
category: overview
tags:
  - process-architecture
  - system-overview
  - architecture
  - process-model
  - agent
  - mcp-server
  - llm-service
related:
  - 01_overview-arch-pipelines.md
  - 01_overview-arch-features.md
  - 01_overview.md
source:
  - 01_overview-arch.md
---

# 概要・アーキテクチャ

ファイル構成 → [`01_overview-files-build.md`](01_overview-files-build.md), [`01_overview-files-rag.md`](01_overview-files-rag.md), [`01_overview-files-scripts.md`](01_overview-files-scripts.md), [`01_overview-files-shared.md`](01_overview-files-shared.md), [`01_overview-files-config.md`](01_overview-files-config.md), [`01_overview-files-misc.md`](01_overview-files-misc.md)

## 1. 概要・目的

エージェント + MCP サーバによるマルチエージェントオーケストレーションシステムの構築
- llama.cpp を用いた LLM サーバ群
- 単一責務ツール実行 MCP サーバ群
- 日本語・英語双方に対応した LLM エージェント
- SQLite ベースのベクトル DB による RAG 環境
- 対象 OS は Gentoo Linux or Ubuntu Linux
- 用途はプログラム開発

## 2. アーキテクチャ

### 2.1 プロセス構成

```
ユーザー
    │ 対話入力 (agent[chat]> / agent[code]> プロンプト)
    ▼
┌──────────────────────────────────────────────────────┐
│  agent.py (CLI REPL ツール)                           │
│  入力 → RAG 検索 → LLM 呼出 → MCP ツール実行 → 回答  │
└───────┬─────────────┬──────────────────┬─────────────┘
        │             │                  │
        ▼             ▼                  ▼
:8003 embed-LLM  :8001 agent-LLM   MCP サーバ群 (http)
(RAG 検索時)                       11 サーバ (:8004〜:8014)
```

#### 実装上の補足

- エントリポイントは `scripts/agent/__main__.py` であり、`python -m agent` で起動する。図中の `agent.py` はこのモジュールエントリを指す。(根拠: `__main__.py` の docstring)
- MCP サーバのトランスポートは設定上 `http` / `stdio` の両方が定義可能だが、現在の実装では `ToolExecutor` が HTTP POST `/v1/call_tool` を使用する。(根拠: `shared/tool_executor.py` の `HttpTransport`, stdio トランスポートは削除済み)
- 起動シーケンス (MCP サーバ起動・ヘルスチェック・セキュリティ監査・プロンプトセットアップ) は `agent/startup.py` の `StartupOrchestrator` に分離されており、`AgentREPL.run()` から委譲される。(根拠: `agent/startup.py`)

#### 設定ファイル分離方針

各プロセス (エージェント・各 MCP サーバー・crawler・ingester・chunk_splitter) は独立して動作し、**自身に対応する設定ファイル 1 つのみを読み込む**。他プロセスの設定ファイル (`agent.toml` を含む) は読み込まない。DB パス・外部サービス URL などが複数プロセスで必要な場合は共通ファイルを作らず、各プロセスの設定ファイルに個別に記述する。

| プロセス | 設定ファイル |
|---|---|
| agent | `config/agent.toml` |
| 各 MCP サーバー | `config/<key>_mcp_server.toml` |
| crawler | `config/crawler.toml` |
| ingester | `config/ingester.toml` |
| chunk_splitter | `config/chunk_splitter.toml` |

詳細 → [90_shared_03 §2a](90_shared_03_runtime_and_execution.md#2a-プロセス分離方針-config-isolation-policy)

| サービス | ポート | モデル | 役割 |
|---|---|---|---|
| `agent-llm` | 8001 | Qwen3.6-Instruct-Q4_K_M | チャット/コード生成 LLM (MQE・再ランク兼用) |
| `embed-llm` | 8003 | multilingual-E5-small | テキスト → 384 次元ベクトル変換 |
| `web-search-mcp` | 8004 | — | Web 検索 MCP サーバ (DuckDuckGo) |
| `file-read-mcp` | 8005 | — | ファイル読み取り MCP サーバ |
| `github-mcp` | 8006 | — | GitHub 操作 MCP サーバ |
| `file-write-mcp` | 8007 | — | ファイル書き込み MCP サーバ |
| `file-delete-mcp` | 8008 | — | ファイル削除 MCP サーバ |
| `shell-mcp` | 8009 | — | シェルコマンド実行 MCP サーバ |
| `rag-pipeline-mcp` | 8010 | — | RAG パイプライン MCP サーバ |
| `cicd-mcp` | 8012 | — | GitHub Actions CI/CD MCP サーバ |
| `mdq-mcp` | 8013 | — | Markdown Context Compression Engine MCP サーバ |
| `git-mcp` | 8014 | — | ローカル git 操作 MCP サーバ |

## Keywords

process-architecture
system-overview
agent
mcp-server
llm-service
configuration-isolation
