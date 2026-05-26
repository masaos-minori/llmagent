# ローカルファイル操作 MCP サーバ (file-mcp)

## 1. ローカルファイル操作 MCP サーバ (file-mcp)

### 1.1 機能概要

`fileop_mcp_server.py` は `/opt/llm` 配下のファイルシステムを操作する MCP 互換サーバ。@modelcontextprotocol/server-filesystem 準拠のツール名を採用する。HTTP モード (ポート 8005) で動作する。

| 起動モード | 利用元 | 提供機能 |
|---|---|---|
| HTTP モード (ポート 8005) | `agent_repl.py` (HTTP モード) | 18 エンドポイント (全 HTTP API) |

HTTP モードで公開する MCP ツールは HTTP の操作エンドポイント (POST) と対応する。`/list_allowed_directories` と `/health` は MCP ツールとして公開されない。

パストラバーサル攻撃 (`../` を使って許可ディレクトリ外にアクセスする攻撃) を防ぐため、`ALLOWED_DIRS` で許可するベースディレクトリを明示的に管理。パスは `Path.resolve()` でシンボリックリンクと `../` を解決してから境界チェック。

| エンドポイント | メソッド | 説明 |
|---|---|---|
| `/list_directory` | POST | ディレクトリの直下エントリ一覧を返す (ディレクトリサイズ=0) |
| `/list_directory_with_sizes` | POST | サイズ付きのディレクトリ一覧を返す (ディレクトリも stat サイズ) |
| `/directory_tree` | POST | ディレクトリの再帰ツリー構造を返す |
| `/read_text_file` | POST | ファイルを UTF-8 テキストとして読み込む (head/tail オプション) |
| `/read_media_file` | POST | 画像/音声などのメディアファイルを base64 で取得する |
| `/read_multiple_files` | POST | 複数ファイルを一括取得する |
| `/write_file` | POST | ファイルを新規作成または上書きする |
| `/edit_file` | POST | 文字列置換による差分編集を行う |
| `/create_directory` | POST | ディレクトリを作成する (親ディレクトリも自動作成) |
| `/move_file` | POST | ファイル/ディレクトリを移動またはリネームする |
| `/search_files` | POST | glob パターンでファイル名を検索する |
| `/grep_files` | POST | 正規表現パターンでファイル内容を検索する |
| `/delete_file` | POST | ファイルを削除する |
| `/delete_directory` | POST | ディレクトリを削除する (`recursive` オプションあり) |
| `/get_file_info` | POST | ファイルのメタデータを取得する |
| `/list_allowed_directories` | GET | アクセス許可ディレクトリ一覧を返す |
| `/health` | GET | ヘルスチェック |
| `/v1/call_tool` | POST | ツール名と引数を受け取り、フォーマット済みテキスト結果を返す (HTTP トランスポートモード用) |
| `/v1/tools` | GET | ツール名と説明一覧を返す (エージェント起動時のツール定義検証用) |

### 1.2 サービス構成ファイル

| ファイル | 配置先 | 説明 |
|---|---|---|
| `scripts/fileop_mcp_server.py` | `/opt/llm/scripts/fileop_mcp_server.py` | ファイル操作 MCP サーバ本体 |
| `config/fileop_mcp_server.json` | `/opt/llm/config/fileop_mcp_server.json` | アクセス許可ディレクトリ・サイズ上限設定 |
| `init.d/file-mcp` | `/etc/init.d/file-mcp` | OpenRC 起動スクリプト |

### 1.3 インストール

```bash
# 1. スクリプトと設定ファイルを配置する (追加ライブラリ不要: FastAPI/uvicorn は既存 venv に含まれる)
cp scripts/fileop_mcp_server.py /opt/llm/scripts/
cp config/fileop_mcp_server.json /opt/llm/config/

# 2. OpenRC スクリプトを配置して有効化する
cp init.d/file-mcp /etc/init.d/file-mcp
chmod +x /etc/init.d/file-mcp
rc-update add file-mcp default

# 3. サービスを起動する
rc-service file-mcp start

# 4. 動作確認
curl -s http://127.0.0.1:8005/health
# → {"status": "ok"}

curl -s -X POST http://127.0.0.1:8005/list_directory \
  -H "Content-Type: application/json" \
  -d '{"path": "/opt/llm/scripts"}' \
  | python3 -m json.tool

curl -s -X POST http://127.0.0.1:8005/read_text_file \
  -H "Content-Type: application/json" \
  -d '{"path": "/opt/llm/scripts/agent.py", "head": 30}' \
  | python3 -m json.tool
```

### 1.4 使用方法

```bash
# agent.py REPL 経由での利用 (LLM が自律的にファイルツールを選択する)
source /opt/llm/venv/bin/activate
python /opt/llm/scripts/agent.py
# agent[chat]> /opt/llm/scripts の Python ファイル一覧を教えてください

# HTTP API 直接呼び出し
curl -s -X POST http://127.0.0.1:8005/list_directory \
  -H "Content-Type: application/json" \
  -d '{"path": "/opt/llm/scripts"}' \
  | python3 -m json.tool
# → {"entries": [{"name": "agent.py", "type": "file", "size": 12345}, ...]}

curl -s -X POST http://127.0.0.1:8005/grep_files \
  -H "Content-Type: application/json" \
  -d '{"path": "/opt/llm/scripts", "pattern": "def \\w+", "file_pattern": "*.py"}' \
  | python3 -m json.tool
# → {"pattern": "...", "matches": [{"file": "...", "line_number": 1, "line": "..."}], "truncated": false}
```

### 1.5 設定項目

| パラメータ | ファイル | デフォルト | 説明 |
|---|---|---|---|
| `allowed_dirs` | `config/fileop_mcp_server.json` | `["/opt/llm"]` | アクセス許可するベースディレクトリ |
| `max_read_bytes` | `config/fileop_mcp_server.json` | 1,000,000 | 読み込みサイズ上限 (1 MB) |
| `max_write_bytes` | `config/fileop_mcp_server.json` | 1,000,000 | 書き込みサイズ上限 (1 MB、UTF-8 バイト数で判定) |
| `max_tree_depth` | `config/fileop_mcp_server.json` | 5 | `/directory_tree` の再帰深さ上限 |
| `max_search_results` | `config/fileop_mcp_server.json` | 200 | `/search_files` の返却件数上限 |

### 1.6 実装方式

| 機能 | 実装 |
|---|---|
| フレームワーク | FastAPI + Uvicorn (ポート 8005) |
| 起動モード | HTTP モード (ポート 8005、OpenRC サービス `file-mcp`) |
| 責務集約 | `FileService` クラスがすべてのファイル操作・セキュリティ検査を担う。FastAPI エンドポイントと `_fdisp_*` ハンドラはどちらも `_service` シングルトン (遅延初期化プロキシ) に委譲し、整形・変換のみを行う |
| パス境界チェック | `FileService._resolve_safe()` で `Path.resolve()` によるシンボリックリンク・`../` 解決後に許可ディレクトリリストと照合 |
| 差分編集 | `difflib.unified_diff` で unified diff 形式の差分を生成 |
| 書き込みサイズ検証 | `len(v.encode("utf-8"))` で UTF-8 バイト数を確認 (マルチバイト文字対応) |
| メディア読み込み | `mimetypes.guess_type()` で MIME タイプを判定し、`base64.b64encode()` でエンコード |
| ツールディスパッチ | `POST /v1/call_tool` が `{name, args}` を受け取り `_dispatch_file_tool()` に委譲する。`agent_repl.py` (HTTP トランスポートモード) から呼び出される |
| 遅延初期化 | `_LazyFileService` プロキシにより `FileService` インスタンスの生成を初回リクエスト時まで遅延。import 時の設定ロード副作用なし |

### 1.7 入出力インタフェース

**HTTP API** (2.1 機能概要のエンドポイント表を参照)

主要なリクエスト / レスポンス:

| エンドポイント | リクエスト | レスポンス |
|---|---|---|
| `POST /read_text_file` | `{path: str, head?: int, tail?: int}` | `{path, content, size}` |
| `POST /read_media_file` | `{path: str}` | `{path, content_base64, mime_type, size}` |
| `POST /write_file` | `{path: str, content: str}` | `{path, size}` |
| `POST /edit_file` | `{path, edits: [{old_text, new_text}], dry_run?}` | `{path, diff, applied}` |
| `POST /grep_files` | `{path, pattern, file_pattern?, max_matches?}` | `{pattern, matches: [{file, line_number, line}], truncated}` |
| `POST /directory_tree` | `{path, depth?}` | `{root: TreeNode}` (再帰ツリー) |
| `POST /v1/call_tool` | `{name: str, args: dict}` | `{result: str, is_error: bool}` |

**MCP ツール:** `/list_allowed_directories` を除く 15 ツール

### 1.8 エラーハンドリング

| HTTP ステータス | 発生条件 |
|---|---|
| 400 | 無効なパス / ダングリングシンボリックリンク / ファイル・ディレクトリ種別違反 / 正規表現不正 / `recursive=false` で空でないディレクトリを削除 (ENOTEMPTY) |
| 403 | `ALLOWED_DIRS` 外へのアクセス / OS 権限エラー |
| 404 | ファイル / ディレクトリが存在しない |
| 413 | `read_text_file` / `read_media_file` / `read_multiple_files` でファイルサイズが `max_read_bytes` を超過 |
| 415 | UTF-8 デコード不能バイナリ (`grep_files` はスキップして継続) |
| 422 | `edit_file` の `old_text` がファイル内に見つからない / `read_text_file` で `head` と `tail` を同時指定 / `write_file` の `content` が `max_write_bytes` を超過 (Pydantic バリデーションエラー) |

`write_file` のサイズ上限超過は Pydantic バリデーションエラー (422) であり、読み取り系の 413 とは異なる。
`read_multiple_files` は個別エラーがあっても他ファイルの処理を継続し、エラー内容を `error` フィールドに格納。

### 1.9 ログ出力

- **ファイル:** `/opt/llm/logs/file-mcp.log` + 標準エラー出力
- **フォーマット:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング |
|---|---|
| `INFO` | 各操作のパス・バイト数・件数 |
| `WARNING` | 許可ディレクトリが空 (初回リクエスト時に 1 回)、`grep_files` でディレクトリ走査が権限エラーで中断した場合 |

### 1.10 クラス API

`FileopMCPServer` は `MCPServer` を継承し、HTTP モード起動ロジックを提供する。`MCPServer` 共通 API は `docs/06_ref-mcp.md` §2 を参照。

```python
from fileop_mcp_server import FileopMCPServer

FileopMCPServer().run()
```

| クラス属性 | 値 | 説明 |
|---|---|---|
| `server_name` | `"file-mcp"` | MCP `initialize` レスポンスのサーバ識別名 |
| `server_version` | `"2.0.0"` | バージョン文字列 |
| `http_port` | `8005` | HTTP モード待受ポート |
| `app_module` | `"fileop_mcp_server:app"` | uvicorn 起動ターゲット |
| `mcp_tools` | `_MCP_TOOLS` | `tools/list` に返すツール定義 (15 種) |

| メソッド | 説明 |
|---|---|
| `dispatch(name, args) -> tuple[str, bool]` | `_dispatch_file_tool(name, args)` に委譲する。`_FILE_DISPATCH` テーブルでツール名を解決し、対応する FastAPI ハンドラを直接呼び出す。`(result_text, is_error)` を返す |
| `run() -> None` | HTTP サーバを起動する (継承) |

**HTTP エンドポイント `POST /v1/call_tool`**

```json
// リクエスト
{"name": "list_directory", "args": {"path": "/opt/llm"}}

// レスポンス (トランケートあり例)
{"result": "[Tree: 3 nodes, depth=3, truncated]\n[DIR] opt/\n  [DIR] scripts/ (depth limit reached)\n    [FILE] agent.py (12 KB)", "is_error": false}
```

---
