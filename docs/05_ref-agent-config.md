# agent/config.py

## 1. 機能概要

ConfigLoader.load_all() が以下の設定ファイルを読み込んでマージし、AgentREPL と各コンポーネントが共用する AgentConfig dataclass を提供。

- config/llm.toml / config/http.toml / config/rag.toml / config/context.toml
- config/tools.toml / config/memory.toml / config/otel.toml / config/security.toml
- config/system_prompts.toml / config/mcp_servers.toml / config/tools_definitions.toml

config/common.toml (DBパス/sqlite-vecパス等) は load_all() の対象外。db/helper.py / rag/pipeline.py が ConfigLoader().load("common.toml") を個別に呼ぶ。

- モジュールレベル定数は _SCRIPTS_DIR / _CONFIG_DIR (Path) のみ。他は全て AgentConfig フィールドに集約済み。
- load_config() は常に新鮮なデータを返す（モジュールレベルキャッシュなし）。テスト時は _build_llm_config() 等を直接呼び出し可能。
- ctx.cfg として保持され、/reload コマンドが build_agent_config(new_cfg) で再構築し ctx.cfg を置換。

## 2. McpServerConfig dataclass (shared/mcp_config.py)

1台のMCPサーバのトランスポート設定を保持。_build_mcp_servers() が config/mcp_servers.toml の mcp_servers セクションから構築。

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| transport | str | (必須) | http / stdio |
| url | str | (必須) | HTTP ベース URL (transport=http 時に使用) |
| cmd | list[str] | (必須) | サブプロセス起動コマンド (transport=stdio 時に使用) |
| openrc_service | str | (必須) | ウォッチドッグが再起動に使う OpenRC サービス名 |
| startup_mode | str | persistent | persistent / ondemand / subprocess |
| healthcheck_mode | str | "" | http / process / ping_tool; "" = 自動推論 |
| idle_timeout_sec | int | 0 | ondemand アイドル自動停止まで秒数; 0 = 無効 |
| startup_timeout_sec | int | 30 | subprocess モード: /health ポーリングタイムアウト秒数 |
| working_dir | str | "" | stdio サブプロセス作業ディレクトリ; "" = 親プロセスの cwd を継承 |
| env | dict[str, str] | {} | stdio サブプロセスに追加注入する環境変数 |
| tool_names | list[str] | [] | 明示的ツール名リスト; [] = 静的プレフィックスルーティングに fallback |
| auth_token | str | "" | HttpTransport が送る Bearer トークン; "" = 認証無効 |
| role | str | "" | /mcp status に表示する人間可読なロールラベル |

__post_init__ でバリデーション:

- transport は "http" または "stdio" のみ
- transport="http" のとき url が空でないこと
- transport="stdio" のとき cmd が空でないこと
- startup_mode は "persistent" / "ondemand" / "subprocess" のみ。subprocess は transport="http" のみ有効 (ValueError)
- healthcheck_mode は "" / "http" / "process" / "ping_tool" のみ。"" のとき自動推論: http -> "http", stdio -> "process"

起動モード:

- persistent: エージェント起動時に即座に StdioTransport.start() を呼ぶ。stdio サーバ専用。
- ondemand: 初回ツール呼び出し時に LifecycleProtocol.ensure_ready() が起動。並行呼び出しは per-server asyncio.Lock + double-checked locking で1回のみ。
- subprocess: エージェント起動時に _ServerLifecycleRouter.start_http_subprocess() が uvicorn サブプロセスを起動し、startup_timeout_sec 秒以内に /health が 200 を返すまでポーリング。

working_dir / env の動作 (stdio のみ):

- working_dir = "": cwd=None でサブプロセスを起動 - 親プロセスの cwd を継承
- working_dir = "/some/path": Path(working_dir).is_dir() を事前確認。存在しない場合は ValueError。存在する場合は cwd=working_dir を渡す
- env = {}: env=None で起動 - OS 環境変数をそのまま継承
- env = {"KEY": "VAL"}: {**os.environ, **env} でマージし env=merged を渡す

tool_names によるルーティング:

- tool_names に名前を列挙した場合、ToolRouteResolver はそれらのツールをこのサーバへルーティングする。
- 空リストの場合、ToolRouteResolver._fallback_route() が静的プレフィックス判定にフォールバック。

| 関数 | 戻り値 | 説明 |
|---|---|---|
| _build_mcp_servers(cfg) -> dict[str, McpServerConfig] | dict | config/mcp_servers.toml の mcp_servers セクションから構築。キー例: "web_search" / "file_read" / "file_write" / "file_delete" / "github" |


## 3. AgentConfig dataclass (ネストされたサブコンフィグ構成)

AgentConfig は 7 つのドメイン固有サブコンフィグを compose する。フィールドは cfg.llm.*, cfg.rag.*, cfg.tool.* などのパスでアクセスする。

| フィールド | 型 | 説明 |
|---|---|---|
| llm | LLMConfig | LLM 通信・履歴・圧縮・SSE |
| rag | RAGConfig | RAG パイプライン・ベクトル検索 |
| tool | ToolConfig | ツール実行・キャッシュ・承認・プロンプト |
| memory | MemoryConfig | 永続セマンティックメモリ |
| mcp | MCPConfig | MCP サーバライフサイクル |
| approval | ApprovalConfig | リスクベース承認ポリシー |
| obs | ObservabilityConfig | OpenTelemetry トレース・監査ログ |

__post_init__ で _validate_cross_field() を呼ぶ（サブコンフィグ間の依存検証のみ）。

_validate_cross_field() でサブコンフィグ間の依存を検証:

- rag.use_semantic_cache=True -> rag.embed_url が空でないこと
- memory.use_memory_layer=True -> memory.memory_jsonl_dir が空でないこと
- memory.memory_embed_enabled=True -> rag.embed_url が空でないこと

### 3.1 LLMConfig (LLM 通信・履歴・圧縮・SSE)

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| llm_url | str | "" | LLM エンドポイント URL |
| http_timeout | float | 30.0 | HTTP タイムアウト秒数 |
| llm_max_retries | int | 3 | LLM リトライ回数 |
| llm_retry_base_delay | float | 1.0 | 指数バックオフ基本待機秒数 |
| llm_temperature | float | 0.2 | メイン LLM 生成温度 (0.0-2.0) |
| llm_max_tokens | int | 1024 | メイン LLM 最大生成トークン数 |
| title_llm_temperature | float | 0.1 | セッションタイトル生成 LLM の温度 |
| title_llm_max_tokens | int | 20 | セッションタイトル生成 LLM の最大トークン数 |
| sse_heartbeat_timeout | float | 30.0 | SSE 無通信 timeout 秒 (0 で無効) |
| sse_malformed_retry | int | 2 | malformed chunk の許容回数 |
| sse_reconnect_max | int | 1 | in_stream 切断後の最大再接続回数 |
| llm_stream_retry_on_heartbeat_timeout | bool | True | HEARTBEAT_TIMEOUT で再接続 |
| llm_stream_retry_on_malformed_chunk | bool | False | MALFORMED_SSE_FRAME で再接続 |
| tokenize_url | str | "" | llamacpp /tokenize エンドポイント URL; "" = chars // 4 フォールバック |
| context_token_limit | int | 0 | トークンベース監視閾値 (0 = 無効) |
| context_char_limit | int | 8000 | 会話履歴の圧縮閾値文字数 |
| context_compress_turns | int | 4 | 1回の圧縮で要約するターン対数 |
| history_protect_turns | int | 2 | 直近 N ターンを圧縮から除外 |
| budget_warn_ratio | float | 0.8 | 閾値の何割で budget warning を出すか (0, 1] |

__post_init__ バリデーション: context_char_limit >= 0, budget_warn_ratio in (0.0, 1.0], llm_max_retries >= 0, llm_retry_base_delay > 0, llm_temperature in [0.0, 2.0], llm_max_tokens >= 1, sse_* >= 0


### 3.2 RAGConfig (RAG パイプライン・ベクトル検索)

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| top_k_search | int | 10 | ベクトル / FTS 検索返却件数 |
| top_k_rerank | int | 15 | Cross-Encoder に渡す候補件数 |
| max_chunks_per_doc | int | 2 | 同一ドキュメントから取得する最大チャンク数 |
| web_search_url | str | "" | Web 検索 API エンドポイント |
| web_search_max_results | int | 5 | Web 検索結果の最大件数 |
| embed_url | str | "http://127.0.0.1:8003/embedding" | 埋め込み API エンドポイント |
| use_semantic_cache | bool | False | True のとき RAG 結果をセマンティックキャッシュ |
| semantic_cache_threshold | float | 0.92 | セマンティックキャッシュのコサイン類似度閾値 (0-1) |
| semantic_cache_max_size | int | 100 | セマンティックキャッシュの最大エントリ数 (LRU) |
| use_refiner | bool | False | True のとき Rerank 後チャンクを LLM で圧縮 |
| refiner_max_tokens | int | 512 | Refiner LLM の最大生成トークン数 |
| refiner_timeout | float | 30.0 | Refiner LLM の HTTP タイムアウト秒数 |
| refiner_max_chars_per_chunk | int | 300 | Refiner に渡す1チャンクの最大文字数 |

__post_init__ バリデーション: top_k_search >= 1, top_k_rerank >= 1, max_chunks_per_doc >= 1, refiner_max_tokens >= 1, refiner_timeout > 0, refiner_max_chars_per_chunk >= 1

### 3.3 ToolConfig (ツール実行・キャッシュ・承認・プロンプト)

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| tool_cache_ttl | float | 300.0 | ツール結果キャッシュ有効期間 (秒) |
| tool_cache_max_size | int | 200 | キャッシュ最大エントリ数 (LRU); 0 = 無制限 |
| serial_tool_calls | bool | False | True のとき tool_calls を直列実行 |
| auto_inject_notes | bool | True | True のとき起動時に全ノートをシステムプロンプトへ注入 |
| use_tool_summarize | bool | False | True のとき長いツール結果を LLM 要約 |
| tool_summarize_threshold | int | 3000 | 要約対象の文字数下限 |
| tool_definitions_strict | bool | False | True のとき agent.toml と /v1/tools 差分で起動中止 |
| tool_dedup_max_repeats | int | 3 | 同一 (name, args) が何回目で dedup ヒント注入するか |
| tool_cycle_detect_window | int | 2 | 循環プランニング検出ウィンドウ (round 数); 0 = 無効 |
| tool_error_max_consecutive | int | 3 | 全エラーターンが何回連続したらループ脱出するか |
| tool_error_retry_max | int | 1 | エラーになった (name, args) の retry 上限 |
| tool_concurrency_limits | dict[str, int] | {} | サーバキー -> 最大同時呼び出し数 |
| masked_fields | list[str] | ["file_content"] | コンソール表示でマスクする引数名 |
| plan_blocked_tools | list[str] | ["write_file", "create_directory", "delete_file", "delete_directory"] | plan_mode でブロックするツール |
| max_tool_turns | int | 5 | 1メッセージあたりの最大ツール呼び出しターン数 |
| tool_result_max_llm_chars | int | 8000 | ツール結果を LLM コンテキストに追加する文字数上限 |
| tool_results_turn_max_chars | int | 50000 | 1ターン内の全ツール結果合計文字数上限 |
| use_tool_dag | bool | False | True のとき WRITE_TOOLS を READ_TOOLS より先に実行 |
| tool_definitions | list[dict] | [] | agent.toml から読み込むツール定義 |
| system_prompts | dict[str, str] | {} | /system プレセット辞書 |
| system_prompt_tool | str | "" | システムプロンプト生成用ツールの名前 |
| allowed_tools | list[str] | [] | セッションで許可するツール名リスト。空 = 全ツール許可 |

__post_init__ バリデーション: tool_dedup_max_repeats >= 1, tool_cycle_detect_window >= 0, tool_error_max_consecutive >= 0, tool_cache_max_size >= 0, tool_error_retry_max >= 0


### 3.4 MemoryConfig (永続セマンティックメモリ)

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| use_memory_layer | bool | False | True のとき永続セマンティックメモリを有効化 |
| memory_jsonl_dir | str | "/opt/llm/memory" | JSONL 正源ファイルの保存ディレクトリ。実際のファイルは `{memory_jsonl_dir}/memories.jsonl` |
| memory_max_inject_semantic | int | 5 | SessionStart 時に注入する semantic エントリ上限。`InjectionPolicy` に渡される |
| memory_max_inject_episodic | int | 3 | UserPromptSubmit 時に注入する episodic エントリ上限。`InjectionPolicy` に渡される |
| memory_min_importance | float | 0.3 | 注入対象の最低 importance スコア (0.0-1.0)。`InjectionPolicy` に渡される |
| memory_embed_enabled | bool | False | True のとき埋め込み生成と KNN 検索を有効化。`EmbeddingClient(enabled=...)` に渡される |
| memory_embed_dim | int | 384 | 埋め込みベクトルの次元数 (vec0 スキーマと一致させること) |
| memory_dedup_threshold | float | 0.3 | 重複リンク判定の L2 距離閾値 (未満で memory_links に記録) |
| memory_max_content_chars | int | 500 | 抽出時に保存するコンテンツの最大文字数 |
| memory_embed_timeout_sec | float | 5.0 | 埋め込み HTTP 呼び出しのタイムアウト秒数（`EmbeddingClientConfig.timeout`）。`query_prefix` は `"query: "` でハードコード |
| memory_retention_days | int | 90 | メモリエントリの保持期間 (日数); 超過分は pruning 対象 |
| memory_fts_limit | int | 50 | FTS5 キャンディデート上限（再スコアリング前） |
| memory_rrf_k | int | 60 | RRF fusion 定数 |
| memory_recency_days | float | 7.0 | 最近性ブースト計算のウィンドウ (日数) |

__post_init__ バリデーション: memory_fts_limit >= 1, memory_rrf_k >= 1, memory_recency_days > 0

### 3.5 MCPConfig (MCP サーバライフサイクル)

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| mcp_servers | dict[str, McpServerConfig] | {} | サーバキー -> McpServerConfig |
| mcp_watchdog_interval | float | 0.0 | MCP 死活監視間隔 (秒); 0 で無効 |
| mcp_watchdog_max_restarts | int | 3 | ウォッチドッグの最大再起動回数 |
| github_url | str | "http://127.0.0.1:8006" | GitHub サーバ URL |


### 3.6 ApprovalConfig (リスクベース承認ポリシー)

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| approval_risk_rules | dict[str, str] | {write_file: medium, edit_file: medium, create_directory: medium, move_file: medium, delete_file: high, delete_directory: high, shell_run: high, github_push_files: high, github_create_or_update_file: high, github_delete_file: high, github_merge_pull_request: high, github_create_branch: medium, github_create_pull_request: medium, github_update_pull_request: medium, github_create_issue: medium, github_add_issue_comment: medium} | tool_name -> none/medium/high; absent tools default to medium (fail-closed) |
| approval_protected_paths | list[str] | [/opt/, /etc/, /boot/, /usr/, /bin/, /sbin/] | File path prefixes that escalate any operation to high risk |
| approval_high_risk_branches | list[str] | [main, master] | GitHub branch names where write operations escalate to high risk |
| approval_shell_safe_prefixes | list[str] | [ls, cat, echo, git log, git status, git diff, git show, git branch, pwd, find, grep] | shell_run command prefixes always auto-approved despite high base level |
| approval_resource_keys | dict[str, list[str]] | {path_keys: [path, file_path, directory_path, source, destination], branch_keys: [branch, base, head]} | Arg keys treated as resource identifiers for path/branch escalation |
| approval_dry_run_tools | list[str] | [write_file, edit_file, delete_file, delete_directory, move_file] | Tools with dry_run=True support; approval flow injects dry_run automatically |
| tool_safety_tiers | dict[str, str] | {} | tool_name -> READ_ONLY/WRITE_SAFE/WRITE_DANGEROUS/ADMIN. Absent tools default to WRITE_DANGEROUS (fail-safe) |
| allowed_root | str | "" | Absolute path prefix all file paths must be relative to; "" disables |
| approval_github_allowed_repos | list[str] | [] | GitHub repos (owner/repo) allowed for write ops; empty = deny all (fail-closed) |
| gitops_push_blocked | bool | False | Block all GitHub write operations globally when True |
| gitops_force_push_blocked | bool | True | Block github_push_files with force=True |
| gitops_protected_branches | list[str] | [main, master] | Protected branch names; push/merge to these requires high-risk approval |

__post_init__ バリデーション: approval_risk_rules の値は none/medium/high のみ。tool_safety_tiers の値は READ_ONLY/WRITE_SAFE/WRITE_DANGEROUS/ADMIN のみ。

### 3.7 ObservabilityConfig (OpenTelemetry トレース・監査ログ)

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| otel_enabled | bool | False | OpenTelemetry 有効化フラグ |
| otel_endpoint | str | "" | OTLP HTTP エンドポイント; "" = ConsoleSpanExporter |
| otel_service_name | str | llm-agent | サービス名 |
| audit_log_file | str | /opt/llm/logs/audit.log | Audit log receives turn-level JSON-lines events |
| structured_log | bool | False | True のとき agent.log は JSON-lines フォーマットを使用 |

### 3.8 ConfigLoader.load_all() と build_agent_config()

ConfigLoader.load_all() (shared/config_loader.py) が全設定ファイルをマージした dict を返し、build_agent_config() (agent/config.py:627-654) が各サブコンフィグに分解して AgentConfig を構築。

| 関数 | 場所 | 説明 |
|---|---|---|
| load_config() -> dict[str, Any] | agent/config.py:25 | ConfigLoader().load_all() を呼ぶ。例外は ConfigLoadError にラップ |
| build_agent_config(cfg_override) -> AgentConfig | agent/config.py:627 | cfg_override が None なら load_config() を使用。テスト時・/reload で直接使用 |
| _build_llm_config(cfg) -> LLMConfig | agent/config.py:498 | llm.toml / http.toml のセクションから構築 |
| _build_rag_config(cfg) -> RAGConfig | agent/config.py:526 | rag.toml のセクションから構築 |
| _build_tool_config(cfg, system_prompt_tool) -> ToolConfig | agent/config.py:544 | tools.toml のセクションから構築。system_prompt_tool は cfg.get("system_prompt_tool", "") で取得 |
| _build_memory_config(cfg) -> MemoryConfig | agent/config.py:575 | memory.toml のセクションから構築 |
| _build_approval_config(cfg) -> ApprovalConfig | agent/config.py:594 | security.toml のセクションから構築。_DEFAULT_* 定数がフォールバック値 |
| _build_mcp_servers(cfg) -> dict[str, McpServerConfig] | shared/mcp_config.py:101 | mcp_servers セクションが存在すればそれを使用。なければ legacy URL 定数に DeprecationWarning |


## 4. モジュールレベル定数 (フォールバック値)

_build_*() が config セクションの値を見つけなかったときのデフォルト値。

| 定数 | 型 | 内容 |
|---|---|---|
| _DEFAULT_PLAN_BLOCKED_TOOLS | list[str] | [write_file, create_directory, delete_file, delete_directory] |
| _DEFAULT_APPROVAL_RISK_RULES | dict[str, str] | write_file:medium, edit_file:medium, create_directory:medium, move_file:medium, delete_file:high, delete_directory:high, shell_run:high, github_*:medium/high |
| _DEFAULT_PROTECTED_PATHS | list[str] | [/opt/, /etc/, /boot/, /usr/, /bin/, /sbin/] |
| _DEFAULT_SHELL_SAFE_PREFIXES | list[str] | [ls, cat, echo, git log, git status, git diff, git show, git branch, pwd, find, grep] |
| _DEFAULT_RESOURCE_KEYS | dict[str, list[str]] | {path_keys: [path, file_path, directory_path, source, destination], branch_keys: [branch, base, head]} |
| _DEFAULT_DRY_RUN_TOOLS | list[str] | [write_file, edit_file, delete_file, delete_directory, move_file] |

## 5. MCP サーバ死活監視 (McpServerHealthState / McpServerHealthRegistry)

shared/mcp_config.py で定義。ToolExecutor のディスパッチゲートとして使用。

### McpServerHealthState Enum

| 値 | 説明 |
|---|---|
| HEALTHY = "healthy" | サーバは正常応答中 |
| DEGRADED = "degraded" | 失敗し続けているが未だ利用可能 |
| UNAVAILABLE = "unavailable" | failure_threshold (3) 回の連続失敗で遷移。ToolExecutor はこの状態のサーバへのルーティングをスキップ |

### McpServerHealthRegistry クラス

| メソッド | 戻り値 | 説明 |
|---|---|---|
| record_failure(server_key: str) -> McpServerHealthState | state | 失敗カウント +1。閾値以上で UNAVAILABLE を返して状態更新 |
| record_success(server_key: str) -> None | - | ヘルス回復。failure_count=0 にリセット |
| get_state(server_key: str) -> McpServerHealthState | state | 現在の状態。未登録なら HEALTHY |
| is_unavailable(server_key: str) -> bool | bool | UNAVAILABLE なら True |

## 6. github_server_url キーの注意

MCPConfig.github_url dataclass フィールドは、build_agent_config() で config の github_server_url キーから読み込む。

- build_agent_config(): cfg.get("github_server_url", "http://127.0.0.1:8006")
- _build_mcp_servers() フォールバック: cfg.get("github_server_url", "http://127.0.0.1:8006")

設定ファイルでは github_server_url キーを使用すること。dataclass フィールド名 github_url とは異なる。
