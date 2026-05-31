# Markdown Context Compression Engine MCP Server (mdq-mcp)

## 1. Markdown Context Compression Engine MCP Server (mdq-mcp)

### 1.1 機能概要

Markdown Context Compression Engine MCP Server (mdq-mcp) は、Markdown文書のコンテキストを効率的に管理し、大規模なMarkdown文書を部分的に取得してLLMのコンテキストに注入できるようにするMCPサーバです。

### 1.2 ツール一覧

| ツール名 | 説明 |
|---|---|
| `search_docs` | インデックスされたMarkdownセクションを検索する |
| `get_chunk` | Markdownチャンクをchunk_idで取得する |
| `outline` | Markdownファイルの見出し構造を取得する |
| `index_paths` | 対象のパスをインデックスする |
| `refresh_index` | インクリメンタル更新のみを再インデックスする |
| `stats` | インデックスの統計情報を取得する |
| `grep_docs` | Markdownチャンクを正規表現で検索する |

### 1.3 サービス構成ファイル

| ファイル | 配置先 | 説明 |
|---|---|---|
| `scripts/mcp/mdq/server.py` | `/opt/llm/scripts/mcp/mdq/server.py` | mdq MCPサーバ本体 |
| `scripts/mcp/mdq/service.py` | `/opt/llm/scripts/mcp/mdq/service.py` | mdqサービス層 |
| `scripts/mcp/mdq/parser.py` | `/opt/llm/scripts/mcp/mdq/parser.py` | Markdownパーサー |
| `scripts/mcp/mdq/indexer.py` | `/opt/llm/scripts/mcp/mdq/indexer.py` | インデクサー |
| `scripts/mcp/mdq/search.py` | `/opt/llm/scripts/mcp/mdq/search.py` | 検索ロジック |
| `config/mdq_mcp_server.toml` | `/opt/llm/config/mdq_mcp_server.toml` | 設定ファイル |
| `init.d/mdq-mcp` | `/etc/init.d/mdq-mcp` | OpenRC起動スクリプト |

### 1.4 インストール

```bash
# 1. スクリプトと設定ファイルを配置する
cp scripts/mcp/mdq/*.py /opt/llm/scripts/mcp/mdq/
cp config/mdq_mcp_server.toml /opt/llm/config/
cp init.d/mdq-mcp /etc/init.d/mdq-mcp
chmod +x /etc/init.d/mdq-mcp

# 2. OpenRCサービスを登録して起動する
rc-update add mdq-mcp default
rc-service mdq-mcp start

# 3. 動作確認
curl -s http://127.0.0.1:8013/health
# → {"status": "ok"}
```

### 1.5 使用方法

```bash
# agent.py REPL経由での利用
source /opt/llm/venv/bin/activate
python /opt/llm/scripts/agent.py
# agent[chat]> Markdownファイルの見出し構造を取得してください
# agent[chat]> /mcp status でmdq-mcpが表示されることを確認

# HTTP API直接呼び出し
curl -s -X POST http://127.0.0.1:8013/search_docs \
  -H "Content-Type: application/json" \
  -d '{"query": "LLMの設定方法"}' \
  | python3 -m json.tool
```

### 1.6 設定項目

| パラメータ | ファイル | デフォルト | 説明 |
|---|---|---|---|
| `db_path` | `config/mdq_mcp_server.toml` | `/opt/llm/db/mdq.sqlite` | データベースパス |
| `max_search_results` | `config/mdq_mcp_server.toml` | `100` | 検索結果の最大件数 |
| `max_snippet_chars` | `config/mdq_mcp_server.toml` | `500` | スニペットの最大文字数 |
| `max_chunk_chars` | `config/mdq_mcp_server.toml` | `10000` | チャンクの最大文字数 |
| `max_file_chars` | `config/mdq_mcp_server.toml` | `100000` | ファイルの最大文字数 |

### 1.7 実装方式

| 機能 | 実装 |
|---|---|
| フレームワーク | FastAPI + Uvicorn (ポート 8013) |
| 起動モード | HTTPモード (OpenRCサービス `mdq-mcp`) |
| 責務分割 | `MdqService` がビジネスロジックを担当し、`Indexer` がインデックス処理を担当 |
| パーサー | `Markdown` ライブラリを使用した見出しベースの解析 |
| インデクサー | SQLiteを使用したインデックス構築 |
| 検索 | FTS5を使用したBM25検索とgrep検索を組み合わせたハイブリッド検索 |

### 1.8 入出力インタフェース

**HTTP API** (ツールの入出力インタフェースを参照)

主要なリクエスト/レスポンス:

| ツール | リクエスト | レスポンス |
|---|---|---|
| `search_docs` | `{query: str, limit?: int, mode?: str, path_prefix?: str, tag_filter?: [str], heading_prefix?: str}` | `{hits: [SearchDocsHit], total_hits: int}` |
| `get_chunk` | `{chunk_id: int, with_neighbors?: bool}` | `{chunk_id: int, source_path: str, heading_path: str, content: str, token_count: int, tags: [str], chunk_order: int}` |
| `outline` | `{path: str}` | `{path: str, title: str, outline: [OutlineEntry]}` |
| `index_paths` | `{paths: [str]}` | `{indexed_paths: [str], total_docs: int}` |
| `refresh_index` | `{paths: [str]}` | `{updated_paths: [str], total_docs: int}` |
| `stats` | `{}` | `{document_count: int, chunk_count: int, latest_update: str, fts_size: int}` |
| `grep_docs` | `{pattern: str, paths?: [str]}` | `{pattern: str, matches: [dict], truncated: bool}` |

### 1.9 エラーハンドリング

| HTTPステータス | 発生条件 |
|---|---|
| 400 | 無効なリクエストパラメータ |
| 404 | ファイルまたはチャンクが存在しない |
| 500 | サーバ内部エラー |

### 1.10 ログ出力

- **ファイル:** `/opt/llm/logs/mdq-mcp.log` + 標準エラー出力
- **フォーマット:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング |
|---|---|
| `INFO` | 各操作のパス・バイト数・件数 |
| `WARNING` | インデックス更新時の警告 |
| `ERROR` | サーバエラー |

### 1.11 クラス API

`MdqMCPServer` は `MCPServer` を継承し、HTTPモード起動ロジックを提供する。`MCPServer` 共通 API は `docs/06_ref-mcp.md` §2 を参照。

| クラス | ファイル | `server_name` | `http_port` | `mcp_tools` |
|---|---|---|---|---|
| `MdqMCPServer` | `scripts/mcp/mdq/server.py` | `"mdq-mcp"` | 8013 | 7 種 |

各サーバの `dispatch(name, args) -> tuple[str, bool]` は、内部の `_dispatch_*_tool()` テーブルでツール名を解決し `(result_text, is_error)` を返す。

**HTTPエンドポイント `POST /v1/call_tool`**

```json
// リクエスト
{"name": "search_docs", "args": {"query": "LLMの設定方法"}}

// レスポンス
{"result": "{\"hits\": [...], \"total_hits\": 5}", "is_error": false}
```