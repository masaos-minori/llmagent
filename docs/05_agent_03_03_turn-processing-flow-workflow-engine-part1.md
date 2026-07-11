---
title: "Agent Turn Processing Flow - Workflow Engine Integration (Part 1)"
category: agent
tags:
  - agent
  - turn
  - workflow-engine
  - partial-completion
  - state-changes
related:
  - 05_agent_00_document-guide.md
  - 05_agent_03_01_turn-processing-flow-overview.md
  - 05_agent_03_02_turn-processing-flow-llm-tool-loop.md
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

```
[warn] Partial LLM completion stored. Use /stats to see count or query session_diagnostics table.
```

実装の詳細は上記の「LLMトランスポートエラー (部分完了)」の節を参照。
永続化の挙動 → [05_agent_04 §Message save rules](05_agent_04_01_state-and-persistence-state-model-part1.md)。
運用者による監視 → [05_agent_10 §Interpreting /stats](05_agent_10_01_operations-and-observability-startup-and-health.md)。

---

## WorkflowEngineとの統合

`Orchestrator.handle_turn()`は、`config/workflows/default.json`が存在しworkflow DBが利用可能な場合、
`WorkflowEngine`経由で実行される。ワークフロー状態が主たる実行モデルであり、
会話履歴は従属的な関心事として維持される。

各ターンは`workflow.sqlite`に`task` / `attempt` / `processed_event`レコードを作成する:
- `tasks` — ターンごとに1件; ステータス: `pending → running → [pending_approval →] completed | halted | failed`
- `attempts` — ステージ実行 (plan/execute/verify) ごとに1件、リトライ追跡を含む
- `processed_events` — 冪等性の担保; ステージの重複実行を防止
- `approvals` — 承認ゲートごとに1件; ステータス: `pending → approved | rejected`
- `artifacts` — ステージコールバックが生成するURI

ワークフローステージ (`default.json`で定義):
- `plan` — LLMが初期計画を生成; 必須
- `execute` — LLMが計画を実行; 必須
- `verify` — LLMが実行結果を検証; 必須
- `retry` — `execute`後のオプションのトランスポートエラーリトライゲート; `retryable: false`; `WorkflowEngine`の動作に存在は必須ではない

各ステージは`StageDefinition`を持つ:
- `id` — 一意のステージ識別子 (例: "plan", "execute")
- `description` — 人間が読める説明
- `timeout_sec` — 最大実行時間 (秒)
- `retryable` — 失敗時にステージをリトライ可能かどうか

`WorkflowDef.get_stage(stage_id)` — 指定したidの`StageDefinition`を返す。存在しない場合は`None`。

フォールバック: `config/workflows/default.json`が存在しない、またはworkflow DBが利用不可の場合、
従来の直接実行フローが使用される。

ワークフローパッケージ: `agent/workflow/` (models, workflow_loader, state_store, workflow_engine)。

デフォルトのリトライポリシー (`default.json`に`retry_policy`が定義されていない場合に適用):
- `max_attempts`: 3
- `backoff`: "fixed"
- `backoff_sec`: 1

### ワークフローステータス

`Orchestrator.workflow_status()`は2つのキーを持つdictを返す:
- `mode`: "auto" | "required" | "disabled" — ワークフローポリシーに基づく
- `tracking`: "enabled" | "not_loaded" — ワークフロー定義が設定されていれば"enabled"、そうでなければ"not_loaded"

### 承認ゲート

`WorkflowEngine(require_approval=True)`の場合、エンジンはexecuteステージ完了後、
verifyステージ実行前に一時停止する:

1. エンジンが`store.request_approval(task_id)`を呼び出す → `status=pending`の`ApprovalRecord`
2. タスクステータス → `pending_approval`
3. `WorkflowPendingApprovalError`が発生 → orchestratorが`approval_id`を`ctx.turn.pending_approval_id`に格納; WARNINGをログ出力: `[workflow] Approval required. Use /approve [reason] or /reject [reason].`

ユーザーが`/approve [reason]`または`/reject [reason]`を実行すると、承認レコードがDB内で更新される。
同一タスクでの次回のワークフロー実行時、ゲートは既存の承認レコードをチェックする:

- `status=approved` → verifyステージへ通過
- `status=rejected` → `WorkflowHaltError`が発生; タスクは停止
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

ステージが`retryable: true`の場合、エンジンはリトライポリシーを使用してリトライ挙動を決定する:
- `max_attempts`: 最大試行回数 (デフォルト3)
- `backoff`: リトライ戦略 — "fixed"または"exponential" (両者とも同じ遅延ロジックを使用)
- `backoff_sec`: リトライ間の遅延秒数 (デフォルト1; backoffの種類にかかわらず常にそのまま使用される — "fixed"と"exponential"はいずれも同じ一定の遅延を適用する)

### ワークフローローダーの検証ルール

`config/workflows/*.json`からワークフロー定義を読み込む際:
- 必須のトップレベルキー: `name`, `version`, `stages`, `retry_policy`
- `stages`は空でないリストである必要がある
- ステージIDの重複は不可
- 必須ステージ: `plan`, `execute`, `verify` (すべて存在する必要がある)
- 各ステージは以下を持つ必要がある: `id`, `description`, `timeout_sec`, `retryable`
- `retry_policy.max_attempts`は1以上である必要がある
- `retry_policy.backoff`は"fixed"または"exponential"である必要がある
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

## Keywords

partial-completion model
workflowengine integration
state changes per turn
turn-state mutation reference
