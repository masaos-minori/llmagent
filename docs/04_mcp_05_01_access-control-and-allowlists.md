---
title: "MCP Security and Safety Model: Access Control, Paths, Repos and Allowlists"
category: mcp
tags:
  - mcp
  - security
  - safety-model
  - access-control
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_05_02_auth-profiles-and-sandboxing.md
  - 04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
  - 04_mcp_05_04_mdq-rag-boundary.md
  - 04_mcp_05_05_mdq-enforcement-and-lockdown.md
---

## config/github_mcp_server.toml

- サーバーカタログ → [04_mcp_04_01_web-search-file-read-github.md](04_mcp_04_01_web-search-file-read-github.md)

## 目的

サーバー間共通のセキュリティモデルを文書化する。対象はアクセス制御、allowlist、denylist パターン、
fail-open 対 fail-closed の方針、サンドボックス、出力制限、リスクティア、AI 安全性に関する注記。

---

## サーバー別アクセス制御

| サーバー | 制御機構 | デフォルトポリシー |
|---|---|---|
| file-read-mcp | `allowed_dirs` | `["/opt/llm", "/opt/llm/storage"]` — パスジェイル |
| file-write-mcp | `allowed_dirs`（書き込み） | `["/opt/llm/storage"]` — パスジェイル |
| file-delete-mcp | `allowed_dirs` | `["/opt/llm/storage"]` — パスジェイル |
| github-mcp | `allowed_repos` | fail-closed（空 = 全書き込みを拒否） |
| shell-mcp | `command_allowlist` + `shell_cwd_allowed_dirs` | 全拒否（デフォルトでは両方とも空） |
| cicd-mcp | `repo_allowlist` + `workflow_allowlist` | 両方とも: fail-closed |
| git-mcp | `allowed_repo_paths` + `read_only` | fail-closed（空パス = 全て拒否); read_only=true |
| mdq-mcp | `allowed_dirs` | fail-closed（デフォルト `[]` = 全て拒否); `MdqAuthorizationError` を発生させる |

---

## パス制御

### `allowed_dirs`（ファイルサーバー）

```toml
# config/file_read_mcp_server.toml
allowed_dirs = ["/opt/llm", "/opt/llm/storage"]
```

- 全パスは比較前に `Path.resolve()` で解決される（`../` やシンボリックリンクを排除）
- `allowed_dirs` 外へのアクセス → HTTP 403
- 空リストの挙動: 全アクセスを拒否（fail-closed）

### `allowed_repo_paths`（git-mcp）

```toml
# config/git_mcp_server.toml
allowed_repo_paths = ["/opt/llm/myrepo"]
```

- パスはサーバー起動時に `Path.resolve()` で正規化される
- 空 → 全リポジトリアクセスを拒否（fail-closed）

---

## リポジトリ制御

### `allowed_repos`（github-mcp）

```toml
allowed_repos = ["org/myrepo", "org/otherrepo"]
```

- 空 → 全リポジトリアクセスを拒否（fail-closed）
- 空でない → リストされたリポジトリのみ許可

以下の9個の書き込み操作に適用される: `github_create_branch`, `github_create_or_update_file`, `github_push_files`,
`github_delete_file`, `github_create_issue`, `github_add_issue_comment`, `github_create_pull_request`,
`github_update_pull_request`, `github_merge_pull_request`。

### `repo_allowlist`（cicd-mcp）

```toml
repo_allowlist = []   # IMPORTANT: empty = deny all (fail-closed)
```

---

## ブランチとパスの Denylist（github-mcp）

### `protected_branches`

```toml
# config/github_mcp_server.toml
protected_branches = ["main", "master", "release/*"]   # fnmatch patterns
```

- 対象ブランチを指定する書き込み操作に適用される
- 空リスト（デフォルト）: 全ブランチを許可
- `branch=""`（省略時）: チェック前に API 経由でデフォルトブランチを解決する

**本番環境の例:**

```toml
# Protect mainline branches and release branches
protected_branches = [
    "main",
    "master",
    "release/*",
    "develop",
]
```

この設定では、`main`, `master`, `release/v1.0`, `develop` を対象とする書き込み操作は、承認によって明示的に上書きされない限りブロックされる。

### `path_denylist`

```toml
# config/github_mcp_server.toml
path_denylist = [".github/**", "Dockerfile*"]   # fnmatch glob patterns
```

- `create_or_update_file`, `push_files`, `github_delete_file` に適用される
- 空リスト（デフォルト）: 全パスを許可

**本番環境の例:**

```toml
# Prevent modifications to CI/CD configs and container definitions
path_denylist = [
    ".github/**",           # block changes to GitHub Actions/workflows
    "Dockerfile*",          # block changes to Docker files
    "docker-compose*.yml",  # block changes to docker compose configs
]
```

この設定では、GitHub Actions のワークフローファイルや Docker 関連ファイルへの変更は、承認状態に関わらずブロックされる。

### `allow_force_push`

```toml
# config/github_mcp_server.toml
allow_force_push = false   # default: force push disabled
```

- 保護対象ブランチで `force-push` 操作を許可するかどうかを制御する
- **推奨: 本番環境では `false` を維持する。** Force push は履歴を書き換え、チームの共同作業を破壊する可能性がある。
- `true` の場合、force push は `protected_branches` の保護を回避する。

**本番環境の例:**

```toml
# NEVER enable force push in production
allow_force_push = false
```

正当な force push が必要な場合（例: rebase 後のコミットの squash）は、この設定を有効化するのではなく、適切な権限を持つ GitHub の UI を直接使用すること。

### `require_pr_review`

```toml
# config/github_mcp_server.toml
require_pr_review = true   # default: PR review required
```

- `true` の場合、保護対象ブランチへの書き込み操作にはプルリクエストが必要（直接コミット不可）
- `false` の場合、保護対象ブランチへの直接コミットが許可される（他の保護の対象となる）

**本番環境の例:**

```toml
# Require PR review for all protected branch writes
require_pr_review = true
```

これにより、`main`, `master`, `release/*` ブランチへの変更は、プルリクエストを介した標準的なコードレビュープロセスを経ることが保証される。

---

## コマンド Allowlist（shell-mcp）

```toml
command_allowlist = ["ls", "cat", "grep", "git", "python3"]
```

- `argv[0]` のベース名にマッチする
- 空 → 全コマンドを拒否（fail-closed の挙動）
- `shell_cwd_allowed_dirs` が空 → 全ての `cwd` 値を拒否

### 環境変数のフィルタリング

```
env_allowlist non-empty  → keep only listed keys (denylist ignored)
env_allowlist empty      → remove denylist pattern matches
both empty               → use req.env as-is
```

---

## ワークフロー Allowlist（cicd-mcp）

```toml
# config/cicd_mcp_server.toml
workflow_allowlist = []   # empty = deny all (fail-closed)
```

**方針: fail-closed。** `workflow_allowlist` が空の場合、全てのワークフロートリガーリクエストは
`CicdAuthorizationError` で拒否される。これは `repo_allowlist` の挙動と一致する。

特定のワークフローを許可するには:

```toml
workflow_allowlist = [
    "my-org/my-repo/.github/workflows/deploy.yml",
    "my-org/my-repo/.github/workflows/ci.yml",
]
```

`workflow_allowlist` が空の場合、起動時に以下の警告が出力される:
`DENY-ALL detected: cicd.workflow_allowlist is empty. cicd-mcp will reject ALL workflow trigger requests.`

**この変更以前:** 空リストは全ワークフローを許可していた（fail-open）が、これは新規デプロイされたサーバーにおける
設定ミスのリスクであった。

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_05_02_auth-profiles-and-sandboxing.md`
- `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
- `04_mcp_05_04_mdq-rag-boundary.md`
- `04_mcp_05_05_mdq-enforcement-and-lockdown.md`

## Keywords

mcp
security
safety-model
access-control
allowed-dirs
allowed-repos
allowed-repo-paths
protected-branches
path-denylist
command-allowlist
workflow-allowlist
read-only
