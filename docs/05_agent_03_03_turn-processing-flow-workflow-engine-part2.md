---
title: "Agent Turn Processing Flow - Workflow Engine Integration (Part 2)"
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
  - 05_agent_03_03_turn-processing-flow-workflow-engine-part2.md
---

# エージェントターン処理フロー

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture-part1.md](05_agent_02_runtime-architecture-part1.md)

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
- `05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`

## Keywords

partial-completion model
workflowengine integration
state changes per turn
turn-state mutation reference
