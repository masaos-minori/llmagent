# git-mcp — ローカル git 操作 MCP サーバ

## §1 概要

| 項目 | 値 |
|---|---|
| ポート | 8014 |
| モジュール | `mcp/git/` |
| サービス名 | `git-mcp` (OpenRC) |
| 設定ファイル | `config/git_mcp_server.toml` |
| transport | HTTP (`startup_mode = "persistent"`) |

ローカル git リポジトリへの操作を提供する MCP サーバ。
`GitService` が `allowed_repo_paths` と `read_only` の 2 段階ガードを実装し、
エージェントが意図せず危険な書き込み操作を実行するのを防ぐ。

## §2 セキュリティ設計

### 2.1 allowed_repo_paths (fail-closed)

- `allowed_repo_paths` が空リストのとき、**すべてのリポジトリアクセスを拒否する (fail-closed)**。
- 指定した絶対パスのプレフィックスに一致するリポジトリのみアクセス可能。
- パスはサーバ起動時に `Path.resolve()` で正規化され、パス・トラバーサルを無効化する。

```toml
allowed_repo_paths = [
    "/opt/llm/myrepo",   # このパス以下のリポジトリのみ許可
]
```

### 2.2 read_only (デフォルト: true)

- `read_only = true` (デフォルト) のとき、書き込みツール (git_add / git_commit / git_checkout / git_pull / git_push) はすべて `[DENIED]` を返す。
- 書き込みを許可する場合は明示的に `read_only = false` を設定する。

### 2.3 dry_run サポート

書き込みツールはすべて `dry_run: bool = false` パラメータを持つ。
`dry_run = true` を渡すと副作用なしでプレビューを返す。
`agent/repl_tool_exec.py` の `approval_dry_run_tools` に git_push / git_checkout が登録されており、
ユーザへの承認プロンプト前に自動的に dry_run が実行される。

## §3 ツール一覧

### 読み取り専用ツール (approval tier: READ_ONLY)

| ツール名 | 説明 |
|---|---|
| `git_status` | 作業ツリーの変更状態を返す |
| `git_log` | コミット履歴を返す (`max_entries` 上限あり) |
| `git_diff` | 作業ツリーまたは staged の diff を返す |
| `git_branch` | ブランチ一覧を返す (現在ブランチに `*` 付き) |
| `git_show` | 指定 ref のコミット詳細と diff を返す (8000文字上限) |

### 書き込みツール (approval tier: WRITE_SAFE / WRITE_DANGEROUS)

| ツール名 | tier | dry_run | 説明 |
|---|---|---|---|
| `git_add` | WRITE_SAFE | yes | 指定ファイルをステージングする |
| `git_commit` | WRITE_SAFE | yes | ステージ済みファイルをコミットする |
| `git_checkout` | WRITE_DANGEROUS | yes | ブランチを切り替える / 新規作成する |
| `git_pull` | WRITE_DANGEROUS | yes | リモートから pull する (dry_run は fetch --dry-run) |
| `git_push` | WRITE_DANGEROUS | yes | リモートへ push する |

## §4 設定ファイル (config/git_mcp_server.toml)

```toml
allowed_repo_paths = []   # fail-closed: 空 = 全拒否
read_only = true          # false にしないと書き込みツールは全拒否
max_log_entries = 50
auth_token = ""           # 空 = auth 無効
audit_log_path = "/opt/llm/logs/git-mcp.log"
```

## §5 agent.toml 設定

```toml
[mcp_servers.git]
transport        = "http"
url              = "http://127.0.0.1:8014"
cmd              = []
openrc_service   = "git-mcp"
startup_mode     = "persistent"
healthcheck_mode = "http"
auth_token       = ""
role             = "vcs"
tool_names       = [
  "git_status", "git_log", "git_diff", "git_branch", "git_show",
  "git_add", "git_commit", "git_checkout", "git_pull", "git_push",
]
```

tool_safety_tiers エントリ (agent.toml):
```toml
git_status   = "READ_ONLY"
git_log      = "READ_ONLY"
git_diff     = "READ_ONLY"
git_branch   = "READ_ONLY"
git_show     = "READ_ONLY"
git_add      = "WRITE_SAFE"
git_commit   = "WRITE_SAFE"
git_checkout = "WRITE_DANGEROUS"
git_pull     = "WRITE_DANGEROUS"
git_push     = "WRITE_DANGEROUS"
```

## §6 クラス API

### GitMCPServer (`mcp/git/server.py`)

`MCPServer` サブクラス。`MCPServer` 共通 API は `docs/06_ref-mcp.md` §2 を参照。

| クラス属性 | 値 | 説明 |
|---|---|---|
| `server_name` | `"git-mcp"` | MCP サーバ識別名 |
| `server_version` | `"1.0.0"` | バージョン文字列 |
| `http_port` | `8014` | HTTP モード待受ポート |
| `app_module` | `"mcp.git.server:app"` | uvicorn 起動ターゲット |
| `mcp_tools` | `_MCP_TOOLS` | `tools/list` に返すツール定義 (10 種) |

| メソッド | 説明 |
|---|---|
| `dispatch(name, args) -> tuple[str, bool]` | `_dispatch_git_tool(name, args)` に委譲する |

### GitService (`mcp/git/service.py`)

ローカル git 操作を `allowed_repo_paths` と `read_only` の 2 段階ガードで実行するサービスクラス。

`GitService(allowed_repo_paths, read_only=True, max_log_entries=50)` で初期化する。

| メソッド (ガード) | シグネチャ | 説明 |
|---|---|---|
| `_check_repo_path` | `(repo_path: str) -> tuple[bool, str]` | `allowed_repo_paths` 内のプレフィックスに一致するか確認。空リスト時は常に拒否 |
| `_check_write` | `() -> tuple[bool, str]` | `read_only=True` のとき `[DENIED]` を返す |
| `_open_repo` | `(repo_path: str) -> git.Repo` | GitPython の `Repo` を開く。`search_parent_directories=False` |
| `get_dispatch_table` | `() -> dict[str, Callable]` | ツール名 → コルーチンのディスパッチテーブルを返す |

**ツール引数仕様:**

| ツール名 | 必須引数 | オプション引数 | 備考 |
|---|---|---|---|
| `git_status` | `repo_path: str` | — | アクティブブランチ・変更ファイル・untracked を返す |
| `git_log` | `repo_path: str` | `max_entries: int=20`, `branch: str=""` | `max_entries` は `max_log_entries` 設定値で上限 |
| `git_diff` | `repo_path: str` | `staged: bool=False`, `commit: str=""` | `staged=True` で `--cached`; `commit` が非空なら指定コミットとの diff |
| `git_branch` | `repo_path: str` | — | 現在ブランチは `*` 付き |
| `git_show` | `repo_path: str` | `ref: str="HEAD"` | `--stat --patch` 形式; 8000 文字で切り捨て |
| `git_add` | `repo_path: str`, `paths: list[str]` | `dry_run: bool=False` | `read_only=false` かつ `dry_run=false` のとき実際にステージング |
| `git_commit` | `repo_path: str`, `message: str` | `dry_run: bool=False` | ステージ済みファイルがないとき `[ERROR]` を返す |
| `git_checkout` | `repo_path: str`, `branch: str` | `create: bool=False`, `dry_run: bool=False` | `create=True` で新規ブランチ作成 (-b 相当) |
| `git_pull` | `repo_path: str` | `remote: str="origin"`, `branch: str=""`, `dry_run: bool=False` | `dry_run=True` は `fetch --dry-run` を実行 |
| `git_push` | `repo_path: str` | `remote: str="origin"`, `branch: str=""`, `dry_run: bool=False` | `branch` 省略時はアクティブブランチを使用 |

## §7 OpenRC

- init.d スクリプト: `init.d/git-mcp`
- conf.d テンプレート: `conf.d/git-mcp`
- 起動コマンド: `rc-service git-mcp start`
- ポート: 8014 (HTTP)
- 実行ユーザ: `llm-agent` (非 root)
