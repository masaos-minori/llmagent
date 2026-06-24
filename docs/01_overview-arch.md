# 概要・アーキテクチャ

ファイル構成 → [`01_overview-files.md`](01_overview-files.md)

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
:8003 embed-LLM  :8001 agent-LLM   MCP サーバ群 (stdio または http)
(RAG 検索時)                       11 サーバ (:8004〜:8014)
```

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
| `sqlite-mcp` | 8011 | — | SQLite 読み取り専用クエリ MCP サーバ |
| `cicd-mcp` | 8012 | — | GitHub Actions CI/CD MCP サーバ |
| `mdq-mcp` | 8013 | — | Markdown Context Compression Engine MCP サーバ |
| `git-mcp` | 8014 | — | ローカル git 操作 MCP サーバ |

### 2.2 取込パイプライン

詳細 → [`03_rag_02_ingestion_pipeline.md`](03_rag_02_ingestion_pipeline.md)

```
target_urls → crawler.py (BFS クロール) → rag-src/*.txt
           → chunk_splitter.py (JA/EN/code 分割) → rag-src/chunk/*.txt
           → ingester.py (embed → SQLite INSERT) → rag-src/registered/
```

### 2.3 クエリパイプライン

詳細 → [`03_rag_03_query_pipeline.md`](03_rag_03_query_pipeline.md)

```
ユーザー入力
  → MQE + embed → KNN+BM25 → RRF → Rerank → Refiner → コンテキスト付加
  → LLM (:8001) → tool_calls → MCP サーバ群 (:8004〜:8014)
  → 最終回答 (SSE ストリーミング)
```

### 2.4 エージェント機能・コマンド一覧

詳細 → [`05_agent_07_cli-and-commands.md`](05_agent_07_cli-and-commands.md)

### 2.5 実装済み機能サマリ

| 機能 | 実装場所 |
|---|---|
| RAG 検索 (MQE + KNN + BM25 + RRF + Rerank + Refiner) | `scripts/rag/pipeline.py` |
| MCP ツールコーリング (HTTP/stdio, 11 サーバ) | `agent/tool_runner.py`, `shared/tool_executor.py` |
| メモリレイヤー (semantic/episodic) | `agent/memory/` |
| セッション永続化・復元 | `agent/session.py`, `db/` |
| コンテキスト圧縮 (LLM 要約) | `agent/history.py` |
| ツール結果 TTL キャッシュ | `shared/tool_cache.py`, `shared/tool_executor.py` |
| SSE ストリーミング | `shared/llm_client.py` |
| スラッシュコマンド群 | `agent/commands/` |

---
