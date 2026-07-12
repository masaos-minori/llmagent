---
title: "Agent Tool Execution and Approval - Canonical Approval Model"
category: agent
tags:
  - agent
  - tool-execution
  - adr-001
  - canonical-approval-model
  - partial-completion
related:
  - 05_agent_00_document-guide.md
  - 05_agent_06_01_tool-execution-and-approval-execution.md
  - 05_agent_06_02_tool-execution-and-approval-approval.md
  - 05_agent_06_03_tool-execution-and-approval-concurrency-safety.md
---

# エージェントのツール実行と承認

- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCPルーティング → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)

## 正準承認モデル (ADR-001)

**Date:** 2026-06-26
**Status:** Accepted

### コンテキスト

エージェントには2つの承認レイヤーが存在する: ツールレベルとワークフローレベル。これらは競合せず共存する必要がある。

### 決定

両レイヤーとも正準 (canonical) である; 境界と責務は排他的ではなく明示的なものとする。

### 境界表

| Axis | Tool-level Approval | Workflow-level Approval |
|------|---------------------|------------------------|
| Implementation | `agent/tool_approval.py` | `agent/workflow/workflow_engine.py` |
| Granularity | ツール呼び出しごと | タスクごと (execute→verify間) |
| State | 一時的 (メモリ上) | DB永続化 (`approvals`) |
| Resolution | 標準入力による対話 | `/approve` / `/reject` |
| Currently active | 常に有効 | 無効 (`require_approval=False`) |

  ワークフローレベルの承認ゲートはワークフロー定義ファイル（`config/workflows/*.json`）の
`require_approval` フィールド（デフォルト`false`）によって制御される。有効にするにはワークフロー定義で
`"require_approval": true`を設定する。フィールドリファレンスについては
[Workflow Definition Schema](05_agent_08_01_configuration-loading-agent-config-part1.md#workflow-definition-schema)を参照。

### 共存ルール

`require_approval=True`の場合:

1. executeステージ中: `run_approval_checks`がツール呼び出しごとに発動する (MEDIUM/HIGHリスクのツールのみ)。
2. executeステージ後: 承認ゲートがワークフローを一時停止する; ユーザーが`/approve`または`/reject`を実行する。
3. 両者は独立して発動する。これは意図的なものであり、両者は異なる粒度で動作する。

### アーキテクチャ図

```
User prompt
  └─► Orchestrator
        └─► WorkflowEngine (plan → execute → [approval gate] → verify)
              └─► repository_gateway.py (tool-call batch)
                    └─► run_approval_checks (per-tool, MEDIUM/HIGH risk)
                          └─► stdin prompt → approved/denied
              └─► Approval gate [when require_approval=True]
                    └─► WorkflowPendingApprovalError
                          └─► /approve or /reject command
```

### ADRの根拠

「単一の正準な承認オブジェクト」という要件は、各レイヤーの境界と責務を明確に定義することを意味する。いずれかのレイヤーを排除することを意味するものではない。両レイヤーは異なる問題を解決する:

- ツールレベル: ツールごとのリアルタイムなリスクゲート (実行前)。
- ワークフローレベル: executeステージ全体の結果に対する人間による承認 (実行後)。

---

## 部分完了の永続化

一部のステップが完了した後にワークフローが失敗した場合、ワークフローエンジンは
`StateStore.update_task_status()`経由で最終的なタスクステータスを記録する:

- `"failed"` — ワークフローステップが未処理の例外を発生させた
- `"halted"` — `WorkflowHaltError`によりワークフローが明示的に停止された

完了したステップは個別には永続化されない (ワークフローエンジンは個々のステップの進捗を
DBで追跡しない)。失敗前にどのステップが成功したかを判断するには、ユーザーは監査ログを
確認する必要がある。

部分完了は自動的には再開**されない** — ユーザーはリクエストを再発行するか、
`/reject`を使って承認待ちのゲートを却下する必要がある。

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_06_01_tool-execution-and-approval-execution.md`
- `05_agent_06_02_tool-execution-and-approval-approval.md`
- `05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`

## Keywords

canonical approval model
ADR-001
boundary table
architecture diagram
partial completion persistence
