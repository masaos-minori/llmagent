---
title: "MCP Server Catalog: web-search-mcp / file-read-mcp / github-mcp"
category: mcp
tags:
  - mcp
  - server-catalog
  - web-search
  - file-read
  - github
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_04_02_file-write-file-delete-shell.md
  - 04_mcp_04_03_rag-pipeline-and-cicd.md
  - 04_mcp_04_04_mdq.md
  - 04_mcp_04_05_git.md
---

# MCP Server Catalog: web-search-mcp / file-read-mcp / github-mcp

## 目的

全10 MCP サーバーのサーバーごとの仕様: 目的、ポート、ツール、入出力、
設定、起動、セキュリティ、ログ、運用上の注意点、既知の制約。

> **注記:** 本ドキュメントは正式なサーバーカタログである。ポートとトランスポート種別を含むシステムレベルのサーバー一覧については、[04_mcp_01_system_overview.md §Server Catalog](04_mcp_01_system_overview.md) を参照。

---

## web-search-mcp（ポート 8004）

**目的:** DuckDuckGo によるウェブ検索（API キー不要）。
**起動モード:** persistent（HTTP）
**設定:** `config/web_search_mcp_server.toml`

**ツール:**

| ツール | 入力 | 出力 |
|---|---|---|
| `search_web` | `{query: str, max_results?: int}` | ヘッダー + N件の結果ブロック（title/URL/snippet） |

**設定パラメータ:**

| キー | デフォルト | 説明 |
|---|---|---|
| `default_max_results` | `5` | デフォルトの結果件数 |
| `max_results_limit` | `20` | サーバー側の上限 |

**ヘルス:** `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}` — ready 時は HTTP 200、degraded 時は 503。
**ログ:** `/opt/llm/logs/web-search-mcp.log`
**使用場面:** RAG インデックスにないリアルタイム情報; 最新リリース; ニュース。

---

## file-read-mcp（ポート 8005）

**目的:** `allowed_dirs` 内のローカルファイルシステムへの読み取り専用アクセス。
**起動モード:** persistent（HTTP）
**設定:** `config/file_read_mcp_server.toml`

**ツール（9個）:** `read_text_file`, `list_directory`, `list_directory_with_sizes`, `directory_tree`,
`read_media_file`, `read_multiple_files`, `search_files`, `grep_files`, `get_file_info`

全ツールとも config を必要としない（`requires_config: false`）。

**主要なツール入力:**

| Tool | Input |
|---|---|
| `read_text_file` | `{path, head?, tail?}` |
| `read_media_file` | `{path, mime_type?}` |
| `read_multiple_files` | `{paths: list[str]}` |
| `list_directory` | `{path}` |
| `list_directory_with_sizes` | `{path}` |
| `directory_tree` | `{path, depth?}` |
| `search_files` | `{path, pattern}` |
| `grep_files` | `{path, pattern, file_pattern?, max_matches?}` |
| `get_file_info` | `{path}` |

**設定フィールド:** `allowed_dirs`, `max_read_bytes`（デフォルト: 1,000,000）, `max_tree_depth`（デフォルト: 5）, `max_search_results`（デフォルト: 200）

**ヘルス:** `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{"filesystem":"/workspace is not a directory"/"check failed: <error>"},"details":{}}` — ready 時は HTTP 200、degraded 時は 503。
**エラーコード:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**ログ:** `/opt/llm/logs/file-read-mcp.log`
**追加エンドポイント:** `GET /list_allowed_directories`（MCP ツールではない）

---

## github-mcp（ポート 8006）

**目的:** PyGithub 経由の GitHub API。GitHub リポジトリへの読み書きを行う。
**起動モード:** persistent（HTTP）
**設定:** `config/github_mcp_server.toml`
**認証:** `GITHUB_TOKEN` 環境変数（PAT）; 未設定の場合は匿名で 60 req/hour

**ツール（21個）:** 全て `github_` 接頭辞: `github_search_repositories`, `github_get_file_contents`,
`github_push_files`, `github_delete_file`, `github_list_branches`, `github_get_commit`, `github_list_issues`, `github_get_issue`,
`github_create_issue`, `github_search_issues`, `github_list_pull_requests`, `github_get_pull_request`,
`github_search_pull_requests`, `github_update_pull_request`, `github_merge_pull_request`, `github_list_commits`,
`github_search_code`, `github_create_pull_request`, `github_create_branch`, `github_create_or_update_file`, `github_add_issue_comment`

全ツールとも config が必須（`requires_config: true`）。

**書き込み操作（9個）はリポジトリ allowlist の対象:**
`github_create_branch`, `github_create_or_update_file`, `github_push_files`, `github_delete_file`,
`github_create_issue`, `github_add_issue_comment`, `github_create_pull_request`, `github_update_pull_request`, `github_merge_pull_request`

**設定フィールド:** `default_per_page`（20）, `max_per_page`（100）, `allowed_repos`, `protected_branches`, `path_denylist`, `max_file_size_kb`（1024 KB）, `allow_force_push`（false）, `require_pr_review`（true）, `audit_log_path`

**セキュリティ制御:**
- `allowed_repos`（fail-closed; 空リスト = 全て拒否）
- `protected_branches`（fnmatch パターン）
- `path_denylist`（fnmatch パターン）
- `max_file_size_kb`（0 = 無制限）
- `allow_force_push`（デフォルト `false`; force-push と rebase マージを許可するには `true` に設定）
- `require_pr_review`（デフォルト `true`; レビューなしでのマージを許可するには `false` に設定）

**ドメイン例外**（`scripts/mcp_servers/github/models_config.py` で定義、`models.py` で再エクスポート）: `GitHubNotFoundError` (404), `GitHubAuthorizationError` (403),
`GitHubConflictError` (409), `GitHubValidationError` (400), `GitHubUpstreamError` (502), `GitHubAuditError` (500)

**ヘルス:** トークン設定時は `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`; 未設定時は `"status":"degraded","ready":false,"dependencies":{"github_token":"not_set"}` — ready 時は HTTP 200、degraded 時は 503。
**ログ:** `/opt/llm/logs/github-mcp.log`
**Audit ログ:** `config/github_mcp_server.toml::audit_log_path`

---

## Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_04_02_file-write-file-delete-shell.md`
- `04_mcp_04_03_rag-pipeline-and-cicd.md`
- `04_mcp_04_04_mdq.md`
- `04_mcp_04_05_git.md`

## Keywords

mcp
server-catalog
web-search-mcp, file-read-mcp, github-mcp, port 8004, port 8005, port 8006
