# GitHub 操作 MCP サーバ (github-mcp)

## 1. GitHub 操作 MCP サーバ (github-mcp)

### 1.1 機能概要

`mcp/github/server.py` は GitHub API を HTTP 経由で提供する MCP 互換サーバ。`@modelcontextprotocol/server-github` 相当の機能を Python + PyGithub で実装している。HTTP モード (ポート 8006) で動作する。

| 起動モード | 利用元 | 提供機能 |
|---|---|---|
| HTTP モード (ポート 8006) | `agent/repl.py` (HTTP モード) | 24 エンドポイント (全 HTTP API: POST 21 + `/health` + `/v1/call_tool` + `/v1/tools`) |

HTTP の操作エンドポイント (POST) と MCP ツールは 1 対 1 で対応。`/health` は MCP ツールとして非公開。

**認証・レート制限:** PyGithub は同期 API のため `asyncio.to_thread` でスレッドプールに委譲する。`GITHUB_TOKEN` (PAT: Personal Access Token) 未設定の場合は匿名アクセスとなり、GitHub API のレート制限が 60 req/hour に制限される。`GithubException` は HTTP エラーコードに応じて 404 / 403 / 502 に変換する。

| エンドポイント | メソッド | 説明 |
|---|---|---|
| `/search_repositories` | POST | GitHub リポジトリを検索する |
| `/get_file_contents` | POST | リポジトリ内のファイル内容を取得する |
| `/push_files` | POST | 複数ファイルを単一コミットとして push する (原子的操作) |
| `/delete_repo_file` | POST | リポジトリのファイルを削除する |
| `/list_branches` | POST | ブランチ一覧を取得する |
| `/get_commit` | POST | 特定のコミット詳細を取得する |
| `/list_issues` | POST | イシュー一覧を取得する |
| `/get_issue` | POST | 特定のイシューを取得する |
| `/create_issue` | POST | イシューを作成する |
| `/search_issues` | POST | イシュー/PR をキーワード検索する |
| `/list_pull_requests` | POST | プルリクエスト一覧を取得する |
| `/get_pull_request` | POST | 特定のプルリクエストを取得する |
| `/search_pull_requests` | POST | プルリクエストをキーワード検索する |
| `/update_pull_request` | POST | プルリクエストのタイトル/本文/状態を更新する |
| `/merge_pull_request` | POST | プルリクエストをマージする |
| `/list_commits` | POST | コミット一覧を取得する |
| `/search_code` | POST | コードを検索する |
| `/create_pull_request` | POST | プルリクエストを作成する |
| `/create_branch` | POST | ブランチを作成する |
| `/create_or_update_file` | POST | リポジトリ内のファイルを作成または更新する |
| `/add_issue_comment` | POST | イシューにコメントを投稿する |
| `/health` | GET | ヘルスチェック |
| `/v1/call_tool` | POST | ツール名と引数を受け取り、フォーマット済みテキスト結果を返す (HTTP トランスポートモード用) |
| `/v1/tools` | GET | ツール名と説明一覧を返す (エージェント起動時のツール定義検証用) |

書き込み系操作の許可リスト (`allowed_repos` / `allowed_repos_mode`)

`config/github_mcp_server.toml` の `allowed_repos` に `owner/repo` 形式で許可リポジトリを列挙する。動作は `allowed_repos_mode` で切り替える。

| `allowed_repos_mode` | リストが空 | リストに列挙あり |
|---|---|---|
| `"fail_open"` (デフォルト) | 全リポジトリを許可 | 列挙済みのみ許可 |
| `"fail_closed"` | 全リポジトリを拒否 | 列挙済みのみ許可 |

対象外リポジトリへの書き込みは HTTP 403 を返す。書き込み系対象: `create_branch`, `create_or_update_file`, `push_files`, `delete_repo_file`, `create_issue`, `add_issue_comment`, `create_pull_request`, `update_pull_request`, `merge_pull_request`。

ブランチ保護 (`protected_branches` / `_resolve_and_check_branch()`)

`config/github_mcp_server.toml` の `protected_branches` に保護ブランチ名または glob パターン (`fnmatch` 形式、例: `"main"`, `"release/*"`) を列挙する。`push_files` / `create_or_update_file` / `delete_repo_file` 等の書き込み系操作は実行前に `_resolve_and_check_branch()` を呼び出し、対象ブランチが保護パターンに一致する場合は HTTP 403 を返す。`branch=""` (省略) のとき GitHub API でデフォルトブランチを解決してからチェックする。リストが空 (デフォルト) のときは API 呼び出しをスキップして全ブランチを許可する。

ファイルパス制限 (`path_denylist` / `_assert_allowed_path()`)

`config/github_mcp_server.toml` の `path_denylist` に拒否するパスパターン (`fnmatch` glob 形式) を列挙する。`create_or_update_file` / `push_files` / `delete_repo_file` は実行前に `_assert_allowed_path()` を呼び出し、一致した場合は HTTP 403 を返す。リストが空 (デフォルト) のときはすべてのパスを許可する。例: `[".github/**", "Dockerfile*"]`。

ファイルサイズ制限 (`max_file_size_kb` / `_assert_max_file_size()`)

`create_or_update_file` / `push_files` は送信前にファイル内容を UTF-8 エンコードした KB 数を確認する。`max_file_size_kb` を超える場合は HTTP 400 を返す。`0` または負値のとき無効化 (上限なし)。デフォルト: `1024` (1 MB)。

GitHub 操作監査ログ (`audit_log_path`)

書き込み系操作が成功するたびに `audit_log_path` に 1 行のレコードを追記する。書き込みエラー (OSError) はログ出力して無視 (audit 失敗は呼び出し元に伝播させない)。パスが空文字のとき書き込みをスキップする。

レコードフォーマット例:
```
2024-01-15T12:34:56.789012+00:00 op=push_files repo='org/repo' branch='main' paths=['src/a.py'] commit='abc12345'
```

| フィールド | 説明 |
|---|---|
| ISO8601 タイムスタンプ | UTC |
| `op=` | 操作名 (例: `push_files`, `create_branch`, `merge_pull_request`) |
| `repo=` | `owner/repo` 形式 |
| `branch=` / `paths=` / `commit=` / `pr_number=` | 操作に応じて付加 |

### 1.2 サービス構成ファイル

| ファイル | 配置先 | 説明 |
|---|---|---|
| `scripts/mcp/github/server.py` | `/opt/llm/scripts/mcp/github/server.py` | GitHub MCP サーバ本体 |
| `config/github_mcp_server.toml` | `/opt/llm/config/github_mcp_server.toml` | 取得件数上限設定 |
| `init.d/github-mcp` | `/etc/init.d/github-mcp` | OpenRC 起動スクリプト |
| `conf.d/github-mcp` | `/etc/conf.d/github-mcp` | GITHUB_TOKEN 設定ファイル |

### 1.3 インストール

```bash
# 1. PyGithub をインストールする
source /opt/llm/venv/bin/activate
pip install "PyGithub>=2.3.0"

# 2. GitHub Personal Access Token を取得して設定する
#    GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
#    必要なスコープ: Contents (read/write), Issues (read/write), Pull requests (read/write)
#    ※ push_files / delete_repo_file / create_or_update_file を使う場合は Contents write が必要
#    ※ merge_pull_request / update_pull_request を使う場合は Pull requests write が必要
cp conf.d/github-mcp /etc/conf.d/github-mcp
vi /etc/conf.d/github-mcp
#   GITHUB_TOKEN="<取得した PAT>"

# 3. スクリプトと設定ファイルを配置する (deploy.sh で一括実施可能)
cp -r scripts/mcp/github/ /opt/llm/scripts/mcp/
cp config/github_mcp_server.toml /opt/llm/config/

# 4. OpenRC スクリプトを配置して有効化する
cp init.d/github-mcp /etc/init.d/github-mcp
chmod +x /etc/init.d/github-mcp
rc-update add github-mcp default

# 5. サービスを起動する
rc-service github-mcp start

# 6. 動作確認
curl -s http://127.0.0.1:8006/health
# → {"status":"ok","github_token":"set"}
#    github_token が "not_set" の場合は /etc/conf.d/github-mcp を確認する

curl -s -X POST http://127.0.0.1:8006/search_repositories \
  -H "Content-Type: application/json" \
  -d '{"query": "sqlite-vec language:C stars:>100", "per_page": 3}' \
  | python3 -m json.tool
```

### 1.4 使用方法

```bash
# agent.py REPL 経由での利用 (LLM が自律的に GitHub ツールを選択する)
source /opt/llm/venv/bin/activate
python /opt/llm/scripts/agent.py
# agent[chat]> sqlite-vec の最新バージョンと主な機能を教えてください

# HTTP API 直接呼び出し
curl -s -X POST http://127.0.0.1:8006/search_repositories \
  -H "Content-Type: application/json" \
  -d '{"query": "sqlite-vec language:C stars:>100", "per_page": 3}' \
  | python3 -m json.tool
# → {"query": "...", "results": [{"full_name": "...", "description": "...", "url": "...", "stars": 1234}]}

curl -s -X POST http://127.0.0.1:8006/get_file_contents \
  -H "Content-Type: application/json" \
  -d '{"owner": "asg017", "repo": "sqlite-vec", "path": "README.md"}' \
  | python3 -m json.tool
# → {"path": "README.md", "content": "...", "sha": "..."}
```

### 1.5 設定項目

| パラメータ | ファイル | デフォルト | 説明 |
|---|---|---|---|
| `default_per_page` | `config/github_mcp_server.toml` | `20` | 一覧取得のデフォルト件数 |
| `max_per_page` | `config/github_mcp_server.toml` | `30` | 一覧取得の最大件数 |
| `allowed_repos` | `config/github_mcp_server.toml` | `[]` | 書き込みを許可するリポジトリ一覧 (`owner/repo` 形式) |
| `allowed_repos_mode` | `config/github_mcp_server.toml` | `"fail_open"` | 空リスト時の動作: `"fail_open"` (全許可) / `"fail_closed"` (全拒否) |
| `protected_branches` | `config/github_mcp_server.toml` | `[]` | 書き込みを拒否するブランチ名または glob パターン (`fnmatch`) |
| `path_denylist` | `config/github_mcp_server.toml` | `[]` | 書き込みを拒否するファイルパスの glob パターンリスト (`fnmatch`) |
| `max_file_size_kb` | `config/github_mcp_server.toml` | `1024` | ファイル 1 件あたりの書き込みサイズ上限 (KB); `0` 以下で無効化 |
| `audit_log_path` | `config/github_mcp_server.toml` | `""` | GitHub 操作監査ログのファイルパス; 空文字で書き込みスキップ |
| `allow_force_push` | `config/github_mcp_server.toml` | `true` | `false` のとき `merge_pull_request` で `merge_method="rebase"` を拒否 (403) |
| `require_pr_review` | `config/github_mcp_server.toml` | `false` | `true` のとき承認済みレビューがない PR のマージを拒否 (403) |

### 1.6 実装方式

| 機能 | 実装 |
|---|---|
| フレームワーク | FastAPI + Uvicorn (ポート 8006) |
| 起動モード | HTTP モード (ポート 8006、OpenRC サービス `github-mcp`) |
| 設定クラス | `GitHubConfig` dataclass (`mcp/github/models.py`): 設定値を型付きで保持。`GitHubConfig.load()` で TOML から読み込み; `GitHubConfig.from_dict(d)` でテスト用に直接構築可能 |
| サービスクラス | `GitHubService` (`mcp/github/service.py`) がすべての GitHub API 操作を実装する。`GitHubService(gh, cfg: GitHubConfig)` で初期化し、`_LazyGitHubService` プロキシにより初回アクセス時まで初期化を遅延する |
| GitHub API クライアント | PyGithub (同期ライブラリ) を `asyncio.to_thread` でスレッドプール実行 |
| 認証 | `GITHUB_TOKEN` 環境変数 (PAT) → `Github(auth=Auth.Token(...))` で初期化; 未設定時は匿名 (60 req/hour) |
| エラー変換 | `GitHubService._handle_github_error()` で `GithubException` を domain 例外 (`GitHubNotFoundError`/`GitHubAuthorizationError`/`GitHubUpstreamError`) に変換; server.py の `@app.exception_handler` が HTTP 応答に変換する |
| domain 例外 | `GitHubAuthorizationError` (403) / `GitHubNotFoundError` (404) / `GitHubValidationError` (400) / `GitHubConflictError` (409) / `GitHubUpstreamError` (502) / `GitHubAuditError` (500) — すべて `mcp.github.models` で定義 |
| ページネーション | `itertools.islice` で `per_page` 件に打ち切り。`_clamp_per_page()` で `max_per_page` を超えないよう制限 |

### 1.7 入出力インタフェース

**HTTP API** (3.1 機能概要のエンドポイント表を参照)

主要なリクエスト / レスポンス:

| エンドポイント | リクエスト | レスポンス |
|---|---|---|
| `POST /search_repositories` | `{query: str, per_page?: int}` | `{query, results: [{full_name, description, url, stars, forks, language, updated_at}]}` |
| `POST /get_file_contents` | `{owner, repo, path, ref?}` | `{path, content, sha, size, encoding}` |
| `POST /create_or_update_file` | `{owner, repo, path, content, message, branch?, sha?}` | `{path, commit_sha, operation}` (`operation` は `"created"` or `"updated"`) |
| `POST /list_issues` | `{owner, repo, state?}` | `{issues: [{number, title, state, url, body, created_at, updated_at, labels, assignees}]}` |
| `POST /merge_pull_request` | `{owner, repo, pr_number, merge_method?, commit_title?, commit_message?}` | `{pr_number, merged, sha, message}` |
| `POST /v1/call_tool` | `{name: str, args: dict}` | `{result: str, is_error: bool}` |

`merge_method` は `"merge"` / `"squash"` / `"rebase"` (デフォルト: `"merge"`)。

`search_pull_requests` はクエリに `is:pr` を自動付加するため、クエリ文字列への明示的な記述は不要。

**MCP ツール:** HTTP の操作エンドポイント (POST) と 1 対 1 で対応する 21 ツール (ツール名はすべて `github_` プレフィックス)

### 1.8 エラーハンドリング

| ケース | 対処 |
|---|---|
| `GithubException` (404) | HTTP 404 (リポジトリ・ファイル不存在) |
| `GithubException` (403) | HTTP 403 (API レート制限またはアクセス拒否) |
| `GithubException` (その他) | HTTP 502 + エラーコードと詳細 |
| `GITHUB_TOKEN` 未設定 | 匿名アクセスで動作継続 (60 req/hour 制限) |
| `per_page` 上限超過 | `min(req.per_page, MAX_PER_PAGE)` でサーバ側で打ち切り |

### 1.9 ログ出力

- **ファイル:** `/opt/llm/logs/github-mcp.log` + 標準エラー出力
- **フォーマット:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング |
|---|---|
| `INFO` | 各操作の種別、リポジトリ名、取得件数 |

### 1.10 クラス API

`GithubMCPServer` は `MCPServer` を継承し、HTTP モード起動ロジックを提供する。`MCPServer` 共通 API は `docs/06_ref-mcp.md` §2 を参照。

```python
from mcp.github.server import GithubMCPServer

GithubMCPServer().run_http()
```

| クラス属性 | 値 | 説明 |
|---|---|---|
| `server_name` | `"github-mcp"` | MCP `initialize` レスポンスのサーバ識別名 |
| `server_version` | `"1.0.0"` | バージョン文字列 |
| `http_port` | `8006` | HTTP モード待受ポート |
| `app_module` | `"github_mcp_server:app"` | uvicorn 起動ターゲット |
| `mcp_tools` | `_MCP_TOOLS` | `tools/list` に返すツール定義 (21 種、すべて `github_` プレフィックス) |

| メソッド | 説明 |
|---|---|
| `dispatch(name, args) -> tuple[str, bool]` | `_dispatch_github_tool(name, args)` に委譲する。`_GITHUB_DISPATCH` テーブルでツール名を解決し、対応する FastAPI ハンドラを直接呼び出す。`(result_text, is_error)` を返す |
| `run() -> None` | HTTP サーバを起動する (継承) |

**GitHubService クラス API** (`mcp/github/service.py`)

ビジネスロジックを担うサービスクラス。`GitHubService(gh: Github, default_per_page: int, max_per_page: int)` で初期化する。

| メソッド (静的) | 説明 |
|---|---|
| `_handle_github_error(e: GithubException) -> NoReturn` | `GithubException` を HTTPException (404/403/502) に変換して raise |
| `_assert_allowed_branch(owner, repo, branch)` | `protected_branches` パターンに一致する場合 403 (内部ガード) |
| `_resolve_and_check_branch(owner, repo, branch)` | `branch=""` のときデフォルトブランチを解決してからブランチ保護チェックを実行。`protected_branches=[]` のとき API 呼び出しをスキップ |
| `_assert_allowed_path(path)` | `path_denylist` パターンに一致する場合 403 |
| `_assert_max_file_size(content, path)` | `max_file_size_kb` 超過時 400 |
| `_write_github_audit_log(op, **kwargs)` | 監査ログに 1 行追記。書き込みエラーは伝播させない |

| メソッド (インスタンス) | 説明 |
|---|---|
| `_assert_allowed_repo(owner, repo)` | `allowed_repos` / `allowed_repos_mode` に基づき 403 または通過 |
| `_clamp_per_page(per_page) -> int` | `min(per_page, max_per_page)` で制限 |
| `get_dispatch_table() -> dict[str, ...]` | ツール名 → `fmt_*` コルーチンのディスパッチテーブルを返す |

`merge_pull_request` は追加で以下を検証する:
- `allow_force_push=false` かつ `merge_method="rebase"` の場合 403
- `require_pr_review=true` かつ承認済みレビューがない場合 403
- ベースブランチが `protected_branches` に一致する場合 403

**HTTP エンドポイント `POST /v1/call_tool`**

```json
// リクエスト
{"name": "github_search_repositories", "args": {"query": "fastapi"}}

// レスポンス
{"result": "[tiangolo/fastapi](https://...) ★78000 Python\n...", "is_error": false}
```

---
