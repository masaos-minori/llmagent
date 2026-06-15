# 概要・アーキテクチャ

ファイル構成 → [`01_overview-files.md`](01_overview-files.md)

## 1. 概要・目的

CPU 専用のローカル環境 (Intel N100 / 16 GB RAM) に llama.cpp を用いた LLM サーバ群と SQLite ベースのベクトル DB を構築し、日本語・英語双方に対応した高精度 RAG システムを実現。

### 1.1 前提条件

| 項目 | 値 |
|---|---|
| OS | Gentoo Linux or Ubuntu Linux |
| 用途 | コーディング補助・日本語チャット |

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
:8003 embed-LLM  :8001 code-LLM    MCP サーバ群 (stdio または http)
(RAG 検索時)     :8002 chat-LLM    11 サーバ (:8004〜:8014)
```

| OpenRC サービス | ポート | モデル | 役割 |
|---|---|---|---|
| `embed-llm` | 8003 | multilingual-E5-small | テキスト → 384 次元ベクトル変換 |
| `llama-chat-llm` | 8002 | gemma-4-e4b | 日本語チャット・MQE・再ランク |
| `llama-coding-llm` | 8001 | qwen2.5-coder-7b | コード生成 |
| `web-search-mcp` | 8004 | — | Web 検索 MCP サーバ (Brave/Bing/DuckDuckGo) |
| `file-read-mcp` | 8005 | — | ファイル読み取り MCP サーバ |
| `github-mcp` | 8006 | — | GitHub 操作 MCP サーバ |
| `file-write-mcp` | 8007 | — | ファイル書き込み MCP サーバ |
| `file-delete-mcp` | 8008 | — | ファイル削除 MCP サーバ |
| `shell-mcp` | 8009 | — | シェルコマンド実行 MCP サーバ |
| `rag-pipeline-mcp` | 8010 | — | RAG パイプライン MCP サーバ |
| `sqlite-mcp` | 8011 | — | SQLite 読み取り専用クエリ MCP サーバ |
| `cicd-mcp` | 8012 | — | GitHub Actions CI/CD MCP サーバ |
| `mdq-mcp` | 8013 | — | Markdown Context Compression Engine MCP サーバ |
| `git-mcp` | 8014 | — | ローカル git 操作 MCP サーバ |

### 2.2 取込パイプライン

詳細 → [`03_rag-ingestion-pipeline.md`](03_rag-ingestion-pipeline.md)

```
target_urls → crawler.py (BFS クロール) → rag-src/*.txt
           → chunk_splitter.py (JA/EN/code 分割) → rag-src/chunk/*.txt
           → ingester.py (embed → SQLite INSERT) → rag-src/registered/
```

### 2.3 クエリパイプライン

詳細 → [`05_agent.md`](05_agent.md)

```
ユーザー入力
  → MQE + embed → KNN+BM25 → RRF → Rerank → コンテキスト付加
  → LLM (:8001/:8002) → tool_calls → MCP サーバ群 (:8004〜:8014)
  → 最終回答 (SSE ストリーミング)
```

### 2.4 エージェント機能・コマンド一覧

詳細 → [`05_agent.md`](05_agent.md)

### 2.5 実装済み機能サマリ

| 機能 | 実装場所 |
|---|---|
| RAG 検索 (MQE + KNN + BM25 + RRF + Rerank) | `rag/pipeline.py` |
| MCP ツールコーリング (HTTP/stdio, 11 サーバ) | `agent/tool_runner.py`, `shared/tool_executor.py` |
| メモリレイヤー (semantic/episodic) | `agent/memory/` |
| セッション永続化・復元 | `agent/session.py`, `db/` |
| コンテキスト圧縮 (LLM 要約) | `agent/history.py` |
| ツール結果 TTL キャッシュ | `shared/tool_cache.py`, `shared/tool_executor.py` |
| SSE ストリーミング | `shared/llm_client.py` |
| スラッシュコマンド群 | `agent/commands/` |

詳細 → [`05_agent.md`](05_agent.md)

---
