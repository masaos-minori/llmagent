# agent/config.py

## 1. 機能概要

`ConfigLoader.load_all()` が以下の設定ファイルをこの順に読み込んでマージし、`AgentREPL` と各コンポーネントが共用する設定 dataclass を提供。

- `config/llm.toml` / `config/http.toml` / `config/rag.toml` / `config/context.toml`
- `config/tools.toml` / `config/memory.toml` / `config/otel.toml` / `config/security.toml`
- `config/system_prompts.toml` / `config/mcp_servers.toml` / `config/tools_definitions.toml`

`config/common.toml` (DB パス / sqlite-vec パス等) は `load_all()` の対象外。`db/helper.py` / `rag/pipeline.py` などが `ConfigLoader().load("common.toml")` を個別に呼ぶ。

- モジュールレベル定数は `_SCRIPTS_DIR` / `_CONFIG_DIR` (Path) のみ。他は全て `AgentConfig` フィールドに集約済み。
- `_cfg: dict | None = None` → `_get_cfg()` (try/except 付きキャッシュ) で遅延ロード。
- `build_agent_config()` は `_get_cfg()` を直接参照して `AgentConfig` インスタンスを生成。テスト時は `_get_cfg()` をモックするだけで設定を差し替え可能。
- `ctx.cfg` として保持され、`/reload` コマンドが `_apply_config_params()` 経由でフィールドをその場で更新。

## 2. McpServerConfig dataclass

1 台の MCP サーバのトランスポート設定を保持。`_build_mcp_servers()` が `agent.toml` の `mcp_servers` セクションから構築。

```python
@dataclass
class McpServerConfig:
    transport: str              # "http" | "stdio"
    url: str                    # HTTP ベース URL (transport="http" 時に使用)
    cmd: list[str]              # サブプロセス起動コマンド (transport="stdio" 時に使用)
    openrc_service: str         # ウォッチドッグが再起動に使う OpenRC サービス名
    startup_mode: str = "persistent"   # "persistent" | "ondemand" | "subprocess"
    healthcheck_mode: str = ""  # "http" | "process" | "ping_tool"; "" = 自動推論
    idle_timeout_sec: int = 0   # ondemand アイドル自動停止まで秒数; 0 = 無効
    startup_timeout_sec: int = 30  # subprocess モード: /health ポーリングタイムアウト秒数
    working_dir: str = ""       # stdio サブプロセス作業ディレクトリ; "" = 親プロセスの cwd を継承
    env: dict[str, str] = field(default_factory=dict)  # stdio サブプロセスに追加注入する環境変数; 空 = 継承
    tool_names: list[str] = field(default_factory=list)  # 明示的ツール名リスト; [] = 静的プレフィックスルーティングに fallback
    auth_token: str = ""        # HttpTransport が送る Bearer トークン; "" = 認証無効
    role: str = ""              # /mcp status に表示する人間可読なロールラベル
```

`__post_init__` でバリデーション:
- `transport` は `"http"` または `"stdio"` のみ
- `transport="http"` のとき `url` が空でないこと
- `transport="stdio"` のとき `cmd` が空でないこと
- `startup_mode` は `"persistent"` / `"ondemand"` / `"subprocess"` のみ。`"subprocess"` は `transport="http"` のみ有効 (`transport="stdio"` との組み合わせは `ValueError`)
- `healthcheck_mode` は `""` / `"http"` / `"process"` / `"ping_tool"` のみ。`""` 指定時はトランスポートから自動推論 (`http` → `"http"`, `stdio` → `"process"`)

**起動モード:**
- `persistent`: エージェント起動時に `_start_subprocess_servers()` が即座に `StdioTransport.start()` を呼ぶ。stdio サーバ専用。
- `ondemand`: 初回ツール呼び出し時に `ServerLifecycleManager.ensure_ready()` が起動。並行呼び出しは per-server `asyncio.Lock` + double-checked locking で 1 回のみ起動。stdio サーバ専用。
- `subprocess`: エージェント起動時に `ServerLifecycleManager.start_http_subprocess()` が uvicorn サブプロセスを起動し、`startup_timeout_sec` 秒以内に `/health` が 200 を返すまでポーリング。HTTP サーバ専用 (OpenRC 不要)。

**`working_dir` / `env` の動作 (stdio のみ):**
- `working_dir = ""` (デフォルト): `StdioTransport.start()` は `cwd=None` でサブプロセスを起動 — 親プロセスのカレントディレクトリを継承する
- `working_dir = "/some/path"`: `start()` 呼び出し時に `Path(working_dir).is_dir()` を事前確認し、存在しない場合は `ValueError` を送出する。存在する場合は `cwd=working_dir` をサブプロセスに渡す
- `env = {}` (デフォルト): `env=None` で起動 — OS 環境変数をそのまま継承する
- `env = {"KEY": "VAL"}`: `start()` 呼び出し時に `{**os.environ, **env}` でマージし `env=merged` を渡す。マージは `start()` 実行時点の `os.environ` スナップショットを使用

**tool_names によるルーティング:**
- `tool_names` に名前を列挙した場合、`ToolRouteResolver` はそれらのツールをこのサーバへルーティングする。
- 空リストの場合、`ToolRouteResolver._fallback_route()` が静的プレフィックス判定 (frozenset) にフォールバックする。

| 関数 | 戻り値 | 説明 |
|---|---|---|
| `_build_mcp_servers(cfg) -> dict[str, McpServerConfig]` | `dict` | `agent.toml` の `mcp_servers` セクションから構築。キー例: `"web_search"` / `"file_read"` / `"file_write"` / `"file_delete"` / `"github"` |

## 3. AgentConfig dataclass

ホットリロード対象のランタイム設定を一元管理。`/reload` コマンドがフィールドをその場で更新。

```python
@dataclass
class AgentConfig:
    # ── 履歴・圧縮 ────────────────────────────────────────────────────────────
    # build_agent_config() デフォルト: context_char_limit=8000, context_compress_turns=4
    context_char_limit: int          # 会話履歴の圧縮閾値文字数
    context_compress_turns: int      # 1 回の圧縮で要約するターン対数
    context_token_limit: int = 0     # トークンベース監視閾値 (0 = 無効)
    tokenize_url: str = ""           # llamacpp /tokenize エンドポイント URL; "" = 無効 (chars // 4 フォールバック)
    history_protect_turns: int = 2   # 直近 N ターンを圧縮から除外
    budget_warn_ratio: float = 0.8   # 閾値の何割で budget warning を出すか (0, 1]

    # ── RAG (mcp/rag_pipeline/ 側設定; agent 側 in-process RAG は削除済み) ────────
    # build_agent_config() デフォルト: top_k_search=20, top_k_rerank=15
    # max_chunks_per_doc=2
    # use_semantic_cache=False, semantic_cache_threshold=0.92, semantic_cache_max_size=100
    # use_refiner=False, refiner_max_tokens=512, refiner_timeout=30.0, refiner_max_chars_per_chunk=300
    top_k_search: int                # ベクトル / FTS 検索返却件数
    top_k_rerank: int                # Cross-Encoder に渡す候補件数
    max_chunks_per_doc: int          # 同一ドキュメントから取得する最大チャンク数
    use_semantic_cache: bool         # True のとき RAG 結果をセマンティックキャッシュ
    semantic_cache_threshold: float  # セマンティックキャッシュのコサイン類似度閾値 (0–1)
    semantic_cache_max_size: int     # セマンティックキャッシュの最大エントリ数 (LRU)
    use_refiner: bool                # True のとき Rerank 後チャンクを LLM で圧縮
    refiner_max_tokens: int          # Refiner LLM の最大生成トークン数
    refiner_timeout: float           # Refiner LLM の HTTP タイムアウト秒数
    refiner_max_chars_per_chunk: int # Refiner に渡す 1 チャンクの最大文字数

    # ── LLM ──────────────────────────────────────────────────────────────────
    # build_agent_config() デフォルト: llm_max_retries=3, llm_retry_base_delay=1.0
    # llm_temperature=0.2, llm_max_tokens=1024
    llm_max_retries: int             # LLM リトライ回数
    llm_retry_base_delay: float      # 指数バックオフ基本待機秒数
    llm_temperature: float           # メイン LLM 生成温度 (0.0–2.0)
    llm_max_tokens: int              # メイン LLM 最大生成トークン数
    llm_url: str = ""                # LLM エンドポイント URL

    # ── URL / HTTP ────────────────────────────────────────────────────────────
    github_url: str = "http://127.0.0.1:8006"
    web_search_url: str = ""
    embed_url: str = "http://127.0.0.1:8003/embedding"
    http_timeout: float = 30.0
    web_search_max_results: int = 5

    # ── ツール設定 ────────────────────────────────────────────────────────────
    # build_agent_config() デフォルト: tool_cache_ttl=300, serial_tool_calls=False
    # auto_inject_notes=True, use_tool_summarize=False, tool_summarize_threshold=3000
    # tool_definitions_strict=False, masked_fields=["file_content"]
    # plan_blocked_tools=["write_file","create_directory","delete_file","delete_directory"]
    tool_cache_ttl: float                              # ツール結果キャッシュ有効期間 (秒)
    tool_cache_max_size: int = 200                     # キャッシュ最大エントリ数 (LRU); 0 = 無制限
    serial_tool_calls: bool = False                    # True のとき tool_calls を直列実行
    auto_inject_notes: bool = True                     # True のとき起動時に全ノートをシステムプロンプトへ注入
    use_tool_summarize: bool = False                   # True のとき長いツール結果を LLM 要約
    tool_summarize_threshold: int = 3000               # 要約対象の文字数下限
    tool_definitions_strict: bool = False              # True のとき agent.toml と /v1/tools 差分で起動中止
    tool_definitions: list[dict] = field(default_factory=list)  # agent.toml から読み込むツール定義
    tool_result_max_llm_chars: int = 8000              # ツール結果を LLM コンテキストに追加する文字数上限
    tool_results_turn_max_chars: int = 50000           # 1 ターン内の全ツール結果合計文字数上限
    masked_fields: list[str] = field(default_factory=lambda: ["file_content"])
                                                       # コンソール表示でマスクするツール引数フィールド名
    plan_blocked_tools: list[str] = field(default_factory=list)
                                                       # plan_mode 中にブロックするツール名リスト
    tool_concurrency_limits: dict[str, int] = field(default_factory=dict)
                                                       # サーバキー → 最大同時呼び出し数 (Semaphore)

    # ── ツールループガード ─────────────────────────────────────────────────────
    # build_agent_config() デフォルト: tool_dedup_max_repeats=3, tool_cycle_detect_window=2
    # tool_error_max_consecutive=3
    tool_dedup_max_repeats: int      # 同一 (name, args) が何回目で dedup ヒント注入するか
    tool_cycle_detect_window: int    # 循環プランニング検出ウィンドウ (round 数); 0 = 無効
    tool_error_max_consecutive: int  # 全エラーターンが何回連続したらループ脱出するか
    tool_error_retry_max: int = 1    # このターンですでにエラーになった (name, args) の retry 上限

    # ── プロンプト・セッション ─────────────────────────────────────────────────
    system_prompts: dict[str, str] = field(default_factory=dict)  # /system プレセット辞書
    system_prompt_tool: str = ""
    max_tool_turns: int = 5          # 1 メッセージあたりの最大ツール呼び出しターン数

    # ── MCP サーバ ────────────────────────────────────────────────────────────
    # build_agent_config() デフォルト: mcp_watchdog_interval=0.0, mcp_watchdog_max_restarts=3
    mcp_watchdog_interval: float     # MCP 死活監視間隔 (秒); 0 で無効
    mcp_watchdog_max_restarts: int   # ウォッチドッグの最大再起動回数
    mcp_servers: dict[str, McpServerConfig] = field(default_factory=dict)

    # ── 承認ルール (risk-based approval) ────────────────────────────────────
    approval_risk_rules: dict[str, str] = field(default_factory=dict)
                                   # ツール名 → "none" | "medium" | "high"
                                   # 未登録ツールは tool_safety_tiers にフォールバック
                                   # (tier 未登録は WRITE_DANGEROUS → "medium" 相当)
    approval_protected_paths: list[str] = field(default_factory=list)
                                   # high risk にエスカレートするファイルパスプレフィックス
                                   # デフォルト: ["/opt/", "/etc/", "/boot/", "/usr/", "/bin/", "/sbin/"]
    approval_high_risk_branches: list[str] = field(default_factory=list)
                                   # 書き込み操作を high risk にするブランチ名リスト
                                   # デフォルト: ["main", "master"]
    approval_shell_safe_prefixes: list[str] = field(default_factory=list)
                                   # shell_run で自動承認とみなすコマンド先頭文字列
                                   # デフォルト: ["ls", "cat", "echo", "git log", "git status", ...]
    approval_resource_keys: dict[str, list[str]] = field(default_factory=dict)
                                   # {"path_keys": [...], "branch_keys": [...]}
                                   # デフォルト path_keys: ["path","file_path","directory_path","source","destination"]
                                   # デフォルト branch_keys: ["branch","base","head"]
    approval_dry_run_tools: list[str] = field(default_factory=list)
                                   # 承認前に dry_run プレビューを自動実行するツール名
                                   # デフォルト: ["write_file","edit_file","delete_file","delete_directory","move_file"]

    # ── ツール安全性強化 ─────────────────────────────────────────────────────
    tool_safety_tiers: dict[str, str] = field(default_factory=dict)
                                   # ツール名 → "READ_ONLY" | "WRITE_SAFE" | "WRITE_DANGEROUS" | "ADMIN"
                                   # approval_risk_rules が優先。未登録は WRITE_DANGEROUS (Fail-Safe)
    allowed_root: str = ""         # ファイルパス引数の許可ルートパス。空文字列でチェック無効
    approval_github_allowed_repos: list[str] = field(default_factory=list)
                                   # GitHub 書き込み許可リポジトリ (owner/repo)。空=Fail-Closed

    # ── 許可ツール ────────────────────────────────────────────────────────────
    allowed_tools: list[str] = field(default_factory=list)
                                   # セッションで許可するツール名リスト。空リスト = 全ツール許可

    # ── メモリ ───────────────────────────────────────────────────────────────
    use_memory_layer: bool = False          # True のとき永続セマンティックメモリを有効化
    memory_jsonl_dir: str = "/opt/llm/memory"  # JSONL 正源ファイルの保存ディレクトリ
    memory_max_inject_semantic: int = 5    # SessionStart 時に注入する semantic エントリ上限数
    memory_max_inject_episodic: int = 3    # UserPromptSubmit 時に注入する episodic エントリ上限数
    memory_min_importance: float = 0.3     # 注入対象の最低 importance スコア (0.0–1.0)
    memory_embed_enabled: bool = False     # True のとき埋め込み生成と KNN 検索を有効化
    memory_embed_dim: int = 384            # 埋め込みベクトルの次元数 (vec0 スキーマと一致させること)
    memory_dedup_threshold: float = 0.3    # 重複リンク判定の L2 距離閾値 (未満で memory_links に記録)
    memory_max_content_chars: int = 500    # 抽出時に保存するコンテンツの最大文字数
    memory_embed_timeout_sec: float = 5.0  # 埋め込み HTTP 呼び出しのタイムアウト秒数
    memory_retention_days: int = 90        # メモリエントリの保持期間 (日数); 超過分は pruning 対象

    # ── OTel / ロギング ──────────────────────────────────────────────────────
    otel_enabled: bool = False
    otel_endpoint: str = ""              # OTLP HTTP エンドポイント; 空文字 = ConsoleSpanExporter
    otel_service_name: str = "llm-agent"
    audit_log_file: str = "/opt/llm/logs/audit.log"
    structured_log: bool = False         # True のとき agent.log を JSON-lines 形式で出力

    # ── SSE ストリーム堅牢化 ───────────────────────────────────────────────────
    sse_heartbeat_timeout: float = 30.0              # 無通信 timeout 秒 (0 で無効)
    sse_malformed_retry: int = 2                     # malformed chunk の許容回数
    sse_reconnect_max: int = 1                       # in_stream 切断後の最大再接続回数
    llm_stream_retry_on_heartbeat_timeout: bool = True   # True のとき HEARTBEAT_TIMEOUT で再接続
    llm_stream_retry_on_malformed_chunk: bool = False    # True のとき MALFORMED_SSE_FRAME で再接続
```

`__post_init__` で値域バリデーションを実施。違反時は `ValueError` を送出。

| フィールド | バリデーション条件 |
|---|---|
| `context_char_limit` | `>= 0` |
| `budget_warn_ratio` | `(0.0, 1.0]` |
| `top_k_search` / `top_k_rerank` | `>= 1` |
| `llm_max_retries` | `>= 0` |
| `llm_retry_base_delay` | `> 0` |
| `max_chunks_per_doc` | `>= 1` |
| `llm_temperature` | `[0.0, 2.0]` |
| `llm_max_tokens` | `>= 1` |
| `refiner_max_tokens` | `>= 1` |
| `refiner_timeout` | `> 0` |
| `refiner_max_chars_per_chunk` | `>= 1` |
| `tool_dedup_max_repeats` | `>= 1` |
| `tool_cycle_detect_window` | `>= 0` |
| `tool_error_max_consecutive` | `>= 0` |
| `tool_cache_max_size` | `>= 0` |
| `tool_error_retry_max` | `>= 0` |
| `approval_risk_rules` の値 | `"none"` / `"medium"` / `"high"` のいずれか |
| `tool_safety_tiers` の値 | `"READ_ONLY"` / `"WRITE_SAFE"` / `"WRITE_DANGEROUS"` / `"ADMIN"` のいずれか |
| `sse_heartbeat_timeout` / `sse_malformed_retry` / `sse_reconnect_max` | `>= 0` |

| 関数 | 戻り値 | 説明 |
|---|---|---|
| `build_agent_config(cfg_override=None) -> AgentConfig` | `AgentConfig` | `_get_cfg()` を直接参照して `AgentConfig` インスタンスを生成。`cfg_override` を渡すとそちらを使用 (テスト用 DI) |

## 4. DbConfig dataclass

SQLite 接続の不変設定を保持。`build_db_config()` で `_get_cfg()` (= `load_all()` キャッシュ) から生成。注意: `common.toml` は `load_all()` の読み込み対象に含まれないため、`rag_db_path` / `session_db_path` / `sqlite_vec_so` などのキーが他の設定ファイルに存在しない場合は空文字列になり `__post_init__` で `ValueError` が発生する。実運用では `db/helper.py` や `rag/pipeline.py` が `ConfigLoader().load("common.toml")` を個別に呼ぶことでこれらの値を取得している。

```python
@dataclass
class DbConfig:
    rag_db_path: str          # RAG SQLite DB ファイルパス
    session_db_path: str      # Session SQLite DB ファイルパス
    sqlite_vec_so: str        # sqlite-vec 拡張 .so パス
    embed_url: str            # 埋込 API エンドポイント
    sqlite_timeout: int = 30  # SQLite タイムアウト秒数 (デフォルト: 30)
```

`__post_init__` で `rag_db_path` / `session_db_path` / `sqlite_vec_so` / `embed_url` が空でないこと、`sqlite_timeout >= 1` を検証。

| 関数 | 戻り値 | 説明 |
|---|---|---|
| `build_db_config() -> DbConfig` | `DbConfig` | `_get_cfg()` のキャッシュ (= `load_all()` マージ結果) から `DbConfig` インスタンスを生成する |

## 5. モジュールレベル定数

モジュールに残るパス定数は 2 つのみ (他は全て `AgentConfig` フィールドに移行済み)。

| 定数 | 型 | 説明 |
|---|---|---|
| `_SCRIPTS_DIR` | `Path` | scripts/ ディレクトリの絶対パス |
| `_CONFIG_DIR` | `Path` | config/ ディレクトリの絶対パス |

他モジュールがこれらを使う場合は関数スコープ内で `from agent.config import _SCRIPTS_DIR  # noqa: PLC0415` のようにインポートする (CLAUDE.md ルール)。

## 6. 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent/repl.py` | `build_agent_config()` で `AgentConfig` を生成し `ctx.cfg` に保持。`LLMClient` / `ToolExecutor` の初期化パラメータを `ctx.cfg` から取得 |
| `agent/commands/cmd_config.py` | `_apply_config_params()` で `ctx.cfg` フィールドを更新し各コンポーネントに同期。`_cmd_reload()` が呼び出す |
