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
| `search_web` | `{query: str (1-500文字、トリム後非空), max_results?: int (1〜設定された`max_results_limit`、`HARD_MAX_RESULTS_LIMIT=100`でハード上限)}` | ヘッダー + N件の結果ブロック（title/URL/snippet） |

**設定パラメータ:**

| キー | デフォルト | 説明 |
|---|---|---|
| `default_max_results` | `5` | デフォルトの結果件数 |
| `max_results_limit` | `20` | サーバー側の上限（`HARD_MAX_RESULTS_LIMIT=100`以下でなければならない） |
| `search_timeout_sec` | `10.0` | プロバイダ呼び出しのタイムアウト秒数（`(0, 60.0]`の範囲） |

**注記(2026-07-17):** 上記2キーは`mcp_servers/web_search/web_search_models.py`の`SearchRequest.max_results`（Pydantic `Field`の`ge`/`le`/デフォルト値）に、モジュールインポート時にロードされる`WebSearchConfig.load()`経由で直接反映される（`server.py`の既存の`_cfg: WebSearchConfig = WebSearchConfig.load()`パターンを踏襲）。以前はこれらのモジュール定数（`DEFAULT_MAX_RESULTS=5`, `MAX_RESULTS_LIMIT=20`）がハードコードされたバリデーション境界として使われており、config値と一致してはいたが読み込まれていなかった。

**注記(2026-07-20):** `WebSearchConfig.from_dict()`は次の不変条件をバリデーションし、違反時は`ValueError`を送出する（モジュールインポート時に評価されるため、不正な設定はプロセス起動時にフェイルファーストで検出される）: `default_max_results >= 1`、`max_results_limit >= 1`、`default_max_results <= max_results_limit`、`max_results_limit <= HARD_MAX_RESULTS_LIMIT`、`search_timeout_sec`が`(0, 60.0]`の範囲内であること。また`SearchRequest.query`はフィールドバリデータで正規化される: 前後の空白をトリムし、トリム後に空文字列または制御文字（Unicode category `Cc`、NUL含む）を含む場合はリクエストを拒否する。`search_web`ツールの`inputSchema`（`web_search_tools.py`の`TOOL_LIST`）は`minLength`/`maxLength`/`minimum`/`maximum`をこれらの境界値と一致するように`get_max_results_limit()`経由で同じ`_cfg`シングルトンから取得しているため、`max_results_limit`のTOML変更は`_cfg`と同様にサーバー再起動後にのみ`/v1/tools`へ反映される。

**ヘルス:** `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{"service":"web-search-mcp","provider":{...},"metrics":{...}}}` — ready 時は HTTP 200、degraded 時は 503。
**エラーハンドリング:** 全プロバイダ（DuckDuckGo）が失敗すると `WebSearchUpstreamError` を送出し、HTTP 502 を返す（`search_provider.py::search_duckduckgo` が `RuntimeError`/`TimeoutError` を捕捉して変換）。[Explicit in code]
**ログ:** `/opt/llm/logs/web-search-mcp.log`
**Audit:** Layer1 (Agent/MCP共有): tool_exec / Layer2 (共有MCP): mcp_tool_exec / Layer3 (専用): なし
**使用場面:** RAG インデックスにないリアルタイム情報; 最新リリース; ニュース。

**注記(2026-07-20):** `call_tool()` は dispatch 呼び出しを try/except/finally で包み、成功・バリデーションエラー・未知のツール名・プロバイダ障害（タイムアウト含む）のいずれの経路でも `_audit_log(...)` を必ず1回だけ発行する（従来は非送出の成功系のみ到達し、`WebSearchUpstreamError` 系の例外は audit をスキップして直接 502 ハンドラへ抜けていた）。audit レコードの `error_type` は `""`（成功）、`validation_error`/`unknown_tool`/`invalid_tool_name`/`dispatch_error`（dispatch 層で非送出のエラー）、または `timeout`/`network_error`/`parse_error`/`provider_error`（`WebSearchUpstreamError` の具象サブクラスに対する `isinstance` 判定）のいずれか。`detail` フィールドは `max_results`・`latency_ms`・80文字までの `query_preview`・`query_hash`（sha256 先頭16桁）を含む。新設の `scripts/mcp_servers/web_search/health.py`（プロバイダ健全性: 直近成功/失敗時刻、連続失敗数、`consecutive_failures >= 3` で degraded）と `scripts/mcp_servers/web_search/metrics.py`（クエリ本文を一切保持しない件数/平均レイテンシのみのカウンタ）はプロセス内メモリのみで永続化されず、`/health` の `details.provider`/`details.metrics` に反映される。degraded 判定時は `dependencies.web_search_provider` が非空になり HTTP 503 を返す。

**注記(2026-07-20):** `health.record_success()`/`record_failure()`/`metrics.record_query()`の呼び出しは新設の `scripts/mcp_servers/web_search/service.py`（`SearchRequest`の構築、`search_provider.search_duckduckgo`呼び出し、レイテンシ計測を担うオーケストレーション層）に一本化されている。`formatters.py::fdisp_search_web()`が`service.search_web()`を呼び出し、その結果を整形する。`web_search_server.py::call_tool()`はこれらの更新フックを直接呼ばず、`_audit_log(...)`用の`outcome`/`error_type`分類のみを行う——health/metricsの二重計上を避けるため、パッケージ内で`health.record_*`/`metrics.record_query`を呼び出すのは`service.py`のみである。

**注記(2026-07-20):** `browser_fetch`ツールは旧単独サーバー`browser-mcp`（ポート8016）から本サーバーへ統合された。読み取り専用のページ取得・テキスト抽出（対話操作なし; JavaScript実行なし）を行う。

| ツール | 入力 | 出力 |
|---|---|---|
| `browser_fetch` | `{url: str (http/httpsのみ), max_response_kb?: int}` | 抽出テキスト（`truncated`フラグ付き） |

**設定パラメータ（`config/web_search_mcp_server.toml`に統合済み）:**

| キー | デフォルト | 説明 |
|---|---|---|
| `browser_allowed_domains` | `[]` | fail-closed; 空 = 全て拒否（ホスト名の完全一致） |
| `browser_max_response_kb` | `256` | 抽出テキストのサイズ上限。超過時は切り詰め、`truncated=true` |
| `browser_timeout_sec` | `15` | 取得リクエストのタイムアウト秒数 |
| `browser_auth_token` | `""` | `browser_fetch`呼び出し専用のBearerトークン（`search_web`とは独立） |

**実装上の補足（browser_fetch、統合元の`04_mcp_04_06_browser.md`より移設）:**

- ホスト名が IP リテラルの場合、`ipaddress.ip_address()` で判定した上で loopback / link-local / private / reserved / multicast のいずれかに該当すれば、`allowed_domains` の内容に関わらず無条件に `BrowserAuthorizationError`（HTTP 403）を送出する。ドメイン許可リストによるチェックとは独立した defense-in-depth の経路である。(Explicit in code, `search_provider.py::_check_domain`)
- `url` のスキームは `http`/`https` のみ許可され、それ以外および hostname 欠落は `BrowserValidationError`（HTTP 422）となる。(Explicit in code)
- `max_response_kb` はツール呼び出し側で指定できるが、常にサーバー設定値 `browser_max_response_kb` を上限として `min()` で clamp される。(Explicit in code)
- テキスト切り詰めはバイト列にエンコードしてからスライスする（`_truncate`）。文字単位で素朴に切ると UTF-8 のマルチバイト文字を途中で破壊する可能性があるため。(Explicit in code)
- JavaScript を実行しない（HTML を取得し `BeautifulSoup` で可視テキストを抽出するのみ）ため、クライアントサイドでレンダリングされる SPA/React 系ページでは意味のあるテキストがほとんど、あるいは全く取得できない場合がある。これは意図された仕様である（Accepted current specification）。
- `browser_fetch`の health/metrics は`search_web`とは独立したシングルトン（`health.py`/`metrics.py`内の`_browser_*`）で管理され、`/health`の`details`に別々に反映される。

---

## file-read-mcp（ポート 8005）

**目的:** `allowed_dirs` 内のローカルファイルシステムへの読み取り専用アクセス。
**起動モード:** persistent（HTTP）
**設定:** `config/file_read_mcp_server.toml`

**ツール:** `read_text_file`, `list_directory`, `list_directory_with_sizes`, `directory_tree`,
`read_media_file`, `read_multiple_files`, `search_files`, `grep_files`, `get_file_info`

全ツールとも config を必要としない（`config_dependent: false`）。

これらのツールの実行時可用性（`enabled`/`disabled_reason`）は `allowed_dirs` に依存する（空 → 無効、理由 `"allowed_dirs is empty"`）。詳細は[04_mcp_03_06_tool-runtime-availability-metadata.md](04_mcp_03_06_tool-runtime-availability-metadata.md)。

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
**Audit:** Layer1 (Agent/MCP共有): tool_exec / Layer2 (共有MCP): なし / Layer3 (専用): なし — audit ログを書かない
**追加エンドポイント:** `GET /list_allowed_directories`（MCP ツールではない）

### 実装上の補足（file-read-mcp）

- `FileReadConfig.from_dict`（`read_models.py`）は toml の `max_read_bytes` を **KB 換算で読み替えて** 保持する（`max_file_size_kb = max_read_bytes // 1024`）。デフォルト値 1,000,000 の場合、実効上限は `1,000,000 // 1024 * 1024 = 999,424` バイトとなり、toml の値と厳密には一致しない。[Explicit in code]
- 読み取り専用系エラーは `FileAuthorizationError`(403) / `FileNotFoundError`(404) / `FileValidationError`(400 または 422 で登録されるが、`read_server.py` では 422 ハンドラのみ登録)に加え、`read_text_file` の `head`/`tail` 同時指定は Pydantic のモデルバリデーションで拒否される（`model_validator` により ValueError → FastAPI 標準の 422）。[Explicit in code]

---

## github-mcp（ポート 8006）

**目的:** PyGithub 経由の GitHub API。GitHub リポジトリへの読み書きを行う。
**起動モード:** persistent（HTTP）
**設定:** `config/github_mcp_server.toml`
**認証:** `GITHUB_TOKEN` 環境変数（PAT）; 未設定の場合は匿名で 60 req/hour

**ツール:** 全て `github_` 接頭辞: `github_search_repositories`, `github_get_file_contents`,
`github_push_files`, `github_delete_file`, `github_list_branches`, `github_get_commit`, `github_list_issues`, `github_get_issue`,
`github_create_issue`, `github_search_issues`, `github_list_pull_requests`, `github_get_pull_request`,
`github_search_pull_requests`, `github_update_pull_request`, `github_merge_pull_request`, `github_list_commits`,
`github_search_code`, `github_create_pull_request`, `github_create_branch`, `github_create_or_update_file`, `github_add_issue_comment`

全ツールとも config が必須（`config_dependent: true`）。

github MCPサーバーの`enabled`/`disabled_reason`の計算ロジックは要件15/16の実装次第。現在の契約については[04_mcp_03_06_tool-runtime-availability-metadata.md](04_mcp_03_06_tool-runtime-availability-metadata.md)を参照。

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
**Audit:** Layer1 (Agent/MCP共有): tool_exec / Layer2 (共有MCP): mcp_tool_exec / Layer3 (専用): github_audit.log

### 実装上の補足（github-mcp）

- ドメイン例外の HTTP ステータス対応（`exception_handlers.py`）: `GitHubAuthorizationError`→403, `GitHubNotFoundError`→404, `GitHubValidationError`→400, `GitHubConflictError`→409, `GitHubUpstreamError`→502, `GitHubAuditError`→500。[Explicit in code]
- PyGithub の `GithubException` は `service_security.py` のエラーハンドラでステータスコードに応じてドメイン例外へ変換される（404→NotFound, 403→Authorization, 409→Conflict, 400/422→Validation、それ以外→Upstream）。[Explicit in code]
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
