# agent/config.py

## 1. 機能概要

`config/common.toml` と `config/agent.toml` を遅延ロードし、`AgentREPL` と各コンポーネントが共用する設定 dataclass を提供。

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
    startup_mode: str = "persistent"   # "persistent" | "ondemand"
    healthcheck_mode: str = ""  # "http" | "process" | "ping_tool"; "" = 自動推論
    idle_timeout_sec: int = 0   # ondemand アイドル自動停止まで秒数; 0 = 無効
    working_dir: str = ""       # stdio サブプロセス作業ディレクトリ; "" = 継承
    env: dict[str, str] = field(default_factory=dict)  # stdio サブプロセスに注入する環境変数
    tool_names: list[str] = []  # 明示的ツール名リスト; [] = 静的プレフィックスルーティングに fallback
```

`__post_init__` でバリデーション:
- `transport` は `"http"` または `"stdio"` のみ
- `transport="http"` のとき `url` が空でないこと
- `transport="stdio"` のとき `cmd` が空でないこと
- `startup_mode` は `"persistent"` または `"ondemand"` のみ
- `healthcheck_mode` は `""` / `"http"` / `"process"` / `"ping_tool"` のみ。`""` 指定時はトランスポートから自動推論 (`http` → `"http"`, `stdio` → `"process"`)

**起動モード:**
- `persistent`: エージェント起動時に `_start_stdio_servers()` が即座に `StdioTransport.start()` を呼ぶ。HTTP サーバはプロセス管理不要のため常にこのモードで動作。
- `ondemand`: 初回ツール呼び出し時に `ServerLifecycleManager.ensure_ready()` が起動。並行呼び出しは per-server `asyncio.Lock` + double-checked locking で 1 回のみ起動。

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
    context_char_limit: int          # 会話履歴の圧縮閾値文字数
    context_compress_turns: int      # 1 回の圧縮で要約するターン対数
    context_token_limit: int = 0     # トークンベース監視閾値 (0 = 無効)
    history_protect_turns: int = 2   # 直近 N ターンを圧縮から除外
    budget_warn_ratio: float = 0.8   # 閾値の何割で budget warning を出すか (0, 1]

    # ── RAG ──────────────────────────────────────────────────────────────────
    top_k_search: int                # ベクトル / FTS 検索返却件数
    top_k_rerank: int                # Cross-Encoder に渡す候補件数
    rag_top_k: int                   # LLM コンテキスト追加チャンク数上限
    use_mqe: bool                    # MQE 有効フラグ
    use_search: bool                 # RAG 検索有効フラグ
    use_rrf: bool                    # RRF マージ有効フラグ
    use_rerank: bool                 # Cross-Encoder 再ランク有効フラグ
    rag_min_score: float             # Rerank スコア閾値 (0–10); 未満チャンクを除外
    max_chunks_per_doc: int          # 同一ドキュメントから取得する最大チャンク数
    use_two_stage_fetch: bool        # 二段階取得有効フラグ
    two_stage_max_docs: int          # 二段階取得で全文展開するドキュメント数上限
    use_semantic_cache: bool         # True のとき RAG 結果をセマンティックキャッシュ
    semantic_cache_threshold: float  # セマンティックキャッシュのコサイン類似度閾値 (0–1)
    semantic_cache_max_size: int     # セマンティックキャッシュの最大エントリ数 (FIFO)
    use_refiner: bool                # True のとき Rerank 後チャンクを LLM で圧縮
    refiner_max_tokens: int          # Refiner LLM の最大生成トークン数
    refiner_timeout: float           # Refiner LLM の HTTP タイムアウト秒数
    refiner_max_chars_per_chunk: int # Refiner に渡す 1 チャンクの最大文字数
    rag_service_url: str = ""        # 外部 RAG HTTP サービス URL (空文字 = in-process)

    # ── LLM ──────────────────────────────────────────────────────────────────
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
    tool_cache_ttl: float                      # ツール結果キャッシュ有効期間 (秒)
    tool_cache_max_size: int = 200             # キャッシュ最大エントリ数 (LRU); 0 = 無制限
    serial_tool_calls: bool                    # True のとき tool_calls を直列実行
    auto_inject_notes: bool                    # True のとき起動時に全ノートをシステムプロンプトへ注入
    use_tool_summarize: bool                   # True のとき長いツール結果を LLM 要約
    tool_summarize_threshold: int              # 要約対象の文字数下限
    tool_definitions_strict: bool              # True のとき agent.toml と /v1/tools 差分で起動中止
    tool_definitions: list[dict] = field(...)  # agent.toml から読み込むツール定義
    tool_result_max_llm_chars: int = 8000      # ツール結果を LLM コンテキストに追加する文字数上限
    tool_results_turn_max_chars: int = 50000   # 1 ターン内の全ツール結果合計文字数上限
    masked_fields: list[str]                   # コンソール表示でマスクするツール引数フィールド名
    plan_blocked_tools: list[str]              # plan_mode 中にブロックするツール名リスト
    tool_concurrency_limits: dict[str, int] = field(default_factory=dict)
                                               # サーバキー → 最大同時呼び出し数 (Semaphore)

    # ── ツールループガード ─────────────────────────────────────────────────────
    tool_dedup_max_repeats: int    # 同一 (name, args) が何回目で dedup ヒント注入するか
    tool_cycle_detect_window: int  # 循環プランニング検出ウィンドウ (round 数); 0 = 無効
    tool_error_max_consecutive: int # 全エラーターンが何回連続したらループ脱出するか
    tool_error_retry_max: int = 1  # このターンですでにエラーになった (name, args) の retry 上限

    # ── プロンプト・セッション ─────────────────────────────────────────────────
    system_prompts: dict[str, str] = field(default_factory=dict)  # /system プレセット辞書
    system_prompt_tool: str = ""
    max_tool_turns: int = 5        # 1 メッセージあたりの最大ツール呼び出しターン数

    # ── MCP サーバ ────────────────────────────────────────────────────────────
    mcp_watchdog_interval: float   # MCP 死活監視間隔 (秒); 0 で無効
    mcp_watchdog_max_restarts: int # ウォッチドッグの最大再起動回数
    mcp_servers: dict[str, McpServerConfig] = field(default_factory=dict)

    # ── 承認ルール (risk-based approval) ────────────────────────────────────
    approval_risk_rules: dict[str, str] = field(default_factory=dict)
                                   # ツール名 → "none" | "medium" | "high"
                                   # 未登録ツールは tool_safety_tiers にフォールバック
    approval_protected_paths: list[str] = field(default_factory=list)
                                   # high risk にエスカレートするファイルパスプレフィックス
    approval_high_risk_branches: list[str] = field(default_factory=list)
                                   # 書き込み操作を high risk にするブランチ名リスト
    approval_shell_safe_prefixes: list[str] = field(default_factory=list)
                                   # shell_run で自動承認とみなすコマンド先頭文字列
    approval_resource_keys: dict[str, list[str]] = field(default_factory=dict)
                                   # {"path_keys": [...], "branch_keys": [...]}
    approval_dry_run_tools: list[str] = field(default_factory=list)
                                   # 承認前に dry_run プレビューを自動実行するツール名

    # ── ツール安全性強化 ─────────────────────────────────────────────────────
    tool_safety_tiers: dict[str, str] = field(default_factory=dict)
                                   # ツール名 → "READ_ONLY" | "WRITE_SAFE" | "WRITE_DANGEROUS" | "ADMIN"
                                   # approval_risk_rules が優先。未登録は WRITE_DANGEROUS (Fail-Safe)
    allowed_root: str = ""         # ファイルパス引数の許可ルートパス。空文字列でチェック無効
    approval_github_allowed_repos: list[str] = field(default_factory=list)
                                   # GitHub 書き込み許可リポジトリ (owner/repo)。空=Fail-Closed

    # ── メモリ・OTel ─────────────────────────────────────────────────────────
    use_memory_layer: bool = False
    otel_enabled: bool = False
    otel_endpoint: str = ""
    otel_service_name: str = "llm-agent"
    audit_log_file: str = "/opt/llm/logs/audit.log"
    structured_log: bool = False

    # ── SSE ストリーム堅牢化 ───────────────────────────────────────────────────
    sse_heartbeat_timeout: float = 30.0              # 無通信 timeout 秒 (0 で無効)
    sse_malformed_retry: int = 2                     # malformed chunk の許容回数
    sse_reconnect_max: int = 1                       # in_stream 切断後の最大再接続回数
    llm_stream_retry_on_heartbeat_timeout: bool = True
    llm_stream_retry_on_malformed_chunk: bool = False
```

`__post_init__` で値域バリデーションを実施。違反時は `ValueError` を送出。

| フィールド | バリデーション条件 |
|---|---|
| `context_char_limit` | `>= 0` |
| `budget_warn_ratio` | `(0.0, 1.0]` |
| `top_k_search` / `top_k_rerank` / `rag_top_k` | `>= 1` |
| `llm_max_retries` | `>= 0` |
| `llm_retry_base_delay` | `> 0` |
| `rag_min_score` | `>= 0.0` |
| `max_chunks_per_doc` / `two_stage_max_docs` | `>= 1` |
| `llm_temperature` | `[0.0, 2.0]` |
| `llm_max_tokens` | `>= 1` |
| `refiner_max_tokens` | `>= 1` |
| `refiner_timeout` | `> 0` |
| `refiner_max_chars_per_chunk` | `>= 1` |
| `tool_dedup_max_repeats` | `>= 1` |
| `approval_risk_rules` の値 | `"none"` / `"medium"` / `"high"` のいずれか |
| `sse_heartbeat_timeout` / `sse_malformed_retry` / `sse_reconnect_max` | `>= 0` |

| 関数 | 戻り値 | 説明 |
|---|---|---|
| `build_agent_config(cfg_override=None) -> AgentConfig` | `AgentConfig` | `_get_cfg()` を直接参照して `AgentConfig` インスタンスを生成。`cfg_override` を渡すとそちらを使用 (テスト用 DI) |

## 4. DbConfig dataclass

SQLite 接続の不変設定を保持。`build_db_config()` で `common.toml` から生成。

```python
@dataclass
class DbConfig:
    rag_db_path: str      # RAG SQLite DB ファイルパス
    session_db_path: str  # Session SQLite DB ファイルパス
    sqlite_vec_so: str    # sqlite-vec 拡張 .so パス
    embed_url: str        # 埋込 API エンドポイント
    sqlite_timeout: int = 30  # SQLite タイムアウト秒数
```

`__post_init__` で `rag_db_path` / `sqlite_vec_so` / `embed_url` が空でないこと、`sqlite_timeout >= 1` を検証。

| 関数 | 戻り値 | 説明 |
|---|---|---|
| `build_db_config() -> DbConfig` | `DbConfig` | `common.toml` から `DbConfig` インスタンスを生成する |

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
