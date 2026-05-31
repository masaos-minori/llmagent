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

## §6 OpenRC

- init.d スクリプト: `init.d/git-mcp`
- conf.d テンプレート: `conf.d/git-mcp`
- 起動コマンド: `rc-service git-mcp start`
- ポート: 8014 (HTTP)
- 実行ユーザ: `llm-agent` (非 root)
