# agent_config.py

## 1. 機能概要

`config/common.json` と `config/agent.json` を import 時に一括ロードし、`AgentREPL` と `CommandRegistry` が共用するモジュールレベル定数を提供。定数を 1 ファイルに集約することで循環 import を回避。

ホットリロード対象パラメータは `AgentConfig` dataclass に集約。`build_agent_config()` は `_get_cfg()` を直接参照して `AgentConfig` インスタンスを生成するため、モジュールレベル定数とは独立しており、テスト時に `_get_cfg()` をモックするだけで設定を差し替え可能。`AgentREPL._cfg` として保持され、`/reload` コマンドはフィールドをその場で更新。

遅延ロードパターン: `_cfg: dict | None = None` → `_get_cfg()` 関数（try/except 付き）でキャッシュ。モジュールレベル定数は後方互換維持のために `_get_cfg()` を import 時に呼び出すが、`build_agent_config()` はそれらに依存しない。MCP サーバ (`FileopMCPServer`, `GithubMCPServer`, `WebSearchMCPServer`) でも同じパターンを採用し、Pydantic スキーマ定義に必要な定数のみを module スコープに残して他はインライン / 遅延プロキシに移行している。

## 2. McpServerConfig dataclass

1 台の MCP サーバのトランスポート設定を保持。`_build_mcp_servers()` が `agent.json` の `mcp_servers` セクションから構築。

```python
@dataclass
class McpServerConfig:
    transport: str        # "http" | "stdio"
    url: str              # HTTP ベース URL (transport="http" 時に使用)
    cmd: list[str]        # サブプロセス起動コマンド (transport="stdio" 時に使用)
    openrc_service: str   # ウォッチドッグが再起動に使う OpenRC サービス名 (例: "file-mcp")
```

`__post_init__` でバリデーション:
- `transport` は `"http"` または `"stdio"` のみ
- `transport="http"` のとき `url` が空でないこと
- `transport="stdio"` のとき `cmd` が空でないこと

| 関数 | 戻り値 | 説明 |
|---|---|---|
| `_build_mcp_servers(cfg) -> dict[str, McpServerConfig]` | `dict` | `agent.json` の `mcp_servers` セクションから構築。キー: `"web_search"` / `"file"` / `"github"` 等。`mcp_servers` セクションがない場合は旧来の URL 定数からフォールバック生成 |

## 3. AgentConfig dataclass

ホットリロード対象のランタイム設定を一元管理。`/reload` コマンドがフィールドをその場で更新。

```python
@dataclass
class AgentConfig:
    context_char_limit: int         # 会話履歴の圧縮閾値文字数
    context_compress_turns: int     # 1 回の圧縮で要約するターン対数
    tool_cache_ttl: float           # ツール結果キャッシュ有効期間 (秒)
    top_k_search: int               # ベクトル / FTS 検索返却件数
    top_k_rerank: int               # Cross-Encoder に渡す候補件数
    rag_top_k: int                  # LLM コンテキスト追加チャンク数上限
    use_mqe: bool                   # MQE 有効フラグ
    use_search: bool                # RAG 検索有効フラグ
    use_rrf: bool                   # RRF マージ有効フラグ
    use_rerank: bool                # Cross-Encoder 再ランク有効フラグ
    llm_max_retries: int            # LLM リトライ回数
    llm_retry_base_delay: float     # 指数バックオフ基本待機秒数
    rag_min_score: float            # Rerank スコア閾値 (0–10); 未満チャンクを除外
    max_chunks_per_doc: int         # 同一ドキュメントから取得する最大チャンク数
    use_two_stage_fetch: bool       # 二段階取得有効フラグ
    two_stage_max_docs: int         # 二段階取得で全文展開するドキュメント数上限
    serial_tool_calls: bool         # True のとき tool_calls を直列実行 (write→read 依存用)
    auto_inject_notes: bool         # True のとき起動時に全ノートをシステムプロンプトへ注入
    use_tool_summarize: bool        # True のとき長いツール結果を LLM 要約してから追加
    tool_summarize_threshold: int   # 要約対象の文字数下限
    use_semantic_cache: bool        # True のとき RAG 結果をセマンティックキャッシュ
    semantic_cache_threshold: float # セマンティックキャッシュのコサイン類似度閾値 (0–1)
    semantic_cache_max_size: int    # セマンティックキャッシュの最大エントリ数 (FIFO)
    tool_definitions_strict: bool   # True のとき agent.json と /v1/tools 差分で起動中止
    mcp_watchdog_interval: float    # MCP 死活監視間隔 (秒); 0 で無効
    mcp_watchdog_max_restarts: int  # ウォッチドッグの最大再起動回数
    require_approval_tools: list[str]  # 実行前に y/N 確認を要求するツール名リスト
    masked_fields: list[str]        # コンソール表示でマスクするツール引数フィールド名
    plan_blocked_tools: list[str]   # plan_mode 中にブロックするツール名リスト
    llm_temperature: float          # メイン LLM 生成温度 (0.0–2.0)
    llm_max_tokens: int             # メイン LLM 最大生成トークン数 (>= 1)
    use_refiner: bool               # True のとき Rerank 後チャンクを LLM で圧縮
    refiner_max_tokens: int         # Refiner LLM の最大生成トークン数
    refiner_timeout: float          # Refiner LLM の HTTP タイムアウト秒数
    refiner_max_chars_per_chunk: int # Refiner に渡す 1 チャンクの最大文字数
    mcp_servers: dict[str, McpServerConfig]  # サーバキー → トランスポート設定
```

`__post_init__` で値域バリデーションを実施。違反時は `ValueError` を送出。

| フィールド | バリデーション条件 |
|---|---|
| `context_char_limit` | `>= 0` |
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

| 関数 | 戻り値 | 説明 |
|---|---|---|
| `build_agent_config() -> AgentConfig` | `AgentConfig` | `_get_cfg()` を直接参照して `AgentConfig` インスタンスを生成。モジュールレベル定数に依存しないためテスト/DI に対応 |

## 4. DbConfig dataclass

SQLite 接続と埋込サービス URL の不変設定を保持。`build_db_config()` で `common.json` から生成。

```python
@dataclass
class DbConfig:
    db_path: str          # SQLite DB ファイルパス
    sqlite_vec_so: str    # sqlite-vec 拡張 .so パス
    embed_url: str        # 埋込 API エンドポイント
    sqlite_timeout: int   # SQLite タイムアウト秒数 (デフォルト: 30)
```

`__post_init__` で `db_path` / `sqlite_vec_so` / `embed_url` が空でないこと、`sqlite_timeout >= 1` を検証。

| 関数 | 戻り値 | 説明 |
|---|---|---|
| `build_db_config() -> DbConfig` | `DbConfig` | `common.json` から `DbConfig` インスタンスを生成する |

## 5. エクスポートされる静的定数

| 定数 | 型 | 説明 |
|---|---|---|
| `CHAT_URL` | `str` | チャット LLM エンドポイント (gemma-4-e4b :8002) |
| `CODE_URL` | `str` | コーディング LLM エンドポイント (qwen2.5-coder-7b :8001) |
| `WEB_SEARCH_URL` | `str` | Web 検索 MCP サーバのベース URL |
| `FILE_SERVER_URL` | `str` | file-mcp サーバのベース URL |
| `GITHUB_URL` | `str` | github-mcp サーバのベース URL |
| `HTTP_TIMEOUT` | `float` | httpx.AsyncClient タイムアウト秒数 |
| `SYSTEM_PROMPT_TOOL` | `str` | デフォルトのシステムプロンプト文字列 |
| `WEB_SEARCH_MAX_RESULTS` | `int` | Web 検索の最大結果件数 |
| `MAX_TOOL_TURNS` | `int` | 1 メッセージあたりのツール呼び出し最大ターン数 |
| `TOP_K_SEARCH` | `int` | ベクトル / FTS 検索それぞれの返却件数 |
| `TOP_K_RERANK` | `int` | Cross-Encoder Rerank に渡す候補件数 |
| `DEFAULT_MODE` | `str` | 起動時 LLM モード (`"chat"` / `"code"`) |
| `CONTEXT_CHAR_LIMIT` | `int` | 会話履歴の圧縮閾値文字数 |
| `CONTEXT_COMPRESS_TURNS` | `int` | 1 回の圧縮で要約する turn 対数 |
| `BUDGET_WARN_RATIO` | `float` | LLM 入力文字数が `context_char_limit` のこの割合を超えたとき `logger.warning` で内訳付き警告を出力 (デフォルト: 0.8) |
| `TOOL_CACHE_TTL` | `float` | ツール結果キャッシュの有効期間 (秒) |
| `LLM_MAX_RETRIES` | `int` | LLM リクエスト指数バックオフリトライ回数 |
| `LLM_RETRY_BASE_DELAY` | `float` | 指数バックオフの基本待機秒数 |
| `RAG_TOP_K` | `int` | LLM コンテキストに追加するチャンク数上限。`agent.json` の `rag_top_k` で設定可能 (デフォルト: 5) |
| `TOOL_RESULT_MAX_LLM_CHARS` | `int` | ツール実行結果の LLM コンテキスト追加時の文字数上限。`agent.json` の `tool_result_max_llm_chars` で設定可能 (デフォルト: 8000) |
| `SYSTEM_PROMPTS` | `dict[str, str]` | `/system` コマンド用プレセット辞書 |
| `TOOL_DEFINITIONS` | `list[dict]` | HTTP モード時のツール定義リスト |
| `_USE_MQE` / `_USE_SEARCH` / `_USE_RRF` / `_USE_RERANK` | `bool` | RAG パイプライン各ステップ有効フラグ |
| `_SCRIPTS_DIR` | `Path` | scripts/ ディレクトリの絶対パス |
| `_CONFIG_DIR` | `Path` | config/ ディレクトリの絶対パス |

## 6. 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `agent_repl.py` | モジュールレベルで全定数を import。`AgentConfig` / `build_agent_config` を import して `self._cfg` に保持 |
| `agent_commands.py` | `CommandRegistry` で参照する定数のみ import。`_cmd_reload()` で `self._cfg` フィールドを更新 |
