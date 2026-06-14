# エージェント仕様

## 1. 目的

LLM エージェント REPL（Read-Eval-Print Loop）として、ユーザーの自然言語入力を受け取り、RAG コンテキスト取得・ツール呼び出し・LLM 推論を統合的に処理し、応答を返す。セッション間の会話履歴・メモリ・ノートを永続化する。

---

## 2. スコープ

- **対象コンポーネント:** `agent/` 配下の全モジュール（REPL、Orchestrator、Config、Context、Session、History、Commands、Memory）
- **対象外:** MCP サーバー実装（`mcp/`）、RAG パイプライン実装（`rag/`）、DB 永続化層（`db/`）、共有ライブラリ（`shared/`）

---

## 3. 背景

現行システムは HTTP および stdio (Subprocess) の両方の転送方式で MCP サーバー群を呼び出す単一エージェント REPL 構成である。ユーザーは CLI から直接操作し、コードレビュー・ドキュメント参照・ファイル操作・Git 操作などを自然言語で指示できる。セッション履歴は SQLite に永続化される。

---

## 4. 前提条件

1. Python 3.13、uv による仮想環境（`.venv/`）が構築済みであること。
2. LLM サーバー（llama.cpp）がポート 8001（コード生成）・8002（チャット）で起動済みであること。
3. 埋め込みサーバーがポート 8003 で起動済みであること。
4. SQLite データベース（`rag.sqlite`・`session.sqlite`）が初期化済みであること。
5. MCP サーバー群（ポート 8004〜8014）が起動済みであること。

---

## 5. 制約

| 制約 | 内容 |
|---|---|
| コンテキスト上限 | `context_char_limit`（デフォルト 8000 文字）を超えると自動圧縮 |
| ツールターン上限 | `max_tool_turns`（デフォルト 5）でツールループを打ち切り |
| 連続エラー上限 | `tool_error_max_consecutive`（デフォルト 3）でツールエラーループを中断 |
| LLM リトライ上限 | `llm_max_retries`（デフォルト 3）、指数バックオフ（base_delay × 2^n） |
| 履歴圧縮 | `context_compress_turns`（デフォルト 4）ターン分を LLM 要約に置換 |
| 承認フロー | `approval_risk_rules` に基づく高リスクツールはユーザー確認が必要 |
| 並行性 | asyncio シングルスレッド；ツール実行は `serial_tool_calls=true` で直列化可能 |

---

## 6. 機能要件

### 6.1 REPL 基本機能
- ユーザー入力の受付（readline、複数行入力は行末 `\` で継続）
- LLM へのメッセージ送信とストリーミングレスポンス表示
- スラッシュコマンド（23 種）の処理
- セッション開始・終了・切り替え

### 6.2 ツール呼び出し機能
- OpenAI 互換 function calling によるツール選択
- MCP サーバーへのディスパッチ（`ToolExecutor` 経由）
- 結果キャッシュ（TTL: `tool_cache_ttl` 秒、デフォルト 300 秒）
- 承認フロー（リスクレベルに応じたユーザー確認）
- DAG 実行（`use_tool_dag=true` で write-before-read 順序保証）

### 6.3 RAG 統合
- 各ターンで `RagPipeline.augment()` を呼び出しコンテキストをメッセージに付加
- `use_search=false` で無効化可能

### 6.4 メモリ層
- セマンティックメモリ（ルール・方針）とエピソードメモリ（会話履歴）の二層構造
- `use_memory_layer=true` で有効化
- セッション終了時に `on_session_stop()` で自動抽出・保存

### 6.5 セッション永続化
- SQLite の `sessions`・`messages` テーブルに全会話を保存
- `/session load <id>` で過去セッションの復元

### 6.6 ノート管理
- `/note add|list|delete|pin|unpin|search` でセッション間永続の固定知識を管理
- `auto_inject_notes=true`（デフォルト）で起動時にピン留めノートをシステムプロンプトに注入 + ターン毎に検索マッチノートを注入

---

## 7. 入出力

### 7.1 ユーザー入力
- 通常テキスト入力（自然言語プロンプト）
- スラッシュコマンド（`/help`、`/session list` 等）
- 複数行入力（行末 `\` で継続）

### 7.2 LLM へのリクエスト
```json
{
  "model": "...",
  "messages": [{"role": "system", ...}, {"role": "user", ...}, ...],
  "tools": [...],
  "temperature": 0.2,
  "max_tokens": 1024,
  "stream": true
}
```

### 7.3 LLM からのレスポンス
- SSE ストリーム（`data: {...}` 形式）
- `tool_calls` フィールドにツール呼び出し情報が含まれる場合あり

### 7.4 ツール実行結果
- `execute_one_tool_call()` は `(tc_id, name, args, full_text, is_error, llm_text)` の6要素タプルを返す (tool_runner.py:40-86)

---

## 8. 処理フロー

```
[起動]
  agent.py → AgentREPL.__init__() → build_agent_context()
                                  → _start_subprocess_servers()
                                  → _check_services()
                                  → _setup_initial_prompt()

[1ターンの処理]
  ユーザー入力
    → Orchestrator.handle_turn(line: str) -> None (repl.py:180, orchestrator.py:74)
      → _handle_memory_injection() (memory snippet を history に注入)
      → _append_user_message() (system prompt sync + user message 追加)
      → _handle_history_compression() (コンテキスト上限超過時)
        → tuple[list[LLMMessage], CompressResult] を返す
      → _handle_llm_turn() via LLMTurnRunner.run(llm_url) (orchestrator.py:142)
        → LLMClient.stream() [SSEストリーミング]
        → tool_calls あり？
            Yes → run_approval_checks() → execute_all_tool_calls()
                → ToolLoopGuard で cycle/dedup/retry/error 制限 (tool_loop_guard.py:49)
                → ループ (max_tool_turns まで)
            No  → 最終応答を表示・DB 保存

※ RAG augment は仕様 (§6.3, §8) で定義されているが、エージェントターンでは呼ばれていない。

[セッション終了]
  MemoryIngestionService.on_session_stop() (use_memory_layer=true の場合)
  lifecycle.shutdown_all()
```

---

## 9. データ仕様

### 9.1 AgentConfig サブ設定

AgentConfig は 7 つのサブ config を compose する構造（`config.py:401-415`）。`cfg.llm.llm_url` のようにネストしてアクセスする。

| サブ設定 | 主要フィールド |
|---|---|
| `LLMConfig` | `llm_url`, `http_timeout=30.0`, `llm_retry_base_delay=1.0`, `llm_max_retries=3`, `llm_temperature=0.2`, `llm_max_tokens=1024`, `title_llm_temperature`, `title_llm_max_tokens`, `context_char_limit=8000`, `context_compress_turns=4`, `context_token_limit=0`, `tokenize_url`, `sse_heartbeat_timeout`, `sse_malformed_retry`, `sse_reconnect_max`, `llm_stream_retry_on_heartbeat_timeout`, `llm_stream_retry_on_malformed_chunk`, `history_protect_turns`, `budget_warn_ratio` |
| `RAGConfig` | `top_k_search=10`, `top_k_rerank=15`, `max_chunks_per_doc=2`, `embed_url`, `use_semantic_cache=False`, `semantic_cache_threshold`, `semantic_cache_max_size`, `web_search_url`, `web_search_max_results`, `refiner_max_tokens`, `refiner_timeout`, `refiner_max_chars_per_chunk`, `use_refiner=False` |
| `ToolConfig` | `tool_cache_ttl=300.0`, `tool_cache_max_size=200`, `serial_tool_calls=False`, `auto_inject_notes=True`, `use_tool_summarize=False`, `tool_summarize_threshold=3000`, `tool_definitions_strict=False`, `tool_dedup_max_repeats=3`, `tool_cycle_detect_window=2`, `tool_error_max_consecutive=3`, `tool_error_retry_max=1`, `tool_concurrency_limits={}`, `masked_fields=["file_content"]`, `plan_blocked_tools=["write_file","create_directory","delete_file","delete_directory"]`, `max_tool_turns=5`, `tool_result_max_llm_chars=8000`, `tool_results_turn_max_chars=50000`, `use_tool_dag=False`, `tool_definitions=[]`, `system_prompts={}`, `system_prompt_tool=""`, `allowed_tools=[]` |
| `MemoryConfig` | `use_memory_layer=False`, `memory_jsonl_dir`, `memory_max_inject_semantic=5`, `memory_max_inject_episodic=3`, `memory_embed_enabled=False`, `memory_embed_dim=384`, `memory_min_importance`, `memory_dedup_threshold`, `memory_max_content_chars`, `memory_embed_timeout_sec`, `memory_retention_days`, `memory_fts_limit=50`, `memory_rrf_k=60`, `memory_recency_days=7.0` |
| `MCPConfig` | `mcp_servers={}`, `mcp_watchdog_interval=0.0`, `mcp_watchdog_max_restarts=3`, `github_url` |
| `ApprovalConfig` | `approval_risk_rules`, `approval_protected_paths`, `approval_high_risk_branches`, `approval_github_allowed_repos=[]`, `approval_shell_safe_prefixes`, `approval_resource_keys`, `approval_dry_run_tools`, `tool_safety_tiers`, `allowed_root`, `gitops_push_blocked=False`, `gitops_force_push_blocked=True`, `gitops_protected_branches` |
| `ObservabilityConfig` | `otel_enabled=False`, `otel_endpoint`, `otel_service_name="llm-agent"`, `audit_log_file`, `structured_log=False` |

※ `_cfg` モジュール変数と `_get_cfg()` キャッシュは削除された。`load_config()` は毎回 `ConfigLoader().load_all()` を呼ぶ。

### 9.2 ConversationState / TurnState

```python
@dataclass
class ConversationState:
    history: list[LLMMessage]           # 会話履歴
    llm_url: str                        # LLM エンドポイント
    debug_mode: bool                    # デバッグモード
    plan_mode: bool                     # プランモード
    system_prompt_name: str             # システムプロンプト名 (default="default")
    system_prompt_content: str          # システムプロンプト本文
    shutdown_requested: bool            # シャットダウン要求フラグ

@dataclass
class TurnState:
    current_turn_id: str | None         # UUID4; Orchestrator.handle_turn() で設定
    background_tasks: set[asyncio.Task] # このターン中に生成されたバックグラウンドタスク
    last_error_kind: str | None         # 直近のターン失敗の原因種別
```

※ `session_id` は ConversationState に含まれない。`ctx.session.session_id` でアクセスする。

### 9.3 LLMMessage (TypedDict)

```python
class LLMMessage(TypedDict, total=False):
    role: Literal["user", "assistant", "tool", "system"]
    content: str | None
    tool_calls: list[dict]
    tool_call_id: str
    name: str
    importance: float   # 圧縮スコアリング用 (0.0〜1.0)
    pinned: bool        # 圧縮防止フラグ
```

### 9.4 MemoryEntry フィールド

| フィールド | 型 | 説明 |
|---|---|---|
| `memory_id` | str | UUID |
| `memory_type` | `MemoryType` (StrEnum) | `MemoryType.SEMANTIC` / `MemoryType.EPISODIC`; str との等値比較可 |
| `source_type` | `SourceType` (StrEnum) | `conversation`, `rule`, `decision`, `failure`（`memory/types.py` 定義） |
| `session_id` | int \| None | 生成元セッション |
| `turn_id` | str \| None | 生成元ターンID |
| `project` | str | プロジェクト名 |
| `repo` | str | リポジトリ名 |
| `branch` | str | ブランチ名 |
| `content` | str | 本文 |
| `summary` | str | 要約 |
| `tags` | list[str] | タグリスト |
| `importance` | float | 0.0〜1.0 |
| `pinned` | bool | 常時保持フラグ |
| `created_at` | str | ISO-8601 UTC（デフォルト `""`、`MemoryStore.add()` が書き込み） |
| `updated_at` | str | ISO-8601 UTC（デフォルト `""`、同上） |

※ `MemoryEntry` は `@dataclass(frozen=True)` で定義される (`memory/types.py:44`)。

### 9.5 メモリ層 DTO（memory/models.py）

```python
@dataclass(frozen=True)
class MemorySnippet:       # LLM コンテキスト注入用スニペット（injection.py/services.py の戻り値）
    text: str              # 整形済み文字列（"[Semantic memory] ..." 等のプレフィックス含む）
    source: str = ""       # "semantic" または "episodic"
    score: float = 0.0

@dataclass(frozen=True)
class InjectionSnippet:    # injection.py 内部用（外部には MemorySnippet を公開）
    prefix: str
    text: str
    memory_id: str
    memory_type: str

@dataclass(frozen=True)
class ConsistencyReport:   # memories / memories_fts / memories_vec の行数レポート
    memories: int
    fts: int
    vec: int

@dataclass(frozen=True)
class EmbeddingRequest:    # 埋め込みサービスへの入力
    text: str
    query_prefix: str

@dataclass(frozen=True)
class EmbeddingResponse:   # 埋め込みサービスからのレスポンス
    embedding: list[float]
    model: str | None = None

@dataclass(frozen=True)
class HistoryMessage:      # メモリ層が使用する会話メッセージ表現
    role: str
    content: str

@dataclass(frozen=True)
class JsonlRecord:         # JSONL ストアからの 1 行分デシリアライズ結果
    memory_id: str
    memory_type: str
    source_type: str
    session_id: int | None
    turn_id: str | None
    project: str
    repo: str
    branch: str
    content: str
    summary: str
    tags: list[str]
    importance: float
    pinned: bool
    created_at: str
    updated_at: str
```

### 9.6 メモリ層列挙型

**memory/enums.py:**

| 列挙型 | 値 | 説明 |
|---|---|---|
| `MemoryType` (StrEnum) | `SEMANTIC`, `EPISODIC` | メモリ種別 |
| `RetrievalMode` (StrEnum) | `FTS`, `KNN`, `HYBRID` | 検索モード |
| `ExtractionDecision` (StrEnum) | `ACCEPT`, `REJECT_TOO_SHORT`, `REJECT_NO_KEYWORDS`, `REJECT_DEDUP` | 抽出判断結果 |

**memory/types.py:**

| 列挙型 | 値 | 説明 |
|---|---|---|
| `SourceType` (StrEnum) | `CONVERSATION`, `DECISION`, `RULE`, `FAILURE` | メモリ生成元種別 |
| `EmbeddingErrorKind` (StrEnum) | `DISABLED`, `CIRCUIT_OPEN`, `TIMEOUT`, `HTTP_ERROR`, `INVALID_RESPONSE`, `UNKNOWN_ERROR` | 埋め込み失敗理由 |

---

## 10. 公開インターフェース仕様

### 10.1 AgentREPL

```python
class AgentREPL:
    async def run() -> None
    # 起動エントリーポイント。REPL ループを開始する。
```

### 10.2 Orchestrator

```python
class Orchestrator:
    def __init__(ctx: AgentContext, *, allowed_tools: list[str] | None = None, on_turn_start, on_turn_end, on_error, on_first_turn, tracer) -> None
    # allowed_tools は init 時に self._allowed_tools として保存され、_process_turn() で一時的に適用される
    async def handle_turn(line: str) -> None
    # TurnResult を返さない。side effects (DB save, callbacks) で結果を出力する
```

※ `allowed_tools` はコンストラクタで受け取り `self._allowed_tools` として保持 (§47-59)。`handle_turn()` の引数ではない (§74)。

### 10.3 HistoryManager

```python
class HistoryManager:
    def compress(history: list[LLMMessage]) -> tuple[list[LLMMessage], CompressResult]
    def force_compress(history: list[LLMMessage]) -> tuple[list[LLMMessage], CompressResult]
    # CompressResult: namedtuple(compressed_count, protected_count, summary_added)
    def count_chars(history: list[LLMMessage]) -> int
    def count_tokens(history: list[LLMMessage], last_input_tokens: int | None = None) -> int
    # count_tokens: last_input_tokens 指定時はその値をそのまま返す（chars//4 推定をスキップ）
    def count_tokens_async(history, last_input_tokens) -> tuple[int, bool]
    # 非同期版: (token_count, is_exact) を返す
    def apply_config(char_limit, compress_turns, token_limit, tokenize_url) -> None
    # 設定のホットリロード
    @property
    def compress_turns: int
    # 圧縮対象ターン数
```

※ `compress()` / `force_compress()` は `list[LLMMessage]` のみを返さず、`tuple[list[LLMMessage], CompressResult]` を返す。

### 10.4 CommandRegistry (スラッシュコマンド)

実装は 23 種 (`commands/registry.py:67-209`)。主要コマンド一覧:

| コマンド | 説明 |
|---|---|
| `/help` | コマンド一覧 |
| `/config [key]` | 設定表示 |
| `/stats` | セッション統計（ステップ別レイテンシは "llm" のみ表示） |
| `/context [new]` | コンテキスト利用状況 |
| `/plan` | プランモード切り替え |
| `/undo` | 直前メッセージの取り消し |
| `/reload` | 設定ファイル再読み込み（`ConfigReloadService.apply_config_dict()` 経由） |
| `/compact` | 強制履歴圧縮（`force_compress()` 使用） |
| `/mcp [status\|install]` | MCP サーバー状態確認・テンプレート生成 |
| `/session list\|load\|rename\|delete [id]` | セッション管理 |
| `/clear [new]` | 会話リセット |
| `/ingest <url\|path>` | ドキュメント取り込み |
| `/rag search <query>` | RAG 検索（未実装の augment とは別） |
| `/export [md\|json] [file]` | 会話エクスポート |
| `/history [n]` | 会話履歴表示 |
| `/system [name]` | システムプロンプト切替 |
| `/db stats\|urls\|clean\|rebuild-fts` | DB 操作（`/db urls` は URL・Lang・Chunks・Fetched・Strategy の 5 列を表示） |
| `/note add\|list\|delete\|pin\|unpin\|search` | ノート管理（ピン留めノートはセッション開始時に注入、`search` はターン毎の類似検索） |
| `/tool [filter]` | ツール情報 |
| `/set temperature\|max_tokens <value>` | LLM パラメータ上書き |
| `/memory list\|search\|show\|pin\|delete\|prune` | メモリ層管理 |
| `/debug` | デバッグモード切り替え |
| `/exit` | 終了 |

※ `/rag`, `/history`, `/system` は仕様当初は未記載だったが実装済み。

### 10.5 MemoryServices

MemoryLayer 廃止後の memory サブサービスコンテナ。`AppServices.memory: MemoryServices | None`。

```python
class MemoryServices:
    # regular class (not @dataclass), defined in memory/services.py:16
    injection: MemoryInjectionService   # on_session_start / on_user_prompt
    ingestion: MemoryIngestionService   # on_session_stop / write_semantic / write_episodic
    store: MemoryStore                  # CRUD (get_by_id / pin / unpin / delete / count_*)
    retriever: HybridRetriever          # search / top_semantic / knn_search

# convenience methods (memory/services.py)
mem.on_session_start(session_id) -> list[MemorySnippet]
await mem.on_session_stop(session_id, history, turn_id) -> None
await mem.on_user_prompt(query, session_id) -> list[MemorySnippet]

# ライフサイクルフック（sub-service 経由）
mem.injection.on_session_start() -> list[MemorySnippet]
await mem.injection.on_user_prompt(query, session_id) -> list[MemorySnippet]
await mem.ingestion.on_session_stop(session_id, history, turn_id) -> None
# 手動書き込み
await mem.ingestion.write_semantic(session_id, content) -> None
await mem.ingestion.write_episodic(session_id, content) -> None
# ストア操作
mem.store.get_by_id(memory_id) -> MemoryEntry | None
mem.store.pin(memory_id) / mem.store.unpin(memory_id) -> bool
mem.store.delete(memory_id) -> bool
mem.store.count_entries() -> int
mem.store.count_prunable(days) -> int
# 追加のストア操作 (store.py)
mem.store.clear_by_session(session_id) -> int
mem.store.search_by_type(memory_type, limit, min_importance) -> list[MemoryEntry]
mem.store.count_by_type() -> dict[str, int]
mem.store.count_vec() -> int
mem.store.check_consistency() -> ConsistencyReport
# 検索
mem.retriever.search(query, embedding=None) -> list[MemoryHit]
```

※ `orchestrator.py:111` では `ctx.services.memory.on_user_prompt()` (convenience method 経由) が使われている。

### 10.6 NoteRepository（agent/note_repo.py）

```python
class NoteRepository:
    def add_note(content: str) -> int             # 戻り値: note_id
    def list_notes() -> list[dict]                # note_id, content, created_at, pinned
    def delete_note(note_id: int) -> bool
    def pin_note(note_id: int) -> bool
    def unpin_note(note_id: int) -> bool
    def get_pinned_notes() -> list[dict]          # pinned=1 のノートのみ
    def search_notes(query: str, limit: int = 5) -> list[dict]  # content LIKE '%query%'
    def get_all_note_contents() -> list[str]      # content のみリスト
```

### 10.7 AgentContext 追加メンバ

```python
# context.py:147
tool_result_store: ToolResultStore  # ツール結果の永続保存 (/tool show <id> で参照)

# context.py:152-159
@property
def services_required -> AppServices  # None チェック付きで services を取得
```

---

## 11. エラーハンドリング

| エラー種別 | 対応 |
|---|---|
| LLM 接続タイムアウト | 指数バックオフで最大 `llm_max_retries` 回リトライ |
| SSE 切断 | `sse_reconnect_max` 回まで再接続（デフォルト 1 回） |
| SSE ハートビートタイムアウト | `llm_stream_retry_on_heartbeat_timeout=true` でリトライ |
| ツールエラー連続 | `tool_error_max_consecutive` 回でループ中断 |
| ツールエラーリトライ | `tool_error_retry_max` 回まで同一ツールをリトライ（デフォルト 1） |
| 設定読み込みエラー | `ConfigLoadError` を送出し起動を中断 |
| MCP サーバー未起動 | watchdog が検知して再起動（`mcp_watchdog_interval > 0` 時） |
| 承認拒否 | ツールの呼び出しをスキップし LLM に拒否結果を返す |

### 11.1 メモリ層例外（memory/exceptions.py）

| 例外クラス | 基底 | 送出条件 |
|---|---|---|
| `MemorySchemaError` | ValueError | メモリ行またはフィールドのスキーマ検証失敗 |
| `UnknownMemoryTypeError` | MemorySchemaError | 未知の `memory_type` 値 |
| `MemoryStorageError` | RuntimeError | DB 書き込み操作の失敗 |
| `JsonlFormatError` | ValueError | JSONL 行の解析またはスキーマ検証失敗 |
| `MemoryConsistencyError` | RuntimeError | `memories` / `memories_fts` / `memories_vec` の件数不整合 |
| `EmbeddingTransportError` | RuntimeError | 埋め込みサービスへの HTTP 通信エラー |
| `EmbeddingProtocolError` | ValueError | 埋め込みサービスのレスポンスがスキーマ違反 |
| `ExtractionError` | RuntimeError | 会話履歴からのメモリ抽出失敗 |
| `InjectionValidationError` | ValueError | 注入入力の検証失敗（空クエリ等） |

---

## 12. 検証計画

| 検証項目 | ツール | 合格基準 |
|---|---|---|
| ユニットテスト | `uv run pytest tests/test_agent_*.py` | 全パス |
| 型チェック | `uv run mypy scripts/` | 新規エラーなし |
| Lint | `uv run ruff check scripts/` | 0 エラー |
| アーキテクチャ境界 | `PYTHONPATH=scripts uv run lint-imports` | 0 違反 |
| 統合テスト | `uv run pytest tests/test_orchestrator.py tests/test_repl.py` | 全パス |
| カバレッジ | `diff-cover coverage.xml` | 変更行 ≥ 90% |

---

## 13. 未解決事項・既知問題

| 項目 | 詳細 |
|---|---|
| RAG augment 未実装 | `spec_agent.md:§6.3, §8` で RAG augment の呼び出しが定義されているが、`orchestrator.py` および `llm_turn_runner.py` での actual 呼び出し実装がない。`RagPipeline.augment()` は存在するがエージェントターンでは呼ばれていない |
| `common.toml` 非統合問題 | `load_all()` が `common.toml` を読み込まないため、`build_db_config()` で空文字列になり `ValueError` が発生する。回避策として `db/helper.py` と `rag/pipeline.py` が個別に `ConfigLoader().load("common.toml")` を呼ぶ設計になっている。将来的な統合を検討中。 |
| `AgentConfig.__getattr__`/`__setattr__` | backward-compat レイヤーが残存。`cfg.llm_url` 等のフラットアクセスを廃止して `cfg.llm.llm_url` に統一する作業が未完了 (`implementations/20260606-194837_config_context_compat.md` 参照) |
| `repl_debug.py`/`context_detection.py`/`rag_debug.py` | 参照元のない廃止スタブファイルが残存。削除対象 (`implementations/20260606-194821_delete_obsolete_files.md` 参照) |
| rag-mcp スタブのポート競合 | `mcp/rag/server.py` (port 8014) と `mcp/git/server.py` (port 8014) がポート 8014 で競合。`rag/server.py` はドキュメントなし |
