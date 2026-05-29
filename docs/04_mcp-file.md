# ローカルファイル操作 MCP サーバ (file-mcp)

## 1. ローカルファイル操作 MCP サーバ (file-mcp)

### 1.1 機能概要

ファイルシステム操作 MCP サーバは責務別に 3 つのサーバに分割されている。@modelcontextprotocol/server-filesystem 準拠のツール名を採用する。

| サーバ | スクリプト | ポート | MCP ツール数 |
|---|---|---|---|
| 読み取り (file-read-mcp) | `file_read_mcp_server.py` | 8005 | 9 |
| 書き込み (file-write-mcp) | `file_write_mcp_server.py` | 8007 | 4 |
| 削除 (file-delete-mcp) | `file_delete_mcp_server.py` | 8008 | 2 |

共有コード: `file_mcp_common.py` — パス境界チェック・許可ディレクトリ管理

HTTP モードで公開する MCP ツールは HTTP の操作エンドポイント (POST) と 1 対 1 で対応する。`/list_allowed_directories` と `/health` は MCP ツールとして公開されない。

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
| `scripts/file_read_mcp_server.py` | `/opt/llm/scripts/file_read_mcp_server.py` | 読み取り MCP サーバ (ポート 8005) |
| `scripts/file_read_mcp_service.py` | `/opt/llm/scripts/file_read_mcp_service.py` | 読み取りサービス層 |
| `scripts/file_write_mcp_server.py` | `/opt/llm/scripts/file_write_mcp_server.py` | 書き込み MCP サーバ (ポート 8007) |
| `scripts/file_write_mcp_service.py` | `/opt/llm/scripts/file_write_mcp_service.py` | 書き込みサービス層 |
| `scripts/file_delete_mcp_server.py` | `/opt/llm/scripts/file_delete_mcp_server.py` | 削除 MCP サーバ (ポート 8008) |
| `scripts/file_delete_mcp_service.py` | `/opt/llm/scripts/file_delete_mcp_service.py` | 削除サービス層 |
| `scripts/file_mcp_common.py` | `/opt/llm/scripts/file_mcp_common.py` | パス境界チェック・共通ユーティリティ |
| `config/file_mcp_server.toml` | `/opt/llm/config/file_mcp_server.toml` | アクセス許可ディレクトリ・サイズ上限設定 |
| `init.d/file-mcp` | `/etc/init.d/file-mcp` | OpenRC 起動スクリプト |

### 1.3 インストール

```bash
# 1. スクリプトと設定ファイルを配置する (追加ライブラリ不要: FastAPI/uvicorn は既存 venv に含まれる)
cp scripts/file_{read,write,delete}_mcp_server.py /opt/llm/scripts/
cp scripts/file_{read,write,delete}_mcp_service.py /opt/llm/scripts/
cp scripts/file_mcp_common.py /opt/llm/scripts/
cp config/file_mcp_server.toml /opt/llm/config/

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
| `allowed_dirs` | `config/file_mcp_server.toml` | `["/opt/llm"]` | アクセス許可するベースディレクトリ |
| `max_read_bytes` | `config/file_mcp_server.toml` | 1,000,000 | 読み込みサイズ上限 (1 MB) |
| `max_write_bytes` | `config/file_mcp_server.toml` | 1,000,000 | 書き込みサイズ上限 (1 MB、UTF-8 バイト数で判定) |
| `max_tree_depth` | `config/file_mcp_server.toml` | 5 | `/directory_tree` の再帰深さ上限 |
| `max_search_results` | `config/file_mcp_server.toml` | 200 | `/search_files` の返却件数上限 |

### 1.6 実装方式

| 機能 | 実装 |
|---|---|
| フレームワーク | FastAPI + Uvicorn (read: 8005 / write: 8007 / delete: 8008) |
| 起動モード | HTTP モード (OpenRC サービス `file-mcp`) |
| 責務分割 | `ReadFileService` / `WriteFileService` / `DeleteFileService` の 3 クラスで責務を分離。`file_mcp_common.py` でパス境界チェックを共有 |
| パス境界チェック | `FileService._resolve_safe()` で `Path.resolve()` によるシンボリックリンク・`../` 解決後に許可ディレクトリリストと照合 |
| 差分編集 | `difflib.unified_diff` で unified diff 形式の差分を生成 |
| 書き込みサイズ検証 | `len(v.encode("utf-8"))` で UTF-8 バイト数を確認 (マルチバイト文字対応) |
| メディア読み込み | `mimetypes.guess_type()` で MIME タイプを判定し、`base64.b64encode()` でエンコード |
| ツールディスパッチ | `POST /v1/call_tool` が `{name, args}` を受け取り `_dispatch_file_tool()` に委譲する。`agent/repl.py` (HTTP トランスポートモード) から呼び出される |
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

**MCP ツール:** 読み取り 9 + 書き込み 4 + 削除 2 = 計 15 ツール (`/list_allowed_directories` と `/health` は MCP ツール外)

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

3 つの `MCPServer` サブクラスが責務別に HTTP モード起動ロジックを提供する。`MCPServer` 共通 API は `docs/06_ref-mcp.md` §2 を参照。

| クラス | ファイル | `server_name` | `http_port` | `mcp_tools` |
|---|---|---|---|---|
| `FileReadMCPServer` | `file_read_mcp_server.py` | `"file-read-mcp"` | 8005 | 9 種 |
| `FileWriteMCPServer` | `file_write_mcp_server.py` | `"file-write-mcp"` | 8007 | 4 種 |
| `FileDeleteMCPServer` | `file_delete_mcp_server.py` | `"file-delete-mcp"` | 8008 | 2 種 |

各サーバの `dispatch(name, args) -> tuple[str, bool]` は、内部の `_dispatch_*_tool()` テーブルでツール名を解決し `(result_text, is_error)` を返す。

**HTTP エンドポイント `POST /v1/call_tool`**

```json
// リクエスト
{"name": "list_directory", "args": {"path": "/opt/llm"}}

// レスポンス
{"result": "[DIR] scripts/\n  agent.py (12 KB)\n  ...", "is_error": false}
```

---

## 2. シェル実行 MCP サーバ (shell-mcp)

### 2.1 機能概要

`mcp/shell/server.py` はコマンドアローリスト (許可リスト) に基づいてシェルコマンドをサンドボックス実行する MCP 互換サーバ。HTTP モード (ポート 8009) で動作する。

| エンドポイント | メソッド | 説明 |
|---|---|---|
| `/shell_run` | POST | サンドボックス内でコマンドを実行し stdout / stderr を返す |
| `/health` | GET | ヘルスチェック |
| `/v1/call_tool` | POST | ツール名と引数を受け取り、フォーマット済みテキスト結果を返す |
| `/v1/tools` | GET | ツール定義一覧を返す |

コマンド実行フロー:
1. `_check_command()` — `argv[0]` ベース名を `command_allowlist` と照合 (403)
2. `_resolve_cwd()` — `cwd` が `shell_cwd_allowed_dirs` 配下か確認 (403)
3. `_filter_env()` — 呼び出し元 `env` を `env_allowlist` / `env_denylist` でフィルタ
4. `_build_argv()` — `firejail` サンドボックスラッパーを先頭に挿入 (設定時)
5. `asyncio.create_subprocess_exec()` — `preexec_fn` でリソース制限を適用
6. タイムアウト監視 — 超過時はプロセスグループに `SIGTERM` → `SIGKILL`
7. 出力打ち切り — `stdout + stderr` の合計が `max_output_kb` を超えた場合に比例配分で切り捨て
8. `_write_audit_log()` — 実行結果を監査ログに追記

### 2.2 サービス構成ファイル

| ファイル | 配置先 | 説明 |
|---|---|---|
| `scripts/mcp/shell/server.py` | `/opt/llm/scripts/mcp/shell/server.py` | Shell MCP サーバ本体 |
| `scripts/mcp/shell/service.py` | `/opt/llm/scripts/mcp/shell/service.py` | `ShellService` ビジネスロジック |
| `scripts/mcp/shell/models.py` | `/opt/llm/scripts/mcp/shell/models.py` | Pydantic モデル定義 |
| `config/shell_mcp_server.toml` | `/opt/llm/config/shell_mcp_server.toml` | アローリスト・リソース制限設定 |
| `init.d/shell-mcp` | `/etc/init.d/shell-mcp` | OpenRC 起動スクリプト |

### 2.3 設定項目

| パラメータ | ファイル | デフォルト | 説明 |
|---|---|---|---|
| `command_allowlist` | `config/shell_mcp_server.toml` | `[]` | 実行を許可するコマンド名リスト (`argv[0]` のベース名で照合) |
| `shell_cwd_allowed_dirs` | `config/shell_mcp_server.toml` | `[]` | `cwd` として許可するディレクトリ一覧; 空のとき全 `cwd` を拒否 |
| `default_cwd` | `config/shell_mcp_server.toml` | `""` | `cwd` 未指定時のデフォルト作業ディレクトリ; 空文字のとき親プロセスの `cwd` を継承 |
| `shell_path` | `config/shell_mcp_server.toml` | `"/usr/local/bin:/usr/bin:/bin"` | 子プロセスの `PATH` 環境変数 |
| `max_timeout_sec` | `config/shell_mcp_server.toml` | `300` | `timeout_sec` の上限 (秒); リクエスト値はこの値で打ち切り |
| `max_output_kb` | `config/shell_mcp_server.toml` | `4096` | `stdout + stderr` 合計の上限 (KB); 超過時は比例配分で切り捨て |
| `max_memory_mb` | `config/shell_mcp_server.toml` | `512` | 子プロセスの仮想アドレス空間上限 (`RLIMIT_AS`, MB) |
| `shell_sandbox_backend` | `config/shell_mcp_server.toml` | `"none"` | サンドボックスバックエンド: `"firejail"` / `"none"`。`firejail` が PATH に見つからない場合は起動時に警告して `"none"` にフォールバック |
| `audit_log_path` | `config/shell_mcp_server.toml` | `"/opt/llm/logs/shell_audit.log"` | 実行監査ログのファイルパス |
| `env_allowlist` | `config/shell_mcp_server.toml` | `[]` | 呼び出し元 `req.env` で許可する環境変数キーのリスト。非空のとき `env_denylist` より優先され、列挙キー以外を除去 |
| `env_denylist` | `config/shell_mcp_server.toml` | `[]` | `req.env` から除去する環境変数キーの `fnmatch` glob パターンリスト。`env_allowlist` が空のときのみ有効。例: `["LD_PRELOAD", "LD_*"]` |

**`env_allowlist` vs `env_denylist` の優先順位:**

```
env_allowlist が非空  → allowlist にないキーをすべて除去 (denylist は無視)
env_allowlist が空    → denylist パターンに一致するキーを除去
どちらも空            → req.env をそのまま使用
```

### 2.4 実装方式

| 機能 | 実装 |
|---|---|
| フレームワーク | FastAPI + Uvicorn (ポート 8009) |
| 起動モード | HTTP モード (OpenRC サービス `shell-mcp`) |
| コマンド検証 | `_check_command()` — `req.argv` 指定時は shlex をスキップ (シェルインジェクション防止); 未指定時は `shlex.split(req.command)` でパース |
| cwd 検証 | `_resolve_cwd()` — `Path.resolve()` でシンボリックリンク・`../` を解決後、`shell_cwd_allowed_dirs` 配下か照合 |
| env フィルタ | `_filter_env()` — `env_allowlist` → allowlist のみ保持; `env_denylist` → `fnmatch` 一致を除去 |
| サンドボックス | `_build_argv()` — `firejail` 時は `["firejail", "--private", "--net=none", "--noroot", "--"]` を先頭挿入 |
| リソース制限 | `preexec_fn=_set_resource_limits()` — `RLIMIT_CPU` / `RLIMIT_AS` / `RLIMIT_NOFILE` / `RLIMIT_NPROC` / `RLIMIT_FSIZE` を子プロセス内で設定 |
| タイムアウト | `asyncio.wait_for(proc.communicate(), timeout=timeout_sec)` — 超過時は `os.killpg(SIGTERM)` → 2 秒待機 → `os.killpg(SIGKILL)` |
| 出力打ち切り | `stdout_b[:half]` + `stderr_b[:half]` で KB 単位比例配分; バイト列でスライスして後から UTF-8 デコード |
| 監査ログ | `_write_audit_log()` — 書き込みエラー (OSError) はログ出力して伝播させない |
| 遅延初期化 | `_LazyShellService` プロキシ — 初回属性アクセスで `ShellService` をインスタンス化 |

### 2.5 入出力インタフェース

**`POST /shell_run` リクエスト:**

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `command` | `str` | 必須 | 実行するコマンド文字列 (`argv` が指定されている場合は無視) |
| `argv` | `list[str] \| None` | `null` | 直接指定する argv リスト; 指定時は `command` のシェルパースをスキップ |
| `cwd` | `str \| None` | `null` | 作業ディレクトリ; 未指定時は `default_cwd` を使用 |
| `timeout_sec` | `int` | `30` | タイムアウト秒数 (`max_timeout_sec` で打ち切り) |
| `max_output_kb` | `int` | `256` | 出力上限 KB (`max_output_kb` で打ち切り) |
| `env` | `dict[str, str]` | `{}` | 追加環境変数 (フィルタ後に `os.environ` にマージ) |

**`POST /shell_run` レスポンス:**

| フィールド | 型 | 説明 |
|---|---|---|
| `stdout` | `str` | 標準出力 (UTF-8 decode, replace mode) |
| `stderr` | `str` | 標準エラー出力 |
| `exit_code` | `int` | 終了コード (タイムアウト時は `-1`) |
| `timed_out` | `bool` | タイムアウトしたか |
| `truncated` | `bool` | 出力が `max_output_kb` で切り捨てられたか |
| `elapsed_sec` | `float` | 実行時間 (秒、3 桁丸め) |

### 2.6 エラーハンドリング

| HTTP ステータス | 発生条件 |
|---|---|
| 400 | `shlex.split` 失敗 (unclosed quote 等) / `command` が空 / ファイルサイズ上限超過 |
| 403 | `argv[0]` が `command_allowlist` 外 / `cwd` が `shell_cwd_allowed_dirs` 外 |

### 2.7 監査ログ

実行ごとに `audit_log_path` に 1 行追記する。書き込みエラーは `logging.error` に記録し、コマンド実行結果の返却には影響しない。

レコードフォーマット例:
```
2024-01-15T12:34:56.789012+00:00 cmd='ls' argv=['ls', '-la'] cwd='/opt/llm/workspace' uid=1000 exit=0 elapsed=0.01s truncated=False
```

| フィールド | 説明 |
|---|---|
| ISO8601 タイムスタンプ | UTC |
| `cmd=` | 元の `req.command` 文字列 |
| `argv=` | 実際に実行した argv リスト (サンドボックスラッパー挿入前の値) |
| `cwd=` | 使用した作業ディレクトリ (`None` = 継承) |
| `uid=` | サーバプロセスの実行 UID |
| `exit=` | 終了コード |
| `elapsed=` | 実行時間 (秒) |
| `truncated=` | 出力打ち切りフラグ |

### 2.8 クラス API

`ShellMCPServer` は `MCPServer` を継承し、HTTP モード起動ロジックを提供する。`MCPServer` 共通 API は `docs/06_ref-mcp.md` §2 を参照。

| クラス属性 | 値 | 説明 |
|---|---|---|
| `server_name` | `"shell-mcp"` | MCP `initialize` レスポンスのサーバ識別名 |
| `http_port` | `8009` | HTTP モード待受ポート |
| `mcp_tools` | `_MCP_TOOLS` | `tools/list` に返すツール定義 (1 種: `shell_run`) |

| メソッド | 説明 |
|---|---|
| `dispatch(name, args) -> tuple[str, bool]` | `ShellService.fmt_run_command(args)` に委譲する |
| `run() -> None` | HTTP サーバを起動する (継承) |

---
