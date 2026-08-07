---
title: "Agent Tool Execution and Approval - Concurrency and Safety"
category: agent
tags:
  - agent
  - tool-execution
  - concurrency-limits
  - fail-closed
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_06_03_tool-execution-and-approval-concurrency-safety.md
---

# エージェントのツール実行と承認

- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCPルーティング → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)

## Purpose

安全制御の責任分割、ToolLoopGuardの設計判断、フェイルクローズポリシーについて文書化する。

## Design Intent

### 安全制御のまとめ

| Control | Config field | Behavior |
|---|---|---|
| `allowed_tools` | `cfg.tool.allowed_tools` | ホワイトリスト; 空の場合はすべて許可。本番環境では`allowed_tools=[]`は設定エラーとして扱われる |
| `allowed_root` | `cfg.approval.allowed_root` | パスジェイル; 空の場合は無効 |
| `approval_github_allowed_repos` | `cfg.approval.*` | GitHub書き込み許可リスト; 空の場合はすべて拒否 (**フェイルクローズ**) |
| `plan_blocked_tools` | `cfg.tool.plan_blocked_tools` | プランモードでの自動拒否 |
| `approval_protected_paths` | `cfg.approval.*` | パスプレフィックスによる`high`へのエスカレーション |
| `approval_high_risk_branches` | `cfg.approval.*` | ブランチ名による`high`へのエスカレーション |
| `gitops_push_blocked` | `cfg.approval.*` | GitHubへの書き込みをグローバルにすべてブロック |

### ToolLoopGuard の設計判断

`LLMTurnRunner`内の内部ツールループを制御する:

| Guard | Config field | Behavior |
|---|---|---|
| 重複排除 | `tool_dedup_max_repeats` (デフォルト3) | 同一の(name, args)がN回以上繰り返された場合 → ループを終了 |
| 循環検出 | `tool_cycle_detect_window` (デフォルト2) | 直近Nラウンド内で同一のツール呼び出しフィンガープリントが繰り返された場合 → ループを終了 |
| リトライ上限 | `tool_error_retry_max` (デフォルト1) | エラーとなった(name, args)が再度呼び出された場合 → ループを終了 |
| 連続エラー | `tool_error_max_consecutive` (デフォルト3) | ラウンド内の全ツールがN回エラーとなった場合 → ループを終了 |

**Design judgment**: ガードヒントはオフライン診断専用として格納される。`ctx.conv.history`には**注入されない**。

### 並行実行数の制限

`ToolConfig`内の`tool_concurrency_limits: dict[str, int]`は、サーバーキーを最大並行呼び出し数にマッピングする。ツール実行中に遅延生成される`asyncio.Semaphore`として実装される。

- サーバーキーが制限dictに存在する場合、呼び出しは制限される
- キーが存在しない場合: 制限なし
- 未知のサーバーキーは警告がログに記録されるがエラーにはならない

### フェイルクローズ実行ポリシー

Orchestratorは、ワークフローを作成できない場合に直接 (未承認の) 実行に切り替えることはない。ワークフロー作成が失敗すると`WorkflowCreationError`が発生し、タスクは明確なエラーメッセージと共に拒否される。

**Design judgment**: これはフェイルクローズなポリシーである — 可用性よりも安全性が優先される。

### ワークフロー承認のリカバリ

ワークフローレベルの承認状態は`workflow.sqlite`の`approvals`テーブルに永続化される:

- **起動時のリカバリ**: 起動時、`approvals`テーブルを検索し、承認待ちのものがあるかを確認
- **再起動後の解決**: `/approve`と`/reject`は、ワークフローデータベースから最新の承認待ちを解決
- **警告メッセージにIDを含む**: 運用者はログと照合し、どのタスクに対応すべきかを把握できる

## Responsibility Boundary

- **正典**: `shared/tool_executor.py` (ToolExecutor), `agent/tool_loop_guard.py` (ToolLoopGuard)
- **ワークフロー承認DB**: `workflow.sqlite`

## Key Constraints

- フェイルクローズ: `allowed_tools=[]`（本番環境）、`approval_github_allowed_repos=[]`、ワークフロー作成失敗
- フェイルセーフ: `tool_safety_tiers`未定義ツールは`WRITE_DANGEROUS`
- ToolLoopGuardのガードヒントはhistoryに注入されない

## Operational Notes

- 不明

## Known Limitations

- 不明

## Related Docs

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
