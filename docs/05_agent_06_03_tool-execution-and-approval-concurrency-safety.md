---
title: "Agent Tool Execution and Approval - Concurrency and Safety"
category: agent
tags:
  - agent
  - tool-execution
  - concurrency-limits
  - fail-closed
  - toolloopguard
related:
  - 05_agent_00_document-guide.md
  - 05_agent_06_01_tool-execution-and-approval-execution.md
  - 05_agent_06_02_tool-execution-and-approval-approval.md
  - 05_agent_06_04_tool-execution-and-approval-canonical.md
source:
  - 05_agent_06_tool-execution-and-approval.md
---

# エージェントのツール実行と承認

- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCPルーティング → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)

## 安全制御のまとめ

| Control | Config field | Behavior |
|---|---|---|
| `allowed_tools` | `cfg.tool.allowed_tools` | ホワイトリスト; 空の場合はすべて許可。本番環境では`allowed_tools=[]`は設定エラーとして扱われる (制限なくすべてのツールが許可されるため)。特定のツールに制限する場合は明示的に設定すること。 |
| `allowed_root` | `cfg.approval.allowed_root` | パスジェイル; 空の場合は無効 |
| `approval_github_allowed_repos` | `cfg.approval.*` | GitHub書き込み許可リスト; 空の場合はすべて拒否 (フェイルクローズ) |
| `plan_blocked_tools` | `cfg.tool.plan_blocked_tools` | プランモードでの自動拒否 |
| `approval_protected_paths` | `cfg.approval.*` | パスプレフィックスによる`high`へのエスカレーション |
| `approval_high_risk_branches` | `cfg.approval.*` | ブランチ名による`high`へのエスカレーション |
| `gitops_push_blocked` | `cfg.approval.*` | GitHubへの書き込みをグローバルにすべてブロック |
| `gitops_force_push_blocked` | `cfg.approval.*` | force pushをブロック (デフォルト: `True`) |
| `gitops_protected_branches` | `cfg.approval.*` | 保護対象ブランチ (デフォルト: main, master) |

---

## ToolLoopGuard

`LLMTurnRunner`内の内部ツールループを制御する:

| Guard | Config field | Behavior |
|---|---|---|
| 重複排除 | `tool_dedup_max_repeats` (デフォルト3) | 同一の(name, args)がN回以上繰り返された場合 → ループを終了; ヒントは`session_diagnostics`に格納 |
| 循環検出 | `tool_cycle_detect_window` (デフォルト2) | 直近Nラウンド内で同一のツール呼び出しフィンガープリントが繰り返された場合 → ループを終了; ヒントは`session_diagnostics`に格納 |
| リトライ上限 | `tool_error_retry_max` (デフォルト1) | エラーとなった(name, args)が再度呼び出された場合 → ループを終了; ヒントは`session_diagnostics`に格納 |
| 連続エラー | `tool_error_max_consecutive` (デフォルト3) | ラウンド内の全ツールがN回エラーとなった場合 → ループを終了 |

> **Note:** ガードヒントはオフライン診断専用として格納される。`ctx.conv.history`には**注入されない**。

---

## 並行実行数の制限

`ToolConfig`内の`tool_concurrency_limits: dict[str, int]`は、サーバーキーを最大並行呼び出し数に
マッピングする。ツール実行中に遅延生成される`asyncio.Semaphore`として実装される。

サーバーキーが制限dictに存在する場合、呼び出しは制限される。キーが存在しない場合: 制限なし。
未知のサーバーキーは警告がログに記録されるがエラーにはならない。

---

## フェイルクローズ実行ポリシー

Orchestratorは、ワークフローを作成できない場合に直接 (未承認の) 実行にフォールバックすること
はない。ワークフロー作成が失敗すると`WorkflowCreationError`が発生し、タスクは明確なエラー
メッセージと共に拒否される。

**以前 (削除済み):** ワークフロー計画が利用できない場合、orchestratorはワークフローレベルの
承認チェックをバイパスして、ツール呼び出しを直接実行していた。

**現在:** `WorkflowCreationError`が発生する。ユーザーは根本原因 (計画の欠落、設定の不正) を
修正してから再試行する必要がある。

これはフェイルクローズなポリシーである: 可用性よりも安全性が優先される。
起動時のリカバリモデルについては[Agent Startup and Recovery](05_agent_07_01_cli-and-commands-cli-reference.md#startup-recovery)を参照。

---

## ワークフロー承認のリカバリ (セッションをまたぐ場合)

ワークフローレベルの承認状態は`workflow.sqlite`の`approvals`テーブルに永続化される。
ワークフロータスクが承認待ちで一時停止した場合 (ユーザーは`/approve`または`/reject`を
実行する必要がある)、承認レコードはエージェントの再起動をまたいで存続する:

- **起動時のリカバリ:** 起動時、`approvals`テーブルを検索し、承認待ちのものがあるかを
  確認する。見つかった場合、`ctx.workflow.approval_pending = True`と
  `ctx.turn.pending_approval_id`を設定し、タスクIDと承認IDを含む警告を表示する。

- **再起動後の解決:** `/approve`と`/reject`は、ワークフローデータベースから最新の
  承認待ちを解決する — 解決にはメモリ上の`pending_approval_id`は不要である。
  つまり、メモリ上の状態が失われていても、ユーザーはCLI経由で承認/拒否を行える。

- **警告メッセージにIDを含む:** 起動時の警告は`task=<id> approval=<id> reason=<reason>`を
  表示するため、運用者はログと照合し、どのタスクに対応すべきかを把握できる。

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_06_01_tool-execution-and-approval-execution.md`
- `05_agent_06_02_tool-execution-and-approval-approval.md`
- `05_agent_06_04_tool-execution-and-approval-canonical.md`

## Keywords

safety controls summary
ToolLoopGuard
concurrency limits
fail-closed execution policy
workflow approval recovery
