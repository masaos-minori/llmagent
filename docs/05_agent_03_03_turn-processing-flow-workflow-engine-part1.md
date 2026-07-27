---
title: "Agent Turn Processing Flow - Workflow Engine Integration (Part 1)"
category: agent
tags:
  - agent
  - turn
  - workflow-engine
  - partial-completion
  - state-changes
  - adr-workflow-mandatory
related:
  - 05_agent_00_document-guide.md
  - 05_agent_03_01_turn-processing-flow-overview.md
  - 05_agent_03_02_turn-processing-flow-llm-tool-loop.md
  - 02_deployment-part2.md
source:
  - 05_agent_03_03_turn-processing-flow-workflow-engine-part1.md
---

# エージェントターン処理フロー

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture-part1.md](05_agent_02_runtime-architecture-part1.md)

## 部分完了モデル

部分完了は、全コンテンツを受信する前にLLMレスポンスのストリームが中断された場合に発生する。

| Trigger | Stored where | Visible via | `stat_partial_completions` |
|---|---|---|---|
| `partial_text`が空でない状態での`LLMTransportError` | `session_diagnostics`テーブル | `/stats` | +1 |
| `partial_text`が空の状態での`LLMTransportError` (ストリーム開始前) | 格納されない (ユーザーメッセージは履歴からポップされる) | ユーザーに見えるエラーメッセージ | 変化なし |

**重要な不変条件:** 部分的なコンテンツは決して`ctx.conv.history`に追加されない。診断チャンネルに隔離されることで、以降のLLMコンテキストを汚染しない。

各ターンの後、REPLの行ディスパッチャーが`stat_partial_completions`が増加したかをチェックする。増加していれば:

``` text
[warn] Partial LLM completion stored. Use /stats to see count or query session_diagnostics table.
```

実装の詳細は上記の「LLMトランスポートエラー (部分完了)」の節を参照。
永続化の挙動 → [05_agent_04 §Message save rules](05_agent_04_01_state-and-persistence-state-model-part1.md)。
運用者による監視 → [05_agent_10 §Interpreting /stats](05_agent_10_01_operations-and-observability-startup-and-health.md)。

---

## WorkflowEngineとの統合

`Orchestrator.handle_turn()`は、常に`WorkflowEngine`経由で実行される。ワークフロー定義(`config/workflows/default.json`)は起動時に無条件にロードされ、存在しない・不正な場合は起動前に`RuntimeError`で中断する。ワークフロー状態が主たる実行モデルであり、
会話履歴は従属的な関心事として維持される。

各ターンは`workflow.sqlite`に`task` / `attempt` / `processed_event`レコードを作成する:
- `tasks` — ターンごとに1件; ステータス: `pending → running → [pending_approval →] completed | halted | failed`
- `attempts` — ステージ実行 (plan/execute/verify) ごとに1件、リトライ追跡を含む
- `processed_events` — 冪等性の担保; ステージの重複実行を防止
- `approvals` — 承認ゲートごとに1件; ステータス: `pending → approved | rejected`
- `artifacts` — ステージコールバックが生成するURI

ワークフローステージ (`default.json`で定義):
- `plan` — 実行前のアイデンポテンシー/ブックキーピングのみ; LLM呼び出しなし; 必須
- `execute` — メモリ注入、モード分類、LLM呼び出し、ツール実行ループ; 必須
- `verify` — LLMが実行結果を検証; 必須

各ステージは`StageDefinition`を持つ:
- `id` — 一意のステージ識別子 (例: "plan", "execute")
- `timeout_sec` — 最大実行時間 (秒)
- `retryable` — 失敗時にステージをリトライ可能かどうか。リトライループ関数が`stage_def.retryable`を見て、`plan`/`execute`/`verify`すべてに対しリトライループを適用するか単発実行にするかを一様に決定する (`description`フィールドは2026-07-17に削除 — どのコードパスからも読まれていなかった)

`WorkflowDef.get_stage(stage_id)` — 指定したidの`StageDefinition`を返す。存在しない場合は`None`。

### 既存タスクの再開 (`_init_workflow_task()`)

`Orchestrator._init_workflow_task()`は、`existing_task_id`(`ctx.turn.pending_approval_task_id`
経由; `/approve`実行後にのみ設定され、使用後は即座に`None`に戻る)が渡された場合、新規タスクを
作成せず`get_task_by_id()`で既存の`TaskRecord`を取得して再利用する。このとき2つの検証を行う:
- タスクが見つからない場合 → `RuntimeError(f"Task {existing_task_id} not found")`
- タスクのステータスが`halted`の場合 → `RuntimeError(f"Task {existing_task_id} is halted and
  cannot be automatically resumed")` — halted状態は`/reject`または明示的な停止操作によって
  到達する終端/一時停止状態であり、ユーザーの明示的な操作なしに自動再開してはならないため

いずれの`RuntimeError`も呼び出し元 (`_handle_workflow_engine()`) の`except`節では捕捉されず
(捕捉対象は`WorkflowPendingApprovalError`と`WorkflowHaltError`のみ)、さらに上位へ伝播する。

ワークフローパッケージ: `agent/workflow/` (models, workflow_loader, state_store, workflow_engine)。

デフォルトのリトライポリシー (`default.json`に`retry_policy`が定義されていない場合に適用):
- `max_attempts`: 3
- `backoff_sec`: 1

(`backoff`フィールドは2026-07-17に削除 — "fixed"以外の戦略が実装されたことがなく実質的に定数だった)

### ワークフローステータス

`Orchestrator.workflow_status()`は2つのキーを持つdictを返す:
- `mode`: "required" — ワークフローは常に必須
- `tracking`: "enabled" — ワークフロー定義は起動時に必ずロードされる

### ワークフロー実行必須化 (ADR-Workflow-Mandatory)

**Date:** 2026-07-23
**Status:** Accepted

#### コンテキスト

本システムはLLMが計画したタスクを実行する。一部のツールは副作用を持ち、一部の操作は承認を要し、ツール実行は観測可能かつ回復可能でなければならない。LLMからツールへの直接パスは監査と回復を困難にする。

#### 決定

ワークフロー実行は必須である。ワークフロー定義はデプロイ時の必須アーティファクトである。ワークフローのバイパスモードはサポートしない。オプションのワークフローモードはサポートしない。ダイレクト実行へのフォールバックはサポートしない。(実装上の対応: 上記「WorkflowEngineとの統合」の起動時無条件ロード、および`workflow_mode`が設定キーとして存在しないこと — [01_overview-arch-02-pipelines.md](01_overview-arch-02-pipelines.md)参照)

#### 根拠

- 全ての副作用を伴う操作は追跡可能でなければならない
- 承認状態はプロセス境界を越えて存続しなければならない
- リトライおよび冪等性の挙動は一元管理されなければならない
- 部分的なタスク完了は検査可能でなければならない
- 回復には永続化されたタスク・試行状態が必要である
- ツール実行はLLMの会話状態のみに依存すべきではない

#### 検討した代替案

| 代替案 | 却下理由 |
|---|---|
| ワークフローを介さないダイレクトツール実行 | 監査と回復が困難になる。承認・リトライロジックの永続状態がない |
| オプションのワークフローモード | ワークフロー有効/無効間で挙動に一貫性がなくなる。オペレーターが実行パターンを予測できない |
| ローカルモードでのワークフロー無効化 | ローカルモードでも監査証跡と承認追跡は必要。環境ごとに異なるルールは混乱を招く |
| ワークフロー定義欠如時のフォールバック実行 | サイレントな機能低下は設定エラーを隠蔽する。起動失敗の方が即座にフィードバックを提供できる |
| ワークフロー状態を伴わないツールごとのアドホック承認 | 承認状態がプロセス再起動を越えて存続しない。どの承認がどの試行に適用されたか追跡できない |

#### 影響

- デプロイにはワークフロー定義ファイルを含める必要がある
- 必須のワークフローアーティファクトが欠如・不正な場合、起動は失敗しなければならない (デプロイ時チェックリスト・失敗モード → [02_deployment-part2.md §3.2](02_deployment-part2.md#32-デプロイメントチェックリスト) / [§3.3](02_deployment-part2.md#33-失敗モード))
- ワークフロースキーマはサービス起動前に初期化されていなければならない (スキーマ責務 → [02_deployment-part2.md §3.1](02_deployment-part2.md#31-スキーマ適用))
- オペレーターはワークフロー障害をプラットフォーム障害として扱わなければならない
- 単純なチャットとツールを伴うタスクは同一の実行制御プレーンを共有する

#### 非目標 (Non-Goals)

本決定は以下を扱わない: 個々のワークフローステージの定義、承認ポリシーの再設計、EventBus統合の導入、ランタイム挙動の変更。

### 承認ゲート

`WorkflowEngine(require_approval=True)`の場合、エンジンはexecuteステージ完了後、
verifyステージ実行前に一時停止する:

**現在の実装挙動:** `WorkflowDef.require_approval`のデフォルトは`False`であり、`config/workflows/default.json`にも明示指定がないため、本番デプロイのデフォルト設定では承認ゲートは発火しない。承認ゲートを有効化するには`config/workflows/default.json`に`"require_approval": true`を明示的に追加する必要がある。(Explicit in code / `issues/20260711_00_issue.md`で追跡中の未決事項)

1. エンジンが`store.request_approval(task_id)`を呼び出す → `status=pending`の`ApprovalRecord`
2. タスクステータス → `pending_approval`
3. `WorkflowPendingApprovalError`が発生 → orchestratorが`approval_id`を`ctx.turn.pending_approval_id`に格納; WARNINGをログ出力: `[workflow] Approval required. Use /approve <approval_id> [reason] or /reject <approval_id> [reason].`

ユーザーが`/approve <approval_id> [reason]`または`/reject <approval_id> [reason]`を実行すると、承認レコードがDB内で更新される。
同一タスクでの次回のワークフロー実行時、ゲートは既存の承認レコードをチェックする:

- `status=approved` → verifyステージへ通過
- `status=rejected` → `WorkflowHaltError`が発生; タスクは停止（`/reject` コマンドは拒否操作の直後にタスクを即座に halted 状態にする。このチェックは、その halt が別経路で適用される前にエンジンが再評価した場合に備えた防御的フォールバック）
- `status=pending` → `WorkflowPendingApprovalError`が再度発生 (ユーザーがまだ応答していない)

既存の承認レコードが見つからない場合、新規レコードが作成されワークフローは一時停止する。

### ワークフロー例外

| Exception | When Raised |
|---|---|
| `WorkflowTimeoutError` | ステージ実行が`timeout_sec`を超過した場合 |
| `WorkflowHaltError` | タスクが停止された場合 (例: `/halt`経由、または拒否後) |
| `WorkflowPendingApprovalError` | 承認ゲートが処理継続前にユーザーの操作を要求する場合 |
| `WorkflowLoadError` | ワークフロー定義の検証または読み込みが失敗した場合 |

### リトライメカニズム

`plan`/`execute`/`verify`はすべて同一のリトライループ関数を経由する。`stage_def.retryable`が
`false`のステージ (`config/workflows/default.json`では`plan`と`verify`) は単発実行され、失敗時に
即座に例外を送出する。`retryable: true`のステージ (デフォルトでは`execute`のみ) はリトライポリシーを
使用してリトライ挙動を決定する:
- `max_attempts`: 最大試行回数 (デフォルト3)
- バックオフ戦略は"fixed"のみ実装 (`backoff`フィールドは2026-07-17に削除)
- `backoff_sec`: リトライ間の遅延秒数 (デフォルト1; この値がそのまま適用される)

### ワークフローローダーの検証ルール

`config/workflows/*.json`からワークフロー定義を読み込む際:
- 必須のトップレベルキー: `name`, `version`, `stages`, `retry_policy`
- `stages`は空でないリストである必要がある
- ステージIDの重複は不可
- 必須ステージ: `plan`, `execute`, `verify` (すべて存在する必要がある)
- 各ステージは以下を持つ必要がある: `id`, `timeout_sec`, `retryable`
- `retry_policy.max_attempts`は1以上である必要がある
- `retry_policy.backoff_sec`は0以上である必要がある

See also: [02_deployment-part1.md](02_deployment-part1.md) for deploy-time validation of these same rules,
and the [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md#workflow-deployment-runbook)
for recovery steps when a rule is violated.

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_03_01_turn-processing-flow-overview.md`
- `05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine-part2.md`
- `02_deployment-part2.md`
- `01_overview-arch-02-pipelines.md`

## Keywords

partial-completion model
workflowengine integration
state changes per turn
turn-state mutation reference
ADR-Workflow-Mandatory
workflow execution mandatory
