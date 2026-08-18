
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
  - 02_deployment.md
source:
  - 05_agent_03_03_turn-processing-flow-workflow-engine.md


# エージェントターン処理フロー

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## Purpose

部分完了モデルとワークフローエンジン統合について文書化する。ワークフロー必須化の設計判断と、
プロセス境界を越える承認ゲートの仕組みを記述する。

## Design Intent

### ワークフロー実行必須化 (ADR-Workflow-Mandatory)

**Date:** 2026-07-23
**Status:** Accepted

#### コンテキスト

本システムはLLMが計画したタスクを実行する。一部のツールは副作用を持ち、一部の操作は承認を要し、ツール実行は観測可能かつ回復可能でなければならない。LLMからツールへの直接パスは監査と回復を困難にする。

#### 決定

ワークフロー実行は必須である。ワークフロー定義はデプロイ時の必須アーティファクトである。ワークフローのバイパスモードはサポートしない。オプションのワークフローモードはサポートしない。ダイレクト実行へのフォールバックはサポートしない。

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
- 必須のワークフローアーティファクトが欠如・不正な場合、起動は失敗しなければならない
- ワークフロースキーマはサービス起動前に初期化されていなければならない
- オペレーターはワークフロー障害をプラットフォーム障害として扱わなければならない
- 単純なチャットとツールを伴うタスクは同一の実行制御プレーンを共有する

#### 非目標 (Non-Goals)

本決定は以下を扱わない: 個々のワークフローステージの定義、承認ポリシーの再設計、EventBus統合の導入、ランタイム挙動の変更。

### ワークフロー状態のセマンティクス

ワークフロー状態は「開始済み」を意味する（「完了済み」ではない）。ステージの重複実行を防止するために使用される。各ステージの実行中に`processed_events`レコードが作成され、同じステージの再実行が防止される。

### 既存タスクの再開

`existing_task_id`が渡された場合、新規タスクを作成せず既存の`TaskRecord`を取得して再利用する。このとき2つの検証を行う：

- タスクが見つからない場合 → `RuntimeError`
- タスクのステータスが`halted`の場合 → `RuntimeError` — halted状態は終端/一時停止状態であり、ユーザーの明示的な操作なしに自動再開してはならない

いずれの`RuntimeError`も呼び出し元の`except`節では捕捉されず、さらに上位へ伝播する。

### 承認ゲート

**用語の明確化:**
- **事前実行承認**: ツール実行前に発動するツールレベルの承認ゲート（リアルタイムなリスク評価）
- **事後実行承認**: executeステージ完了後に発動するワークフローレベルの承認ゲート（バッチ的な結果確認）
- **自動実行**: 人間の承認を必要としない操作（計画フェーズ、検証フェーズ、低リスクツール呼び出し）

`WorkflowEngine(require_approval=True)`の場合、エンジンはexecuteステージ完了後、verifyステージ実行前に一時停止する：

**現在の実装挙動:** `WorkflowDef.require_approval`のデフォルトは`False`であり、本番デプロイのデフォルト設定では事後実行承認ゲートは発火しない。承認ゲートを有効化するには`config/workflows/default.json`に`"require_approval": true`を明示的に追加する必要がある。(Needs Confirmation / 未決事項)

1. エンジンが`store.request_approval(task_id)`を呼び出す → `status=pending`の`ApprovalRecord`
2. タスクステータス → `pending_approval`
3. `WorkflowPendingApprovalError`が発生 → orchestratorが`approval_id`を格納し、WARNINGをログ出力

ユーザーが`/approve <approval_id> [reason]`または`/reject <approval_id> [reason]`を実行すると、承認レコードがDB内で更新される。同一タスクでの次回のワークフロー実行時、ゲートは既存の承認レコードをチェックする：

- `status=approved` → verifyステージへ通過
- `status=rejected` → `WorkflowHaltError`が発生; タスクは停止
- `status=pending` → `WorkflowPendingApprovalError`が再度発生

既存の承認レコードが見つからない場合、新規レコードが作成されワークフローは一時停止する。

**注意**: 事前実行承認（ツールレベル）と事後実行承認（ワークフローレベル）は独立して発動する。両者は異なる粒度で動作し、競合せず共存する。

## Responsibility Boundary

### 部分完了モデル

部分完了は、全コンテンツを受信する前にLLMレスポンスのストリームが中断された場合に発生する。

| Trigger | 保存先 | 表示方法 | `stat_partial_completions` |
|---|---|---|---|
| `partial_text`が空でない状態での`LLMTransportError` | `session_diagnostics`テーブル | `/stats` | +1 |
| `partial_text`が空の状態での`LLMTransportError` (ストリーム開始前) | 格納されない (ユーザーメッセージは履歴からポップされる) | ユーザーに見えるエラーメッセージ | 変化なし |

**重要な不変条件:** 部分的なコンテンツは決して`ctx.conv.history`に追加されない。診断チャンネルに隔離されることで、以降のLLMコンテキストを汚染しない。

### ワークフロー実行必須化

`Orchestrator.handle_turn()`は常に`WorkflowEngine`経由で実行される。ワークフロー定義は起動時に無条件にロードされ、存在しない・不正な場合は起動前に`RuntimeError`で中断する。ワークフロー状態が主たる実行モデルであり、会話履歴は従属的な関心事として維持される。

### ワークフローステータス

`Orchestrator.workflow_status()`は2つのキーを持つdictを返す：

- `mode`: "required" — ワークフローは常に必須
- `tracking`: "enabled" — ワークフロー定義は起動時に必ずロードされる

### ワークフローステージ

| ステージ | 責任 | 必須 |
|---|---|---|
| plan | 実行前のアイデンポテンシー/ブックキーピングのみ; LLM呼び出しなし | はい |
| execute | メモリ注入、モード分類、LLM呼び出し、ツール実行ループ | はい |
| verify | LLMが実行結果を検証 | はい |

### リトライメカニズム

`plan`/`execute`/`verify`はすべて同一のリトライループ関数を経由する。`retryable`が`false`のステージ（デフォルトでは`plan`と`verify`）は単発実行され、失敗時に即座に例外を送出する。`retryable: true`のステージ（デフォルトでは`execute`のみ）はリトライポリシーを使用してリトライ挙動を決定する：

- `max_attempts`: 最大試行回数（デフォルト3）
- バックオフ戦略は"fixed"のみ実装
- `backoff_sec`: リトライ間の遅延秒数（デフォルト1）

### ワークフローローダーの検証ルール

`config/workflows/*.json`からワークフロー定義を読み込む際：

- 必須のトップレベルキー: `name`, `version`, `stages`, `retry_policy`
- `stages`は空でないリストである必要がある
- ステージIDの重複は不可
- 必須ステージ: `plan`, `execute`, `verify`
- 各ステージは以下を持つ必要がある: `id`, `timeout_sec`, `retryable`
- `retry_policy.max_attempts`は1以上である必要がある
- `retry_policy.backoff_sec`は0以上である必要がある

See also: [02_deployment.md](02_deployment.md) for deploy-time validation of these same rules,
and the [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook)
for recovery steps when a rule is violated.

## Key Constraints

### 起動時復旧

`Orchestrator.__init__()`で`StateStore.recover_stale_attempts()`を呼び出す。これはプロセス起動時に実行中の試行を検索し、それらを`failed`としてマークする。

### 承認ゲートのデフォルト動作

本番デプロイのデフォルト設定では承認ゲートは発火しない。承認ゲートを有効化するには構成変更が必要。

## Operational Notes

- ハルト状態は`/reject`または明示的な停止操作によって到達する終端状態であり、自動再開は行われない
- 既存の承認レコードが見つからない場合、新規レコードが作成されワークフローは一時停止する

## Known Limitations

- 承認ゲートのデフォルトは非有効であり、明示的な構成変更が必要
- リトライバックオフ戦略は"fixed"のみ実装されている

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_03_01_turn-processing-flow-overview.md`
- `05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine.md`
- `02_deployment.md`
- `01_overview-arch-02-pipelines.md`

## Keywords

partial-completion model
workflowengine integration
state changes per turn
turn-state mutation reference
ADR-Workflow-Mandatory
workflow execution mandatory

# エージェントターン処理フロー

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## Purpose

部分完了モデルとワークフローエンジン統合について文書化する。ワークフロー必須化の設計判断と、
プロセス境界を越える承認ゲートの仕組みを記述する。

## Design Intent

### ワークフロー実行必須化 (ADR-Workflow-Mandatory)

**Date:** 2026-07-23
**Status:** Accepted

#### コンテキスト

本システムはLLMが計画したタスクを実行する。一部のツールは副作用を持ち、一部の操作は承認を要し、ツール実行は観測可能かつ回復可能でなければならない。LLMからツールへの直接パスは監査と回復を困難にする。

#### 決定

ワークフロー実行は必須である。ワークフロー定義はデプロイ時の必須アーティファクトである。ワークフローのバイパスモードはサポートしない。オプションのワークフローモードはサポートしない。ダイレクト実行へのフォールバックはサポートしない。

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
- 必須のワークフローアーティファクトが欠如・不正な場合、起動は失敗しなければならない
- ワークフロースキーマはサービス起動前に初期化されていなければならない
- オペレーターはワークフロー障害をプラットフォーム障害として扱わなければならない
- 単純なチャットとツールを伴うタスクは同一の実行制御プレーンを共有する

#### 非目標 (Non-Goals)

本決定は以下を扱わない: 個々のワークフローステージの定義、承認ポリシーの再設計、EventBus統合の導入、ランタイム挙動の変更。

### ワークフロー状態のセマンティクス

ワークフロー状態は「開始済み」を意味する（「完了済み」ではない）。ステージの重複実行を防止するために使用される。各ステージの実行中に`processed_events`レコードが作成され、同じステージの再実行が防止される。

### 既存タスクの再開

`existing_task_id`が渡された場合、新規タスクを作成せず既存の`TaskRecord`を取得して再利用する。このとき2つの検証を行う：

- タスクが見つからない場合 → `RuntimeError`
- タスクのステータスが`halted`の場合 → `RuntimeError` — halted状態は終端/一時停止状態であり、ユーザーの明示的な操作なしに自動再開してはならない

いずれの`RuntimeError`も呼び出し元の`except`節では捕捉されず、さらに上位へ伝播する。

### 承認ゲート

**用語の明確化:**
- **事前実行承認**: ツール実行前に発動するツールレベルの承認ゲート（リアルタイムなリスク評価）
- **事後実行承認**: executeステージ完了後に発動するワークフローレベルの承認ゲート（バッチ的な結果確認）
- **自動実行**: 人間の承認を必要としない操作（計画フェーズ、検証フェーズ、低リスクツール呼び出し）

`WorkflowEngine(require_approval=True)`の場合、エンジンはexecuteステージ完了後、verifyステージ実行前に一時停止する：

**現在の実装挙動:** `WorkflowDef.require_approval`のデフォルトは`False`であり、本番デプロイのデフォルト設定では事後実行承認ゲートは発火しない。承認ゲートを有効化するには`config/workflows/default.json`に`"require_approval": true`を明示的に追加する必要がある。(Needs Confirmation / 未決事項)

1. エンジンが`store.request_approval(task_id)`を呼び出す → `status=pending`の`ApprovalRecord`
2. タスクステータス → `pending_approval`
3. `WorkflowPendingApprovalError`が発生 → orchestratorが`approval_id`を格納し、WARNINGをログ出力

ユーザーが`/approve <approval_id> [reason]`または`/reject <approval_id> [reason]`を実行すると、承認レコードがDB内で更新される。同一タスクでの次回のワークフロー実行時、ゲートは既存の承認レコードをチェックする：

- `status=approved` → verifyステージへ通過
- `status=rejected` → `WorkflowHaltError`が発生; タスクは停止
- `status=pending` → `WorkflowPendingApprovalError`が再度発生

既存の承認レコードが見つからない場合、新規レコードが作成されワークフローは一時停止する。

**注意**: 事前実行承認（ツールレベル）と事後実行承認（ワークフローレベル）は独立して発動する。両者は異なる粒度で動作し、競合せず共存する。

## Responsibility Boundary

### 部分完了モデル

部分完了は、全コンテンツを受信する前にLLMレスポンスのストリームが中断された場合に発生する。

| Trigger | 保存先 | 表示方法 | `stat_partial_completions` |
|---|---|---|---|
| `partial_text`が空でない状態での`LLMTransportError` | `session_diagnostics`テーブル | `/stats` | +1 |
| `partial_text`が空の状態での`LLMTransportError` (ストリーム開始前) | 格納されない (ユーザーメッセージは履歴からポップされる) | ユーザーに見えるエラーメッセージ | 変化なし |

**重要な不変条件:** 部分的なコンテンツは決して`ctx.conv.history`に追加されない。診断チャンネルに隔離されることで、以降のLLMコンテキストを汚染しない。

### ワークフロー実行必須化

`Orchestrator.handle_turn()`は常に`WorkflowEngine`経由で実行される。ワークフロー定義は起動時に無条件にロードされ、存在しない・不正な場合は起動前に`RuntimeError`で中断する。ワークフロー状態が主たる実行モデルであり、会話履歴は従属的な関心事として維持される。

### ワークフローステータス

`Orchestrator.workflow_status()`は2つのキーを持つdictを返す：

- `mode`: "required" — ワークフローは常に必須
- `tracking`: "enabled" — ワークフロー定義は起動時に必ずロードされる

### ワークフローステージ

| ステージ | 責任 | 必須 |
|---|---|---|
| plan | 実行前のアイデンポテンシー/ブックキーピングのみ; LLM呼び出しなし | はい |
| execute | メモリ注入、モード分類、LLM呼び出し、ツール実行ループ | はい |
| verify | LLMが実行結果を検証 | はい |

### リトライメカニズム

`plan`/`execute`/`verify`はすべて同一のリトライループ関数を経由する。`retryable`が`false`のステージ（デフォルトでは`plan`と`verify`）は単発実行され、失敗時に即座に例外を送出する。`retryable: true`のステージ（デフォルトでは`execute`のみ）はリトライポリシーを使用してリトライ挙動を決定する：

- `max_attempts`: 最大試行回数（デフォルト3）
- バックオフ戦略は"fixed"のみ実装
- `backoff_sec`: リトライ間の遅延秒数（デフォルト1）

### ワークフローローダーの検証ルール

`config/workflows/*.json`からワークフロー定義を読み込む際：

- 必須のトップレベルキー: `name`, `version`, `stages`, `retry_policy`
- `stages`は空でないリストである必要がある
- ステージIDの重複は不可
- 必須ステージ: `plan`, `execute`, `verify`
- 各ステージは以下を持つ必要がある: `id`, `timeout_sec`, `retryable`
- `retry_policy.max_attempts`は1以上である必要がある
- `retry_policy.backoff_sec`は0以上である必要がある

See also: [02_deployment.md](02_deployment.md) for deploy-time validation of these same rules,
and the [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook)
for recovery steps when a rule is violated.

## Key Constraints

### 起動時復旧

`Orchestrator.__init__()`で`StateStore.recover_stale_attempts()`を呼び出す。これはプロセス起動時に実行中の試行を検索し、それらを`failed`としてマークする。

### 承認ゲートのデフォルト動作

本番デプロイのデフォルト設定では承認ゲートは発火しない。承認ゲートを有効化するには構成変更が必要。

## Operational Notes

- ハルト状態は`/reject`または明示的な停止操作によって到達する終端状態であり、自動再開は行われない
- 既存の承認レコードが見つからない場合、新規レコードが作成されワークフローは一時停止する

## Known Limitations

- 承認ゲートのデフォルトは非有効であり、明示的な構成変更が必要
- リトライバックオフ戦略は"fixed"のみ実装されている

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_03_01_turn-processing-flow-overview.md`
- `05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine.md`
- `02_deployment.md`
- `01_overview-arch-02-pipelines.md`

## Keywords

partial-completion model
workflowengine integration
state changes per turn
turn-state mutation reference
ADR-Workflow-Mandatory
workflow execution mandatory



# エージェントターン処理フロー

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## Purpose

ターンごとの状態変化について文書化する。各フェーズでの状態変更と、その永続性について記述する。

## Responsibility Boundary

### ターンごとの状態変化

| フェーズ | 変更される状態 |
|---|---|
| TurnStart | `ctx.turn.current_turn_id` = UUID4 |
| メモリ注入 | `ctx.conv.history`の先頭にsystemメッセージが追加される |
| ユーザー追加 | `ctx.conv.history` += ユーザーメッセージ; `ctx.stats.stat_turns += 1` |
| 圧縮 | `ctx.conv.history`の最も古いターンが要約に置換される |
| LLM + ツール | `ctx.conv.history` += assistant + toolメッセージ; 統計を更新 |
| TurnEnd | `ctx.turn.current_turn_id` = None |

### ターン状態変更リファレンス

| 状態フィールド | 変更タイミング | 永続性 | 備考 |
|---|---|---|---|
| `ctx.conv.history` | 各LLM/toolラウンド (追加) | はい — メッセージごとにSQLiteへ保存 | HistoryManagerによる圧縮も行われる |
| `ctx.turn.current_turn_id` | TurnStart時 (UUID4) / TurnEnd時 (None) | いいえ — メモリ上のみ | ターン単位の相関に使用 |
| `ctx.turn.pending_approval_id` | ワークフロー承認ゲートの一時停止時 | いいえ — メモリ上のみ; 承認は`workflow.sqlite`に永続化 | 次のターンでNoneにリセット |
| `ctx.stats.stat_turns` | 各ユーザーメッセージ追加後 | いいえ — メモリ上 (`/stats`経由で報告) | セッション再起動時にリセット |
| `ctx.stats.stat_partial_completions` | LLMストリーム中断時 | いいえ — メモリ上; 部分的なコンテンツは`session_diagnostics`に格納 | セッション再起動時にリセット |
| `session.title` | 最初のターン (非同期バックグラウンドタスク) | はい — SQLite `sessions.title` | ノンブロッキング; LLM失敗時は先頭入力の切り詰めにフォールバック |

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_03_01_turn-processing-flow-overview.md`
- `05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine.md`

## Keywords

partial-completion model
workflowengine integration
state changes per turn
turn-state mutation reference

# エージェントターン処理フロー

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## Purpose

ターンごとの状態変化について文書化する。各フェーズでの状態変更と、その永続性について記述する。

## Responsibility Boundary

### ターンごとの状態変化

| フェーズ | 変更される状態 |
|---|---|
| TurnStart | `ctx.turn.current_turn_id` = UUID4 |
| メモリ注入 | `ctx.conv.history`の先頭にsystemメッセージが追加される |
| ユーザー追加 | `ctx.conv.history` += ユーザーメッセージ; `ctx.stats.stat_turns += 1` |
| 圧縮 | `ctx.conv.history`の最も古いターンが要約に置換される |
| LLM + ツール | `ctx.conv.history` += assistant + toolメッセージ; 統計を更新 |
| TurnEnd | `ctx.turn.current_turn_id` = None |

### ターン状態変更リファレンス

| 状態フィールド | 変更タイミング | 永続性 | 備考 |
|---|---|---|---|
| `ctx.conv.history` | 各LLM/toolラウンド (追加) | はい — メッセージごとにSQLiteへ保存 | HistoryManagerによる圧縮も行われる |
| `ctx.turn.current_turn_id` | TurnStart時 (UUID4) / TurnEnd時 (None) | いいえ — メモリ上のみ | ターン単位の相関に使用 |
| `ctx.turn.pending_approval_id` | ワークフロー承認ゲートの一時停止時 | いいえ — メモリ上のみ; 承認は`workflow.sqlite`に永続化 | 次のターンでNoneにリセット |
| `ctx.stats.stat_turns` | 各ユーザーメッセージ追加後 | いいえ — メモリ上 (`/stats`経由で報告) | セッション再起動時にリセット |
| `ctx.stats.stat_partial_completions` | LLMストリーム中断時 | いいえ — メモリ上; 部分的なコンテンツは`session_diagnostics`に格納 | セッション再起動時にリセット |
| `session.title` | 最初のターン (非同期バックグラウンドタスク) | はい — SQLite `sessions.title` | ノンブロッキング; LLM失敗時は先頭入力の切り詰めにフォールバック |

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_03_01_turn-processing-flow-overview.md`
- `05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine.md`

## Keywords

partial-completion model
workflowengine integration
state changes per turn
turn-state mutation reference

