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

## Purpose

ランタイムの拡張ポイント、ライフサイクルフェーズ、シャットダウンポリシーを記述し、
コンポーネントの動作期間と相互依存関係を明確にする。

## Design Intent

AgentREPLはUIループ、コマンドディスパッチ、出力表示のみを担当し、ビジネスロジックを持たない。
すべての起動シーケンスを`StartupOrchestrator`に委譲することで、REPLが純粋な入力/出力層として機能する。

`StartupOrchestrator`をAgentREPLから分離した理由: 起動時の複雑さ（サービスチェック、MCPサーバー起動、承認待ち復旧）を
REPLの責任範囲から切り離し、REPLがUI関心事のみ持つようにするため。

## Responsibility Boundary

### コンポーネントの責務

#### AgentREPL (`agent/repl.py`)

- 入力/ディスパッチループを管理する: 行を読み取る → コマンドまたはLLMターンへ
- グレースフルシャットダウンを管理する
- ビジネスロジックを持たない。UIループ、コマンドディスパッチ、出力表示のみを含む

#### StartupOrchestrator (`agent/startup.py`)

- `AgentREPL`から抽出された起動オーケストレーション処理をすべて内包する
- `(ctx, view)`で構築される。`run()`は`(CommandRegistry, Orchestrator)`を返す
- 起動時の複雑さを分離し、`AgentREPL`がUI関心事のみを持つようにする

#### Orchestrator (`agent/orchestrator.py`)

- 1回のユーザーターンをエンドツーエンドで処理する
- メモリ注入 → ユーザーメッセージ追加 → 履歴圧縮 → LLMターンの流れを管理する
- LLMストリーミングとツールループを`LLMTurnRunner`に委譲する
- 監査ログイベント(`turn_start`、`turn_end`)を発行する

#### AgentContext (`agent/context.py`)

共有される可変状態とコンポーネント参照のハブである。`factory.build_agent_context()`が
すべてのサービスを注入する。

| Sub-structure | Scope | Key contents |
|---|---|---|
| `ctx.conv` | セッション | `history`, `plan_mode`, `debug_mode`, `system_prompt_content` |
| `ctx.turn` | ターンごと | `current_turn_id` (UUID4、ターン間ではNone) |
| `ctx.stats` | 累積 | `stat_turns`、`stat_tool_calls`、`stat_latency`、トークン数 |
| `ctx.workflow` | セッション | `WorkflowState`: `active`、`current_task_id`、`workflow_id`、`approval_pending` (一時的) |
| `ctx.cfg` | ホットリロード | `AgentConfig` (7つのサブ設定) |
| `ctx.session` | セッション | `AgentSession` (SQLite) |
| `ctx.services` | 注入される | すべてのサービスインスタンス (LLMClient、ToolExecutorなど) |

#### LLMClient (`shared/llm_client.py`)

- リクエストペイロードを構築する(messages + tool_defs + temperature + max_tokens)
- SSEストリーミング(インクリメンタルUTF-8、ハートビート追跡)
- リトライ可能なエラー発生時に再接続する
- 部分的な補完の検出と報告

#### ToolExecutor (`shared/tool_executor.py`)

- TTLキャッシュチェック → MCPルーティング
- 副作用検出: write/delete/shell_runが含まれる場合、並列ツール呼び出しを直列化する
- ツール名 → サーバーキーを解決する
- サーバーごとのヘルス状態を追跡する

#### HistoryManager (`agent/history.py`)

- 会話履歴のサイズ(文字数またはトークン数)をカウントする
- 閾値を超えるとLLMベースの要約をトリガーする
- 圧縮対象のターンを選択する(重要度スコアリング + カテゴリ)
- 直近の`history_protect_turns`ターンペアは圧縮対象から保護する

#### CommandRegistry (`agent/commands/registry.py`)

組み込みコマンドをディスパッチする。

#### CLIView (`agent/cli_view.py`)

- 表示層のみを担当し、ビジネスロジックを持たない
- テスト容易性のために`Writer`と`Reader`のプロトコルを提供する
- `Orchestrator`、`HistoryManager`、`LLMClient`にコールバックを注入する

#### LifecycleState (`agent/lifecycle.py`)

ライフサイクルマネージャー間で共有されるトランスポート状態のenum:

| Value | Description |
|---|---|
| `STARTING` | サーバー起動中 |
| `RUNNING` | サーバーは稼働中 |
| `STOPPED` | サーバーは停止済み |
| `FAILED` | サーバーでエラーが発生 |
| `UNKNOWN` | 初期/不明な状態 |

有効な遷移: `STOPPED → STARTING/FAILED`、`STARTING → RUNNING/FAILED/STOPPED`、`RUNNING → STOPPED/FAILED/STARTING`、`FAILED → STARTING/STOPPED`、`UNKNOWN → any`。

#### AgentSession (`agent/session.py`)

- `sessions`、`messages`テーブルのCRUD
- RAGドキュメントの削除/一覧取得(`/db`コマンドから委譲される)
- セッション復元用にメッセージリストを返す

#### Memory Services (`agent/memory/`)

`use_memory_layer=True`で有効化されるオプションのサブシステムである。
`ctx.services.memory`経由でアクセスする。

| Sub-service | Role |
|---|---|
| `injection` | セッション開始時および各ターンで関連するメモリを注入する |
| `ingestion` | セッション終了時にメモリを抽出・永続化する |
| `store` | メモリエントリ用のJSONL + SQLiteストア |
| `retriever` | FTS5とオプションのKNN検索 |

## Key Constraints

### シャットダウン

グレースフルシャットダウンはフラグベースの制御で行う。`SIGTERM`受信時に`shutdown_requested`フラグを立て、
次のターン完了後にループを終了する。進行中のターンには最大10秒の猶予があり、超過するとタイムアウトする。

このアプローチを選んだ理由: システムExitへの直接変換ではなく、進行中のワークフローの整合性を保つため。
ハンドラはブロッキングせず、ターン完了後のチェックに終了処理を委ねる。

リソースクローズはWALチェックポイント実行後に行い、両方の呼び出しは独立して保護される。
一方が失敗しても他方をブロックしない。

### 起動検証パイプライン

サービスチェックは`StartupValidationResult`に結果を蓄積し、FATALが1件でもあれば起動を中断する。
MCPサブプロセス起動後に例外が発生した場合、起動済みのMCPサブプロセスはロールバックされる。

### ライフサイクル実装の所在

`LifecycleManagerProtocol`が`ensure_ready`/`shutdown_all`/`restart`/
`shutdown_idle`/`get_transport_state`/`start_http_subprocess`/`get_process_snapshot`を定義する
構造的サブタイピング用プロトコルである。本番実装は`agent/factory.py`内にあり、HTTPサブプロセスの
起動・ヘルスポーリング・再起動・終了は`agent/http_lifecycle.py`に
委譲される。
`ensure_ready`/`start_http_subprocess`/`restart`は、シャットダウン開始後は
すべて無視されるガードを持つ。

## Operational Notes

- バックグラウンドタスクの失敗閾値到達時通知と一時停止機構はオプトイン（既定無効）。
- `handle_turn()`はワークフローエンジン経由でplan/execute/verifyステージを実行する。
  `ctx.workflow.approval_pending`がTrueの間、およびバックグラウンドタスクが一時停止中の間は
  新規ターンを拒否する。（詳細は[05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)参照）

## Known Limitations

- バックグラウンドタスクの失敗閾値到達時通知と一時停止機構はオプトイン（既定無効）。（詳細は
  [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)参照）

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_02_runtime-architecture-part1.md`

## Keywords

agent
runtime
architecture
lifecycle
