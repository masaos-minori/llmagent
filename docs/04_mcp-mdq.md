# Markdown Context Compression Engine MCP Server (mdq-mcp)

## 1. Markdown Context Compression Engine MCP Server (mdq-mcp)

### 1.1 機能概要

Markdown Context Compression Engine MCP Server (mdq-mcp) は、Markdown文書のコンテキストを効率的に管理し、大規模なMarkdown文書を部分的に取得してLLMのコンテキストに注入できるようにするMCPサーバです。

> **注意:** サーバースキーマとツール定義は実装済みですが、サービス層 (`MdqService`) と検索ロジックはプレースホルダ実装です。本格的なFTS5検索・インデックス構築は今後の実装予定。

### 1.2 ツール一覧

| ツール名 | 説明 |
|---|---|
| `search_docs` | インデックスされたMarkdownセクションを検索する |
| `get_chunk` | Markdownチャンクをchunk_idで取得する |
| `outline` | Markdownファイルの見出し構造を取得する |
| `index_paths` | 対象のパスをインデックスする |
| `refresh_index` | 指定パスを再インデックスする |
| `stats` | インデックスの統計情報を取得する |
| `grep_docs` | Markdownチャンクを部分文字列マッチで検索する |

### 1.3 サービス構成ファイル

| ファイル | 配置先 | 説明 |
|---|---|---|
| `scripts/mcp/mdq/server.py` | `/opt/llm/scripts/mcp/mdq/server.py` | FastAPI + MCPServer 継承サーバ本体 (ポート 8013) |
| `scripts/mcp/mdq/service.py` | `/opt/llm/scripts/mcp/mdq/service.py` | mdqサービス層 (`MdqService`) — プレースホルダ実装 |
| `scripts/mcp/mdq/parser.py` | `/opt/llm/scripts/mcp/mdq/parser.py` | Markdownパーサー (`parse_markdown` 非同期関数) |
| `scripts/mcp/mdq/indexer.py` | `/opt/llm/scripts/mcp/mdq/indexer.py` | インデックス処理 (スタンドアロン非同期関数群) |
| `scripts/mcp/mdq/search.py` | `/opt/llm/scripts/mcp/mdq/search.py` | 検索ロジック (`search_docs` 非同期関数) |
| `scripts/mcp/mdq/models.py` | `/opt/llm/scripts/mcp/mdq/models.py` | Pydantic モデル定義 |
| `scripts/mcp/mdq/tools.py` | `/opt/llm/scripts/mcp/mdq/tools.py` | MCP ツールスキーマ (`_MCP_TOOLS`) |
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
# → {"status": "ok", "service": "mdq-mcp"}
```

### 1.5 使用方法

```bash
# agent.py REPL経由での利用
source /opt/llm/venv/bin/activate
python /opt/llm/scripts/agent.py
# agent[chat]> Markdownファイルの見出し構造を取得してください
# agent[chat]> /mcp status でmdq-mcpが表示されることを確認

# HTTP API直接呼び出し (POST /v1/call_tool)
curl -s -X POST http://127.0.0.1:8013/v1/call_tool \
  -H "Content-Type": "application/json" \
  -d '{"name": "outline", "args": {"path": "/path/to/file.md"}}' \
  | python3 -m json.tool
```

### 1.6 設定項目

| パラメータ | ファイル | デフォルト | 説明 |
|---|---|---|---|
| `db_path` | コードハードコード | `/opt/llm/db/mdq.db` | データベースパス (`MdqService.__init__()` で固定値) |

`search_docs` の検索件数上限は `SearchDocsRequest.limit` フィールド (デフォルト `10`) でリクエストごとに制御する。`SearchDocsRequest.mode` のデフォルト値は `"bm25"` (models.py 定義)。

### 1.7 実装方式

| 機能 | 実装 |
|---|---|
| フレームワーク | FastAPI + Uvicorn (ポート 8013) |
| 起動モード | HTTPモード (OpenRCサービス `mdq-mcp`)、stdioモード (`--stdio` フラグ) |
| ベースクラス | `mcp.server.MCPServer` を継承 |
| 責務分割 | `_DISPATCH_TABLE` でツール名 → ハンドラ非同期関数をマッピング |
| パーサー | `parse_markdown()` — ファイル内容を読み取り、現在はそのまま返す |
| インデクサー | `index_paths()`, `_index_single_file()`, `_index_directory()` — 現在プレースホルダ |
| 検索ロジック | `search_docs()` — 現在プレースホルダ (`"Search results for: {query}"` を返す) |

**実装ステータス:** ツールスキーマ、HTTPエンドポイント、MCPServer基底クラスは完成済み。ビジネスロジック層 (インデックス構築・FTS5検索・チャンク取得) はプレースホルダ実装のため、実際のデータ操作は行われません。

### 1.8 入出力インタフェース

**HTTP API エンドポイント**

| エンドポイント | メソッド | 説明 |
|---|---|---|
| `/v1/tools` | GET | ツールリスト `{tools: [{name, description}]}` |
| `/v1/call_tool` | POST | ツール実行 `{name, args} → {result, is_error}` |
| `/health` | GET | ヘルスチェック `{status: "ok", service: "mdq-mcp"}` |

**MCP ツール (tools/call 経由)**

| ツール名 | 引数 | 戻り値 (現在) | 戻り値 (予定) |
|---|---|---|---|
| `search_docs` | `{query, limit?, mode?, path_prefix?, tag_filter?, heading_prefix?}` | `"Search results for: {query}"` | JSON (`SearchDocsResponse.results`) |
| `get_chunk` | `{chunk_id, with_neighbors?}` | `"Retrieved chunk {chunk_id}"` | JSON (`GetChunkResponse.chunk, headings`) |
| `outline` | `{path}` | ファイル内容 (そのまま) | JSON (`OutlineResponse.headings`) |
| `index_paths` | `{paths}` | `"Indexing complete"` | JSON (`IndexPathsResponse.message`) |
| `refresh_index` | `{paths}` | `"Index refreshed"` | JSON (`RefreshIndexResponse.message`) |
| `stats` | `{}` | `"Stats retrieved"` | JSON (`StatsResponse.document_count, chunk_count, index_metadata`) |
| `grep_docs` | `{pattern, paths?}` | `"Grep results for pattern: {pattern}"` | JSON (`GrepDocsResponse.results`) |

### 1.9 エラーハンドリング

| HTTPステータス | 発生条件 |
|---|---|
| 500 | `MdqServiceError` 例外 (FastAPI exception handler) |

現在、入力検証やビジネスロジックのプレースホルダ実装のため、400/404 は未実装です。本実装時に追加予定。

### 1.10 ログ出力

- **ファイル:** `/opt/llm/logs/mdq-mcp.log` + 標準エラー出力
- **フォーマット:** 各モジュールの `logging.getLogger(__name__)` を使用

| レベル | タイミング |
|---|---|
| `INFO` | 検索・インデックス処理の開始 |
| `WARNING` | パス未存在、非Markdownファイルのスキップ |
| `ERROR` | サーバエラー |

### 1.11 クラス API

**`MdqMCPServer`** (`mcp/mdq/server.py:150-160`)

```python
from mcp.mdq.server import MdqMCPServer

MdqMCPServer().run_http()
```

| クラス属性 | 値 | 説明 |
|---|---|---|
| `server_name` | `"mdq-mcp"` | MCP `initialize` レスポンスのサーバ識別名 |
| `server_version` | `"1.0.0"` | バージョン文字列 |
| `http_port` | `8013` | HTTP モード待受ポート |
| `app_module` | `"mcp.mdq.server:app"` | uvicorn 起動ターゲット |
| `mcp_tools` | `_MCP_TOOLS` | `tools/list` に返すツール定義 (7種) |

| メソッド | 説明 |
|---|---|
| `dispatch(name, args)` | `_DISPATCH_TABLE[name]` 経由でサービス層に委譲。`(result_text, is_error)` を返す |

**`MdqService`** (`mcp/mdq/service.py:31-74`)

| メソッド | シグネチャ | 戻り値 | 備考 |
|---|---|---|---|
| `search_docs` | `async (req: SearchDocsRequest) -> str` | `"Search results for: {req.query}"` | プレースホルダ。本実装時は `search.search_docs()` に委譲予定 |
| `get_chunk` | `async (req: GetChunkRequest) -> str` | `"Retrieved chunk {req.chunk_id}"` | プレースホルダ |
| `outline` | `async (req: OutlineRequest) -> str` | ファイル内容 | `parser.parse_markdown()` に委譲。ファイル不在時は `FileNotFoundError` |
| `index_paths` | `async (req: IndexPathsRequest) -> str` | `"Indexing complete"` | `indexer.index_paths()` に委譲。ディレクトリ指定時は `.md` のみを再帰探索 |
| `refresh_index` | `async (req: RefreshIndexRequest) -> str` | `"Index refreshed"` | プレースホルダ |
| `stats` | `async (req: StatsRequest) -> str` | `"Stats retrieved"` | プレースホルダ |
| `grep_docs` | `async (req: GrepDocsRequest) -> str` | `"Grep results for pattern: {req.pattern}"` | プレースホルダ |

`MdqService.__init__()` は `self.db_path = "/opt/llm/db/mdq.db"` を設定し `_init_db()` を呼ぶ (現在何もしない)。

**スタンドアロン非同期関数** (`mcp/mdq/indexer.py`, `mcp/mdq/search.py`)

| 関数 | シグネチャ | 戻り値 | 備考 |
|---|---|---|---|
| `index_paths` | `async (service, req: IndexPathsRequest) -> str` | `"Indexing complete"` | `Path.is_file()` で `.md` をフィルタ、`Path.is_dir()` で再帰走査 |
| `_index_single_file` | `async (service, path: Path) -> None` | なし | プレースホルダ |
| `_index_directory` | `async (service, path: Path) -> None` | なし | `rglob("*.md")` で再帰走査 |
| `search_docs` | `async (service, req: SearchDocsRequest) -> str` | `"Search results for: {req.query}"` | プレースホルダ。本実装時は FTS5 検索予定 |

**Pydantic モデル** (`mcp/mdq/models.py`)

| モデル | フィールド |
|---|---|
| `SearchDocsRequest` | `query`, `limit=10`, `mode="bm25"`, `path_prefix?`, `tag_filter?`, `heading_prefix?` |
| `GetChunkRequest` | `chunk_id`, `with_neighbors=False` |
| `OutlineRequest` | `path` |
| `IndexPathsRequest` | `paths: list[str]` |
| `RefreshIndexRequest` | `paths: list[str]` |
| `StatsRequest` | (なし) |
| `GrepDocsRequest` | `pattern`, `paths?` |
| `ParseMarkdownRequest` | `path` |

レスポンスモデル: `SearchDocsResponse(results)`, `GetChunkResponse(chunk, headings)`, `OutlineResponse(headings)`, `IndexPathsResponse(message)`, `RefreshIndexResponse(message)`, `StatsResponse(document_count, chunk_count, index_metadata)`, `GrepDocsResponse(results)`

**HTTPエンドポイント `POST /v1/call_tool`**

```json
// リクエスト
{"name": "search_docs", "args": {"query": "LLMの設定方法"}}

// レスポンス (現在: プレースホルダ)
{"result": "Search results for: LLMの設定方法", "is_error": false}
```
