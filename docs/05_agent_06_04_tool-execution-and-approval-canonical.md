---
title: "Agent Tool Execution and Approval - Canonical Approval Model"
category: agent
tags:
  - agent
  - tool-execution
  - adr-001
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_06_04_tool-execution-and-approval-canonical.md
---

# エージェントのツール実行と承認

- ターンフロー → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- MCPルーティング → [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md)

## Purpose

正準承認モデル（ADR-001）と部分完了の永続化について文書化する。

## Design Intent

### 正準承認モデル（ADR-001）

**Date:** 2026-06-26
**Status:** Accepted

#### コンテキスト

エージェントには2つの承認レイヤーが存在する: ツールレベルとワークフローレベル。これらは競合せず共存する必要がある。

#### 決定

両レイヤーとも正準 (canonical) である; 境界と責務は排他的ではなく明示的なものとする。

#### 境界表

| Axis | Tool-level Approval | Workflow-level Approval |
|------|---------------------|------------------------|
| Implementation | `agent/tool_approval.py` | `agent/workflow/workflow_engine.py` |
| Granularity | ツール呼び出しごと | タスクごと (execute→verify間) |
| State | 一時的 (メモリ上) | DB永続化 (`approvals`) |
| Resolution | 標準入力による対話 | `/approve` / `/reject` |
| Currently active | 常に有効 | 無効 (デフォルトのワークフロー定義では `require_approval=false`) |

**Design judgment**: 「単一の正準な承認オブジェクト」という要件は、各レイヤーの境界と責務を明確に定義することを意味する。いずれかのレイヤーを排除することを意味するものではない。両レイヤーは異なる問題を解決する:

- ツールレベル: ツールごとのリアルタイムなリスクゲート (実行前)
- ワークフローレベル: executeステージ全体の結果に対する人間による承認 (実行後)

#### 共存ルール

`require_approval=True`の場合:

1. executeステージ中: `run_approval_checks`がツール呼び出しごとに発動する (MEDIUM/HIGHリスクのツールのみ)
2. executeステージ後: 承認ゲートがワークフローを一時停止する; ユーザーが`/approve`または`/reject`を実行
3. 両者は独立して発動する。これは意図的なものであり、両者は異なる粒度で動作する。

### 部分完了の永続化

一部のステップが完了した後にワークフローが失敗した場合、ワークフローエンジンは`StateStore.update_task_status()`経由で最終的なタスクステータスを記録する:

- `"failed"` — ワークフローステップが未処理の例外を発生させた
- `"halted"` — `WorkflowHaltError`によりワークフローが明示的に停止された

**Design judgment**: 完了したステップは個別には永続化されない。部分完了は自動的には再開**されない** — ユーザーはリクエストを再発行するか、`/reject`を使って承認待ちのゲートを却下する必要がある。

## Responsibility Boundary

- **正典**: `agent/tool_approval.py` (ツールレベル), `agent/workflow/workflow_engine.py` (ワークフローレベル)
- **ワークフロー承認DB**: `workflow.sqlite`

## Key Constraints

- 両承認レイヤーは正準であり排他的でない
- ワークフローレベルの承認ゲートはデフォルトで発火しない
- 部分完了は自動再開されない

## Operational Notes

- 不明

## Known Limitations

- 不明

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_06_01_tool-execution-and-approval-execution.md`
- `05_agent_06_02_tool-execution-and-approval-approval.md`
- `05_agent_06_03_tool-execution-and-approval-concurrency-safety.md`

## Keywords

canonical approval model
ADR-001
partial completion persistence
