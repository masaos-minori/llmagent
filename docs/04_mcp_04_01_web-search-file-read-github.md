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
**エラーハンドリング:** 全プロバイダ（DuckDuckGo）が失敗すると `WebSearchUpstreamError` を送出し、HTTP 502 を返す（`search_provider.py::search_duckduckgo` が `RuntimeError`/`TimeoutError` を捕捉して変換）。[Explicit in code]
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

### 実装上の補足（Current behavior）

- `FileReadConfig.from_dict`（`read_models.py`）は toml の `max_read_bytes` を **KB 換算で読み替えて** 保持する（`max_file_size_kb = max_read_bytes // 1024`）。デフォルト値 1,000,000 の場合、実効上限は `1,000,000 // 1024 * 1024 = 999,424` バイトとなり、toml の値と厳密には一致しない。[Explicit in code]
- 読み取り専用系エラーは `FileAuthorizationError`(403) / `FileNotFoundError`(404) / `FileValidationError`(400 または 422 で登録されるが、`read_server.py` では 422 ハンドラのみ登録)に加え、`read_text_file` の `head`/`tail` 同時指定は Pydantic のモデルバリデーションで拒否される（`model_validator` により ValueError → FastAPI 標準の 422）。[Explicit in code]

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

**設定フィールド:** `max_per_page`（100）, `allowed_repos`, `protected_branches`, `path_denylist`, `max_file_size_kb`（1024 KB）, `allow_force_push`（false）, `require_pr_review`（true）, `audit_log_path`

**注記（2026-07-13）:** `default_per_page` は `config/github_mcp_server.toml` から削除した。`GitHubConfig.default_per_page` は `service_security.py` の `self._default_per_page` に代入されるだけで以降参照されず、実際の一覧系エンドポイントのデフォルト件数はモジュール定数 `DEFAULT_PER_PAGE = 10`（`models_config.py`）を各リクエストモデルが直接参照する（設定不可）。`max_per_page` は `self._max_per_page` として実際に `per_page` のクランプに使われており、こちらは有効な設定である。

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

### 実装上の補足（Current behavior）

- ドメイン例外の HTTP ステータス対応（`exception_handlers.py`）: `GitHubAuthorizationError`→403, `GitHubNotFoundError`→404, `GitHubValidationError`→400, `GitHubConflictError`→409, `GitHubUpstreamError`→502, `GitHubAuditError`→500。[Explicit in code]
- PyGithub の `GithubException` は `service_security.py::_handle_github_error` でステータスコードに応じてドメイン例外へ変換される（404→NotFound, 403→Authorization, 409→Conflict, 400/422→Validation、それ以外→Upstream）。[Explicit in code]
- `allow_force_push=false` は `merge_pull_request` の `merge_method="rebase"` 指定を拒否する形でのみ適用される（それ以外の force-push 相当操作を直接ブロックする実装は無い）。[Explicit in code]
- `require_pr_review=true` は `merge_pull_request` 実行時に限り、少なくとも1件の `APPROVED` レビューが存在するかを確認する。[Explicit in code]
- `GITHUB_TOKEN` 未設定時は匿名 `Github()` クライアントで起動し、`/health` が `degraded` を返す（`service_init.py`）。[Explicit in code]

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
