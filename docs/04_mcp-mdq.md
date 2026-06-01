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
| `refresh_index` | 指定パスを再インデックスする (内部では `index_paths` と同等の処理) |
| `stats` | インデックスの統計情報を取得する |
| `grep_docs` | Markdownチャンクを部分文字列マッチで検索する |

### 1.3 サービス構成ファイル

| ファイル | 配置先 | 説明 |
|---|---|---|
| `scripts/mcp/mdq/service.py` | `/opt/llm/scripts/mcp/mdq/service.py` | mdqサービス層 (`MdqService`) |
| `scripts/mcp/mdq/parser.py` | `/opt/llm/scripts/mcp/mdq/parser.py` | Markdownパーサー |
| `scripts/mcp/mdq/indexer.py` | `/opt/llm/scripts/mcp/mdq/indexer.py` | インデクサー (`Indexer`) |
| `scripts/mcp/mdq/search.py` | `/opt/llm/scripts/mcp/mdq/search.py` | 検索ロジック (`search_chunks`) |
| `scripts/mcp/mdq/models.py` | `/opt/llm/scripts/mcp/mdq/models.py` | Pydantic モデル定義 |
| `config/mdq_mcp_server.toml` | `/opt/llm/config/mdq_mcp_server.toml` | 設定ファイル |
| `init.d/mdq-mcp` | `/etc/init.d/mdq-mcp` | OpenRC起動スクリプト |

> **注意:** `mcp/mdq/server.py` は現時点で未実装。HTTP サーバとして公開する場合は `MCPServer` サブクラスを実装してポート 8013 で起動すること。

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

`db_path` は `Indexer.__init__()` および `search_chunks()` が `shared.config_loader.get_config("mdq_mcp_server")` 経由で読み込む。`search_docs` の検索件数上限は `SearchDocsRequest.limit` フィールド (デフォルト `10`) でリクエストごとに制御する。

### 1.7 実装方式

| 機能 | 実装 |
|---|---|
| フレームワーク | FastAPI + Uvicorn (ポート 8013) |
| 起動モード | HTTPモード (OpenRCサービス `mdq-mcp`) |
| 責務分割 | `MdqService` がビジネスロジックを担当し、`Indexer` がインデックス処理を担当 |
| パーサー | `Markdown` ライブラリを使用した見出しベースの解析 |
| インデクサー | SQLiteを使用したインデックス構築 |
| 検索モード | `mode="bm25"`: FTS5 (BM25ランク順) / `mode="grep"`: content の LIKE 検索 / `mode="hybrid"` (デフォルト): BM25+grep の結果をマージして重複除去 |

### 1.8 入出力インタフェース

**HTTP API** (ツールの入出力インタフェースを参照)

主要なリクエスト/レスポンス:

| ツール | リクエスト | レスポンス |
|---|---|---|
| `search_docs` | `{query: str, limit?: int=10, mode?: str="hybrid", path_prefix?: str, tag_filter?: [str], heading_prefix?: str}` | `{hits: [SearchDocsHit], total_hits: int}` (SearchDocsHit: `{chunk_id, source_path, heading_path, score: float, snippet: str, token_count, tags}`) |
| `get_chunk` | `{chunk_id: int, with_neighbors?: bool=false}` | `{chunk_id: int, source_path: str, heading_path: str, content: str, token_count: int, tags: [str], chunk_order: int}` |
| `outline` | `{path: str}` | `{path: str, title: str, outline: [OutlineEntry]}` |
| `index_paths` | `{paths: [str]}` | `{indexed_paths: [str], total_docs: int}` |
| `refresh_index` | `{paths: [str]}` | `{updated_paths: [str], total_docs: int}` |
| `stats` | `{}` | `{document_count: int, chunk_count: int, latest_update: str, fts_size: int}` |
| `grep_docs` | `{pattern: str, paths?: [str]}` | `{pattern: str, matches: [{chunk_id: int, source_path: str, heading_path: str, content: str}], truncated: bool}` |

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

> **注意:** `mcp/mdq/server.py` は現時点で未実装のため、`MdqMCPServer` クラスは存在しない。サービス層 (`MdqService`) および検索ロジック (`search_chunks`) は実装済み。HTTP サーバを実装する場合は `MCPServer` を継承し `server_name="mdq-mcp"` / `http_port=8013` を設定すること。

**`MdqService` メソッド一覧** (`mcp/mdq/service.py`)

| メソッド | シグネチャ | 戻り値 | 備考 |
|---|---|---|---|
| `search_docs` | `async (request: SearchDocsRequest) -> str` | JSON文字列 (`SearchDocsResponse`) | `search_chunks()` 委譲 |
| `get_chunk` | `async (request: GetChunkRequest) -> str` | JSON文字列 (`ChunkResponse`) | `with_neighbors` は受け取るが現在未使用; 常に単一チャンクを返す |
| `outline` | `async (request: OutlineRequest) -> str` | JSON文字列 (`OutlineResponse`) | ファイル不在時 HTTP 404 |
| `index_paths` | `async (request: IndexPathsRequest) -> str` | JSON文字列 (`IndexPathsResponse`) | ディレクトリ指定時は `.md`/`.markdown`/`.mdx` を再帰探索 |
| `refresh_index` | `async (request: RefreshIndexRequest) -> str` | JSON文字列 (`RefreshIndexResponse`) | 内部で `Indexer.refresh_paths()` を呼ぶ; 差分判定は `mtime`+`doc_hash` |
| `stats` | `async (request: StatsRequest) -> str` | JSON文字列 (`StatsResponse`) | `md_documents` / `md_chunks` / `md_chunks_fts` 行数を集計 |
| `grep_docs` | `async (request: GrepDocsRequest) -> str` | JSON文字列 (`GrepDocsResponse`) | `Indexer.grep_chunks()` 委譲; `truncated` は常に `false` |

`MdqService.__init__()` は `Indexer()` を生成し `self._db_path` に `indexer.db_path` を保持する。全メソッドは `orjson` でシリアライズした JSON 文字列を返す (`_dump()` ヘルパー経由)。

**`Indexer` メソッド一覧** (`mcp/mdq/indexer.py`)

| メソッド | シグネチャ | 戻り値 | 備考 |
|---|---|---|---|
| `index_paths` | `(paths: list[str]) -> list[str]` | インデックスしたファイルパスのリスト | ディレクトリ内は再帰走査 |
| `refresh_paths` | `(paths: list[str]) -> list[str]` | 更新されたファイルパスのリスト | 現実装は `index_paths` と同等 |
| `get_chunk` | `(chunk_id: int) -> dict \| None` | チャンク辞書またはNone | `md_chunks` をIDで1行取得 |
| `get_stats` | `() -> dict` | `{document_count, chunk_count, latest_update, fts_size}` | `latest_update` は `md_documents.updated_at` の最大値; 未更新時は `"Never"` |
| `grep_chunks` | `(pattern: str, paths: list[str] \| None = None) -> list[dict]` | `[{chunk_id, source_path, heading_path, content}]` のリスト | `pattern` は部分文字列マッチ (`in` 演算子); 正規表現ではない |

**`search_chunks()` 関数** (`mcp/mdq/search.py`)

```python
def search_chunks(
    query: str,
    limit: int | None = 10,
    mode: str | None = "hybrid",
    path_prefix: str | None = None,
    tag_filter: list[str] | None = None,
    heading_prefix: str | None = None,
) -> list[dict]:
```

戻り値の各要素: `{chunk_id: int, source_path: str, heading_path: str, score: float, snippet: str, token_count: int, tags: list[str]}`

- `mode="bm25"`: `md_chunks_fts MATCH ?` でFTS5 BM25ランク順
- `mode="grep"`: `content LIKE ?` で部分文字列検索; `score` は常に `0.0`
- `mode="hybrid"`: BM25 と grep を `limit*2` ずつ取得し `chunk_id` で重複除去後 `limit` 件に切り詰め

`_apply_filters()` が付加するフィルタ種別:

| パラメータ | SQL フィルタ | 備考 |
|---|---|---|
| `path_prefix` | `d.source_path LIKE '{prefix}%'` | ドキュメントパスのプレフィックス一致 |
| `heading_prefix` | `c.heading_path LIKE '{prefix}%'` | 見出しパスのプレフィックス一致 |
| `tag_filter` | `c.tags LIKE '%{tag}%'` (各タグの OR 条件) | タグの部分文字列一致 (JSON 配列を文字列として照合)

**HTTPエンドポイント `POST /v1/call_tool`**

```json
// リクエスト
{"name": "search_docs", "args": {"query": "LLMの設定方法"}}

// レスポンス
{"result": "{\"hits\": [...], \"total_hits\": 5}", "is_error": false}
```