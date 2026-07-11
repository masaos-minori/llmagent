---
title: "Agent Runtime Architecture"
category: agent
tags:
  - agent
  - runtime
  - architecture
  - lifecycle
related:
  - 05_agent_00_document-guide.md
---

# Agent Runtime Architecture

- システム概要 → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

主要なランタイムコンポーネント、それらの依存関係、および責務境界を記述し、
エンジニアやAIがどの振る舞いがどこに実装されているかを特定できるようにする。

> **本章の対象範囲:** ランタイムの振る舞い、モジュールグラフ、データフロー、コンポーネントのライフサイクル。
> 関数シグネチャ、パラメータ型、戻り値については → [05_agent_13 §Reference API](05_agent_13_reference-api.md)を参照。

---

## Component Dependency Diagram

```
agent/__main__.py
  └─ AgentREPL (agent/repl.py)          — REPL coordinator; input loop + output only
       ├─ StartupOrchestrator (agent/startup.py) — startup sequence; created once in run()
       ├─ AgentContext (agent/context.py) — per-session DI hub; shared mutable state
       │    ├─ AgentConfig               — hot-reloadable runtime configuration
       │    ├─ AgentSession              — SQLite session/message persistence
       │    ├─ ConversationState         — history list, LLM URL, flags
       │    ├─ TurnState                 — current turn UUID (reset per turn)
       │    ├─ RuntimeStats              — cumulative session metrics
       │    ├─ WorkflowState             — active task ID, approval_pending flag (transient)
       │    └─ AppServices               — all service references (injected by factory.py)
       │         ├─ LLMClient            — SSE streaming, retry
       │         ├─ ToolExecutor         — MCP routing, TTL cache
       │         ├─ HistoryManager       — char counting, LLM compression
       │         ├─ ServerLifecycleRouter — HTTP subprocess lifecycle
       │         ├─ audit_logger         — JSON-lines audit.log writer
       │         └─ MemoryServices?      — optional semantic memory layer
       ├─ CLIView (agent/cli_view.py)    — readline, progress display, multiline input
       ├─ CommandRegistry                — all /cmd dispatch (10 mixins)
       └─ Orchestrator (agent/orchestrator.py) — turn-level facade
            ├─ LLMTurnRunner             — SSE stream + inner tool-call loop
            └─ ToolLoopGuard             — dedup/cycle/retry/error guards
```

---

## Component Responsibilities

### AgentREPL (`agent/repl.py`)

- 入力/ディスパッチループを管理する: 行を読み取る → コマンドまたはLLMターンへ
- 起動シーケンス全体を`StartupOrchestrator`に委譲する
- グレースフルシャットダウンを管理する(SIGTERM → `SystemExit(0)`への変換)
- ビジネスロジックを持たない。UIループ、コマンドディスパッチ、出力表示のみを含む

**起動シーケンス(`StartupOrchestrator.run()`に委譲):**

```
StartupOrchestrator.run()
  Initialization phase:
    → Readline setup
    → build_agent_context(ctx, view)   [factory.py]
    → Command registry initialization
    → Orchestrator initialization
  MCP server startup                 [HTTP subprocess MCP servers]
  Prompt setup
    → system prompt init
    → memory.on_session_start()
→ returns (CommandRegistry, Orchestrator)
REPL loop
```

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

- プラグインツールの検索 → TTLキャッシュチェック → MCPルーティング
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

12個のmixinがあり、それぞれがコマンドグループを1つ担当する。まず組み込みコマンドをディスパッチし、その後プラグインコマンドをディスパッチする。

| Mixin | Commands |
|---|---|
| `SessionMixin` | `/session` |
| `McpMixin` | `/mcp` |
| `ConfigMixin` | `/config`, `/stats`, `/set`, `/reload` |
| `ContextMixin` | `/context`, `/clear`, `/undo`, `/history`, `/system` |
| `DbMixin` | `/db` |
| `ToolingMixin` | `/plan` |
| `DebugMixin` | `/debug` |
| `AuditMixin` | `/audit` |
| `RagExportMixin` | `/rag`, `/export`, `/compact` |
| `MemoryMixin` | `/memory` |
| `WorkflowMixin` | `/approve`, `/reject` |

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

## Keywords

agent
runtime
architecture
lifecycle
