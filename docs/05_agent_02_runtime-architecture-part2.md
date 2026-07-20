---
title: "Agent Runtime Architecture (Part 2)"
category: agent
tags:
  - agent
  - runtime
  - architecture
  - lifecycle
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_02_runtime-architecture-part1.md
---

# Agent Runtime Architecture

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Component Responsibilities

### AgentREPL (`agent/repl.py`)

- 入力/ディスパッチループを管理する: 行を読み取る → コマンドまたはLLMターンへ
- 起動シーケンス全体を`StartupOrchestrator`に委譲する
- グレースフルシャットダウンを管理する
- ビジネスロジックを持たない。UIループ、コマンドディスパッチ、出力表示のみを含む

**起動シーケンス(`StartupOrchestrator.run()`に委譲):**

``` text
StartupOrchestrator.run()
  Initialization phase:
    → Readline setup
    → build_agent_context(ctx, view)   [factory.py]
    → Command registry initialization
    → Workflow definition / schema preflight checks
    → Orchestrator initialization
  MCP server startup [HTTP subprocess MCP servers; startup_mode=SUBPROCESS かつ transport=HTTPのみ]
  Service checks [security audit, embedding dim整合, readiness,
                  tool定義検証, routing drift(static/live), RAG consistency]
  Pending approval recovery [StateStoreから前回セッションの承認待ちを復元]
  Prompt setup
    → system prompt init
    → memory.on_session_start()
→ returns (CommandRegistry, Orchestrator)
REPL loop
```

### シャットダウン

- `AgentREPL.run()`は`SIGTERM`ハンドラを登録し、受信すると`ctx.conv.shutdown_requested = True`を
  設定して`asyncio.Event`をセットする。これによりREPLループが次の入力待ち/ターン完了後に終了する
  (`SystemExit(0)`への直接変換ではなく、フラグベースのグレースフルシャットダウン)。進行中のターンには
  最大10秒(`_GRACEFUL_TIMEOUT`)の猶予があり、超過するとタイムアウトしてループを抜ける。(Explicit in code)
- リソースクローズはWALチェックポイント実行後、`ctx.services.lifecycle.shutdown_all()`と
  `http.aclose()`を呼ぶ。`HttpServerLifecycleManager.shutdown_all()`は実行中に届いた2回目の
  SIGINTを一時的に吸収し、クリーンアップの完了を保証する。(Explicit in code)

### StartupOrchestrator検証パイプライン

サービスチェックは`StartupValidationResult`に各チェックの結果(OK/WARNING/FATAL/SKIPPED)を
蓄積し、FATALが1件でもあれば`RuntimeError`で起動を中断する。MCPサブプロセス起動後に例外が
発生した場合、起動済みのMCPサブプロセスは`shutdown_all()`でロールバックされる。
(Explicit in code)

### StartupOrchestrator (`agent/startup.py`)

- `AgentREPL`から抽出された起動オーケストレーション処理をすべて内包する
- `(ctx, view)`で構築される。`run()`は`(CommandRegistry, Orchestrator)`を返す
- 起動時の複雑さを分離し、`AgentREPL`がUI関心事のみを持つようにする

### Orchestrator (`agent/orchestrator.py`)

- 1回のユーザーターンをエンドツーエンドで処理する
- メモリ注入 → ユーザーメッセージ追加 → 履歴圧縮 → LLMターンの流れを管理する
- LLMストリーミングとツールループを`LLMTurnRunner`に委譲する
- 監査ログイベント(`turn_start`、`turn_end`)を発行する

| Method | Responsibility |
|---|---|
| `handle_turn(line)` | 最上位のターンハンドラー |

`handle_turn()`は上記の流れを`WorkflowEngine`のplan/execute/verifyステージに
乗せて実行する(`plan_fn`は現状no-op、`execute_fn`がLLMターン本体、`verify_fn`がturn_end処理)。
`ctx.workflow.approval_pending`がTrueの間は新規ターンを拒否する。(Explicit in code — 詳細は
`05_agent_03`系の管轄)

### AgentContext (`agent/context.py`)

共有される可変状態とコンポーネント参照のハブである。`factory.build_agent_context()`が
すべてのサービスを注入する。サブ構造は以下の通り:

| Sub-structure | Scope | Key contents |
|---|---|---|
| `ctx.conv` | セッション | `history: list[LLMMessage]`, `plan_mode`, `debug_mode`, `system_prompt_content` |
| `ctx.turn` | ターンごと | `current_turn_id: str\|None` (UUID4、ターン間ではNone) |
| `ctx.stats` | 累積 | `stat_turns`、`stat_tool_calls`、`stat_latency`、トークン数 |
| `ctx.workflow` | セッション | `WorkflowState`: `active`、`current_task_id`、`workflow_id`、`approval_pending` (一時的) |
| `ctx.cfg` | ホットリロード | `AgentConfig` (7つのサブ設定) |
| `ctx.session` | セッション | `AgentSession` (SQLite) |
| `ctx.services` | 注入される | すべてのサービスインスタンス (LLMClient、ToolExecutorなど) |
### LLMClient (`shared/llm_client.py`)

- リクエストペイロードを構築する(messages + tool_defs + temperature + max_tokens)
- `RobustSSEParser`によるSSEストリーミング(インクリメンタルUTF-8、ハートビート追跡)
- リトライ可能なエラー発生時に再接続する(`sse_reconnect_max`まで)
- `LLMTransportError`による部分的な補完の検出と報告

### ToolExecutor (`shared/tool_executor.py`)

- TTLキャッシュチェック → MCPルーティング
- 副作用検出: write/delete/shell_runが含まれる場合、並列ツール呼び出しを直列化する
- `ToolRouteResolver`: ツール名 → サーバーキーを解決する(ライブの`/v1/tools`ディスカバリー → ToolRegistry)
- `McpServerHealthRegistry`: サーバーごとのヘルス状態(HEALTHY/DEGRADED/UNAVAILABLE)を追跡する

### HistoryManager (`agent/history.py`)

- 会話履歴のサイズ(文字数またはトークン数)をカウントする
- 閾値を超えるとLLMベースの要約をトリガーする
- `HistorySelectionPolicy`: 圧縮対象のターンを選択する(重要度スコアリング + カテゴリ)
- 直近の`history_protect_turns`ターンペアは圧縮対象から保護する
- `compress_turns`プロパティ: 圧縮対象として選択された最も古いターンペアの数

### CommandRegistry (`agent/commands/registry.py`)

実装上は14個のmixinを継承する(`_`始まりの内部命名だが、クラス構成として一覧化する)。
組み込みコマンド(`_COMMANDS`、`agent/commands/command_defs_list.py`が正本)をディスパッチする。(Explicit in code — 旧版の「12個」は実態と不一致)

| Mixin | Commands |
|---|---|
| `_SessionMixin` | `/session` |
| `_McpMixin` | `/mcp` |
| `_ConfigMixin` | `/config`, `/stats`, `/set`, `/reload` |
| `_ContextMixin` | `/context`, `/clear`, `/undo`, `/history`, `/system` |

| `_ToolingMixin` | `/plan` |
| `_DebugMixin` | `/debug` |
| `_AuditMixin` | `/audit` |
| `_RagExportMixin` | `/rag`, `/export`, `/compact` |
| `_MemoryMixin` | `/memory` |
| `_WorkflowMixin` | `/approve`, `/reject` |
| `_MdqMixin` | `/mdq` |
| `_SkillMixin` | `/skill` |

### CLIView (`agent/cli_view.py`)

- 表示層のみを担当し、ビジネスロジックを持たない
- テスト容易性のために`Writer`と`Reader`のプロトコルを提供する
- `Orchestrator`、`HistoryManager`、`LLMClient`にコールバックを注入する

### LifecycleState (`agent/lifecycle.py`)

ライフサイクルマネージャー間で共有されるトランスポート状態のenum:

| Value | Description |
|---|---|
| `STARTING` | サーバー起動中 |
| `RUNNING` | サーバーは稼働中 |
| `STOPPED` | サーバーは停止済み |
| `FAILED` | サーバーでエラーが発生 |
| `UNKNOWN` | 初期/不明な状態 |

有効な遷移: `STOPPED → STARTING/FAILED`、`STARTING → RUNNING/FAILED/STOPPED`、`RUNNING → STOPPED/FAILED/STARTING`、`FAILED → STARTING/STOPPED`、`UNKNOWN → any`。

`assert_valid_transition(from_state, to_state)`は、遷移が不正な場合に`ValueError`を発生させる。

### Lifecycle実装の所在

`LifecycleManagerProtocol`(`agent/lifecycle_protocol.py`)が`ensure_ready`/`shutdown_all`/`restart`/
`shutdown_idle`/`get_transport_state`/`start_http_subprocess`/`get_process_snapshot`を定義する
構造的サブタイピング用プロトコルである。本番実装は`agent/factory.py`内にあり、HTTPサブプロセスの
起動・ヘルスポーリング・再起動・終了は`agent/http_lifecycle.py`の`HttpServerLifecycleManager`に
委譲される(実装クラス名はアンダースコア始まりの内部命名のため本書では割愛)。
`ensure_ready`/`start_http_subprocess`/`restart`は、シャットダウン開始後(`shutdown_all()`呼び出し後)は
すべて無視されるガードを持つ。(Explicit in code)

### AgentSession (`agent/session.py`)

- `sessions`、`messages`テーブルのCRUD
- RAGドキュメントの削除/一覧取得(`/db`コマンドから委譲される)
- `fetch_messages(session_id)`はセッション復元用に`list[LLMMessage]`を返す

### Memory Services (`agent/memory/`)

`use_memory_layer=True`で有効化されるオプションのサブシステムである。
`ctx.services.memory`経由でアクセスする。

| Sub-service | Role |
|---|---|
| `injection` | セッション開始時および各ターンで関連するメモリを注入する |
| `ingestion` | セッション終了時にメモリを抽出・永続化する |
| `store` | メモリエントリ用のJSONL + SQLiteストア |
| `retriever` | FTS5とオプションのKNN検索 |

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_02_runtime-architecture-part1.md`

## Keywords

agent
runtime
architecture
lifecycle
