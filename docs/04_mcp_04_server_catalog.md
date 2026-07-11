# MCP サーバーカタログ

- システム概要 → [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md)
- セキュリティモデル → [04_mcp_05_security_and_safety_model.md](04_mcp_05_security_and_safety_model.md)
- 設定 → [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

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

## file-write-mcp（ポート 8007）

**目的:** ローカルファイルシステムへの書き込み操作。全ツールが `dry_run=True` をサポート。
**起動モード:** persistent（HTTP）
**設定:** `config/file_write_mcp_server.toml`

**ツール（4個）:** `write_file`, `edit_file`, `create_directory`, `move_file`

全ツールとも config を必要としない（`requires_config: false`）。

**設定フィールド:** `allowed_dirs`, `max_write_bytes`（デフォルト: 1,000,000）

| ツール | 入力 | dry_run の挙動 |
|---|---|---|
| `write_file` | `{path, content, dry_run?}` | diff のみ返す; 書き込みなし |
| `edit_file` | `{path, edits: [{old_text, new_text}], dry_run?}` | diff を返す; 書き込みなし |
| `create_directory` | `{path, dry_run?}` | ディレクトリ情報を返す（存在するか/作成予定か）; 作成なし |
| `move_file` | `{source, destination, dry_run?}` | 移動可能かどうかを返す |

**ヘルス:** `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{"filesystem":"/workspace is not a directory"/"check failed: <error>"},"details":{}}` — ready 時は HTTP 200、degraded 時は 503。
**設定:** `max_write_bytes`（デフォルト 1 MB; Pydantic により UTF-8 バイト数として強制）
**エラーコード:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**ログ:** `/opt/llm/logs/file-write-mcp.log`

---

## file-delete-mcp（ポート 8008）

**目的:** ローカルファイルシステムの削除。全ツールが `dry_run=True` をサポート。
**起動モード:** persistent（HTTP）
**設定:** `config/file_delete_mcp_server.toml`

**ツール（2個）:** `delete_file`, `delete_directory`

全ツールとも config を必要としない（`requires_config: false`）。

**設定フィールド:** `allowed_dirs`, `audit_log_path`

| ツール | 入力 | dry_run の挙動 |
|---|---|---|
| `delete_file` | `{path, dry_run?}` | ファイル情報を返す; 削除なし |
| `delete_directory` | `{path, recursive?, dry_run?}` | 内容をスキャン（最大1000ファイル）; 削除なし |

**ヘルス:** `{"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{"filesystem":"/workspace is not a directory"/"check failed: <error>"},"details":{}}` — ready 時は HTTP 200、degraded 時は 503。
**削除 audit ログ:** `/opt/llm/logs/delete_audit.log`（ISO8601 UTC + op + path + user）
**エラーコード:** 403 (FileAuthorizationError), 404 (FileNotFoundError), 422 (FileValidationError)
**ログ:** `/opt/llm/logs/file-delete-mcp.log`

---

## shell-mcp（ポート 8009）

**目的:** `command_allowlist` 内でのサンドボックス化されたシェルコマンド実行。
**起動モード:** persistent（HTTP）
**設定:** `config/shell_mcp_server.toml`

**ツール（1個）:** `shell_run`

| キー | デフォルト | 説明 |
|---|---|---|
| `command_allowlist` | `[]` | 許可されるコマンド名（`argv[0]` のベース名） |
| `shell_cwd_allowed_dirs` | `[]` | 許可される CWD パス（空 = 全て拒否） |
| `max_timeout_sec` | `300` | タイムアウトの上限 |
| `max_output_kb` | `4096` | 出力の上限 |
| `max_memory_mb` | `512` | メモリ制限（`RLIMIT_AS`） |
| `shell_sandbox_backend` | `"none"` | `"firejail"` または `"none"`（下記サンドボックス表を参照） |
| `audit_log_path` | `"/opt/llm/logs/shell_audit.log"` | Audit ログ |
| `default_cwd` | `"/opt/llm/storage"` | リクエストで cwd が指定されない場合の作業ディレクトリ |
| `shell_path` | `"/opt/llm/venv/bin:/usr/bin:/bin"` | 子プロセスの PATH 環境変数 |
| `env_allowlist` | `[]` | req.env で許可される環境変数キー（空の場合は env_denylist を使用） |
| `env_denylist` | `["LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH"]` | req.env から除去される環境変数キーの glob パターン |
| `execution_user` | `""` | setuid でコマンドを実行する OS ユーザー（CAP_SETUID が必要） |
| `kill_policy` | `"sigterm_then_sigkill"` | タイムアウトしたプロセスに対する SIGTERM+SIGKILL、または `"sigkill_only"` |
| `kill_grace_sec` | `2.0` | SIGTERM 後、SIGKILL に切り替えるまでの待機秒数 |

**ヘルス:** sh が見つかる場合は `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{"sandbox_backend":"firejail"/"none"}}`; 見つからない場合は `"status":"degraded","ready":false,"dependencies":{"shell":"sh not found in PATH"/"check failed"}}` — ready 時は HTTP 200、degraded 時は 503。
**ログ:** `/opt/llm/logs/shell-mcp.log`

| sandbox_backend | 意味 | 使用場面 |
|---|---|---|
| `"none"` | プロセス分離なし; `RLIMIT_*` の制限のみ適用 | ローカル開発専用 |
| `"firejail"` | firejail によるプロセス分離（`--private --net=none --noroot`） | 本番環境推奨 |

> **セキュリティ注記 — サンドボックスはデフォルトで無効:** `sandbox_backend` のデフォルトは `"none"` である。
> シェルコマンドはエージェントプロセスの OS ユーザーと権限で実行される — コンテナや namespace 分離はない。
> サンドボックスを有効化するには、firejail をインストールし、
> `config/shell_mcp_server.toml` で `sandbox_backend = "firejail"` を設定する。有効なバックエンドは `/health` レスポンスの
> `details.sandbox_backend`（`"none"` または `"firejail"`）で確認できる。
> **本番環境での強制:** 本番モード（`agent.toml` の `security_profile = "production"`）では、
> `sandbox_backend = "none"` は許可されない。この組み合わせが検出された場合、エージェントは起動時に `RuntimeError` を発生させる。
> 本番環境では `sandbox_backend = "firejail"` を設定するか、shell-mcp を無効化すること。

---

## rag-pipeline-mcp（ポート 8010）

**目的:** RAG 検索パイプライン（MQE → 検索 → RRF → リランク → 重複排除 → 拡張）。
**起動モード:** persistent（HTTP）
**設定:** `config/rag_pipeline_mcp_server.toml`

**ツール（4個）:**

| ツール | 入力 | 出力 |
|---|---|---|
| `rag_run_pipeline` | `{query, history_context?, debug?}` | `augmented_text` + `selected_hits` |
| `rag_debug_pipeline` | `{query, history_context?}` | 全ての中間ステージ出力 |
| `rag_list_documents` | `{lang?, limit?}` | インデックス済みドキュメントの一覧 |
| `rag_delete_document` | `{url}` | 削除確認 |

**設定パラメータ（`RagPipelineConfig` dataclass）:**

| キー | デフォルト | 説明 |
|---|---|---|
| `use_mqe` | `true` | マルチクエリ拡張を有効化 |
| `use_rrf` | `true` | RRF 融合を有効化 |
| `rrf_k` | `60` | RRF 定数 |
| `use_rerank` | `true` | クロスエンコーダーによるリランクを有効化 |
| `use_refiner` | `false` | コンテキストの精緻化/圧縮を有効化 |
| `top_k_search` | `20` | クエリごとの KNN/BM25 上位k件 |
| `top_k_rerank` | `15` | クロスエンコーダーの上位k件 |
| `rag_top_k` | `5` | 最終結果件数 |
| `rag_min_score` | `2.0` | リランクスコアの最小しきい値 |
| `max_chunks_per_doc` | `3` | 最終結果におけるドキュメントあたりの最大チャンク数 |
| `semantic_cache_max_size` | `100` | セマンティックキャッシュのエントリ数上限 |
| `semantic_cache_threshold` | `0.92` | セマンティックキャッシュのコサイン類似度しきい値 |
| `refiner_max_tokens` | `512` | コンテキスト精緻化の最大トークン数 |
| `refiner_max_chars_per_chunk` | `300` | コンテキスト精緻化のチャンクあたりの文字数 |
| `refiner_timeout` | `30.0` | コンテキスト精緻化のタイムアウト（秒） |

**設定フィールド（単体）:** `llm_url`, `embed_url`, `rag_db_path`, `sqlite_vec_so`, `host`, `port`, `http_timeout`, `mqe_n_queries`, `mqe_prompt_template`, `rerank_prompt_template`, `use_mqe`, `use_rrf`, `use_rerank`, `use_refiner`, `rrf_k`, `top_k_search`, `top_k_rerank`, `rag_top_k`, `rag_min_score`, `max_chunks_per_doc`, `semantic_cache_max_size`, `semantic_cache_threshold`, `refiner_max_tokens`, `refiner_max_chars_per_chunk`, `refiner_timeout`

**ヘルス:** embed_url が設定されている場合は `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`; 未設定の場合は `"status":"degraded","ready":false,"dependencies":{"embed_url":"not configured"}}` または `"dependencies":{"config":"check failed"}}` — ready 時は HTTP 200、degraded 時は 503。
**設計上の注記:** HTTP ループを防ぐため、`build_rag_cfg_adapter()` では `rag_service_url = ""` がハードコードされている。
**ログ:** `/opt/llm/logs/rag-mcp.log`
**使用場面:** 全ての RAG 検索; `/rag search` コマンドはこのサーバーを経由する。

**ツールステータス:** 全4ツールとも `"production"`（stub/experimental ではない）。

---

## cicd-mcp（ポート 8012）

**目的:** GitHub Actions ワークフロー管理。
**起動モード:** persistent（HTTP）
**設定:** `config/cicd_mcp_server.toml`
**認証:** `GITHUB_TOKEN`（`conf.d/cicd-mcp` 経由）

**ツール（4個）:**

| ツール | ティア | 入力 | `requires_config` |
|---|---|---|---|
| `trigger_workflow` | WRITE_DANGEROUS | `{repo, workflow, ref?, inputs?}` | yes |
| `get_workflow_runs` | READ_ONLY | `{repo, workflow, limit?}` | yes |
| `get_workflow_status` | READ_ONLY | `{repo, run_id}` | yes |
| `get_workflow_logs` | READ_ONLY | `{repo, run_id}` | yes |

**セキュリティ:**
- `repo_allowlist`: fail-closed（空 = 全て拒否; 起動時に warning をログ出力）
- `workflow_allowlist`: fail-closed（空 = 全て拒否; 起動時に warning をログ出力）
- `trigger_workflow` は `dry_run` 引数をサポート（ツールスキーマ経由で公開）

**設定フィールド:** `repo_allowlist`, `workflow_allowlist`, `max_log_size_kb`（デフォルト: 256 KB）, `auth_token`, `github_token`

**ヘルス:** トークン設定時は `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`; 未設定時は `"status":"degraded","ready":false,"dependencies":{"github_token":"not_set"}}` または `"dependencies":{"config":"check failed"}}` — ready 時は HTTP 200、degraded 時は 503。
**ログ上限:** 最大5ジョブ、`max_log_size_kb` で設定可能（デフォルト: 合計256 KB）
**アーキテクチャ:** `CiCdService → CiBackend (Protocol) → GitHubActionsBackend`
**注記:** `CiBackend` Protocol は将来的な GitLab CI / Jenkins バックエンドへの対応を可能にする。

---

## mdq-mcp（ポート 8013）

**目的:** Markdown ドキュメントのインデックス化とコンテキスト圧縮。
**起動モード:** persistent（HTTP）
**設定:** `config/mdq_mcp_server.toml`

**ツール（9個）:** `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`, `fts_consistency_check`, `fts_rebuild`
**ツールステータス:** 7ツールが `production`（`search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`）、2ツール（`fts_consistency_check`, `fts_rebuild`）が `admin`。

**設定フィールド:** `status`, `allowed_dirs`, `db_path`, `include_globs`, `exclude_globs`, `max_search_results`, `max_snippet_chars`, `max_chunk_chars`, `max_file_chars`, `max_results_limit`, `max_chars_per_chunk`, `max_total_result_chars`, `max_outline_items`, `max_grep_matches`, `search_timeout_sec`, `enable_refresh`, `enable_grep`, `audit_log_path`, `concurrency_limit`, `summary_cache_enabled`, `summary_threshold`, `summary_model`, `use_embedding`, `embedding_dims`（デフォルト 384）, `vector_table`, `embedding_model`, `max_chars_per_match`（デフォルト 500）, `context_before`（デフォルト 2）, `context_after`（デフォルト 2）, `max_outline_depth`（デフォルト 6）, `sqlite_busy_timeout`（デフォルト 5000）

**ヘルス:** `{"status":"ok"/"degraded","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":bool,"dependencies":{...},"details":{"service":"mdq-mcp",...}}` — 基本レスポンスよりも多くのフィールドを返す（[04_mcp_06 §Health probes](04_mcp_06_06_verification-methods.md#health-probes) を参照）

**DB パス:** `/opt/llm/db/mdq.sqlite`（`config/mdq_mcp_server.toml`: `db_path`）
**ログ:** `/opt/llm/logs/mdq-mcp.log`
**使用場面:** Markdown ドキュメントのインデックス化とコンテキスト圧縮。本番用 RAG 検索には `rag-pipeline-mcp` を使用する。

### パス制御

パスを受け取る全ツールは、`allowed_dirs` を介した fail-closed な認可を強制する。

| ツール | パス入力 | 認可 |
|------|------------|---------------|
| `index_paths` | インデックス対象のディレクトリ/ファイル | `authorize_path()` — `allowed_dirs` 外の場合 `MdqAuthorizationError` を発生させる |
| `refresh_index` | 更新対象のパス | パス認可 — いずれかのパスが拒否された場合 `MdqAuthorizationError` を発生させる |
| `outline` | outline 対象のファイル | `authorize_path()` — `allowed_dirs` 外の場合 `MdqAuthorizationError` を発生させる |

- `..` トラバーサル: `authorize_path()` 内の `Path.resolve()` によりブロックされる
- シンボリックリンクによる脱出: `authorize_path()` 内の `Path.resolve()` によりブロックされる
- 空の `allowed_dirs = []`（デフォルト）: 全てのパスを拒否する（fail-closed）

インデックス化ツールを使用する前に、`config/mdq_mcp_server.toml` で `allowed_dirs` を設定すること。

### Markdown 互換性の範囲

| Markdown 機能              | サポート | フォールバックの挙動                          |
|---------------------------|---------|---------------------------------------------|
| ATX 見出し（H1〜H6）      | Yes     | —                                           |
| フェンス付きコードブロック        | Yes     | フェンス内の `#` は見出しとして扱われない   |
| YAML frontmatter          | Yes     | ファイル先頭で解析され除去される             |
| H1 より前のコンテンツ         | Yes     | `<root>` セクションとして格納される                  |
| 重複する見出し        | Yes     | ordinal により個別の chunk ID を付与              |
| Setext 見出し（===,---) | No      | プレーンテキストとして扱われる                       |
| HTML ブロック                | No      | プレーンテキストとして扱われる                       |
| MDX                       | No      | インデックス対象外（.mdx は glob で除外）         |
| GFM テーブル                | No      | 親セクション内のプレーンテキストとして格納される      |
| インライン HTML タグ          | No      | プレーンテキストとして扱われる                       |

### 検索モード

| モード | 説明 | 設定 |
|---|---|---|
| FTS5のみ（フェーズ1） | FTS5 による全文検索; 本番のベースライン | `use_embedding = false`（デフォルト） |
| ハイブリッド（フェーズ2） | FTS5 + セマンティックベクトル検索を RRF で統合 | `use_embedding = true` |

**ハイブリッド検索（フェーズ2）:**

`use_embedding = true` の場合、MDQ はハイブリッド検索を実行する。
1. `chunks_fts` に対する FTS5 キーワード検索
2. セマンティックベクトル検索（スタブ — フェーズ1では空リストを返す）
3. Reciprocal Rank Fusion（RRF）による結果の統合

**MDQ ハイブリッド対 RAG の判断基準:**

| 使用場面 | 推奨 | 理由 |
|---|---|---|
| Markdown の構造的クエリ（見出し、セクション、outline） | MDQ ハイブリッド | MDQ は Markdown ドキュメント構造を理解する; FTS5 はドキュメント内のキーワードマッチングに高精度 |
| 全インデックス済みコンテンツに対する汎用的なセマンティック検索 | RAG パイプライン | RAG はより広いコーパスカバレッジと成熟した埋め込みモデル統合を持つ |
| ドキュメント間の構造比較 | MDQ ハイブリッド | MDQ の chunk_id には見出しの階層情報が含まれる（level, parent_path, ordinal） |

> **注記:** MDQ 対 RAG の境界の詳細な定義については、[04_mcp_05 §MDQ vs RAG Boundary](04_mcp_05_security_and_safety_model.md#mdq-vs-rag-boundary) を参照。

---

## git-mcp（ポート 8014）

**目的:** 2段階の安全ガードを備えたローカル git リポジトリ操作。
**起動モード:** persistent（HTTP）
**設定:** `config/git_mcp_server.toml`
**認証:** `GITHUB_TOKEN` は不要; ローカルの git 認証情報を使用する

**ツール（10個）:**

全ツールとも config が必須（`requires_config: true`）。

| ツール | ティア | `read_only` ガード | `dry_run` | `requires_config` |
|---|---|---|---|---|
| `git_status` | READ_ONLY | — | — | yes |
| `git_log` | READ_ONLY | — | — | yes |
| `git_diff` | READ_ONLY | — | — | yes |
| `git_branch` | READ_ONLY | — | — | yes |
| `git_show` | READ_ONLY | — | — | yes |
| `git_add` | WRITE_SAFE | `read_only=true` の場合ブロック | yes | yes |
| `git_commit` | WRITE_SAFE | ブロック | yes | yes |
| `git_checkout` | WRITE_DANGEROUS | ブロック | yes | yes |
| `git_pull` | WRITE_DANGEROUS | ブロック | yes | yes |
| `git_push` | WRITE_DANGEROUS | ブロック | yes | yes |

**ヘルス:** git が見つかる場合は `{"status":"ok","ready":true,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}`; 見つからない場合は `"status":"degraded","ready":false,"dependencies":{"git":"git not found in PATH"/"check failed"}}` — ready 時は HTTP 200、degraded 時は 503。
**設定:**

| キー | デフォルト | 備考 |
|---|---|---|
| `allowed_repo_paths` | `[]` | fail-closed; 空 = 全て拒否; パスは `Path.resolve()` で解決される |
| `read_only` | `true` | 明示的に `false` にしない限り、全ての書き込みツールは `[DENIED]` を返す |
| `max_log_entries` | `50` | `git_log` のエントリ数上限 |
| `audit_log_path` | `"/opt/llm/logs/git-mcp.log"` | 操作ログ |
| `auth_token` | `""` | MCP サーバー呼び出し認証用の Bearer トークン |

**注記:** `git_show` は8000文字で切り詰められる。`git_log` の inputSchema はデフォルトで `max_entries=20`; config の上限 `max_log_entries` のデフォルトは `50`。
