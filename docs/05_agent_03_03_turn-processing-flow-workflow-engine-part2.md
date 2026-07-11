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
  - 05_agent_03_03_turn-processing-flow-workflow-engine-part1.md
---

# エージェントターン処理フロー

- ランタイムアーキテクチャ → [05_agent_02_runtime-architecture-part1.md](05_agent_02_runtime-architecture-part1.md)

## ターンごとの状態変化

| Stage | State mutated |
|---|---|
| ① TurnStart | `ctx.turn.current_turn_id` = UUID4 |
| ② メモリ注入 | `ctx.conv.history`の先頭にsystemメッセージが追加される |
| ③ ユーザー追加 | `ctx.conv.history` += ユーザーメッセージ; `ctx.stats.stat_turns += 1` |
| ④ 圧縮 | `ctx.conv.history`の最も古いターンが要約に置換される |
| ⑤ LLM + ツール | `ctx.conv.history` += assistant + toolメッセージ; 統計を更新 |
| ⑥ TurnEnd | `ctx.turn.current_turn_id` = None |

## ターン状態変更リファレンス

| State field | Mutated When | Durable? | Notes |
|---|---|---|---|
| `ctx.conv.history` | 各LLM/toolラウンド (追加) | Yes — メッセージごとにSQLiteへ保存 | HistoryManagerによる圧縮も行われる |
| `ctx.turn.current_turn_id` | TurnStart時 (UUID4) / TurnEnd時 (None) | No — メモリ上のみ | ターン単位の相関に使用 |
| `ctx.turn.pending_approval_id` | ワークフロー承認ゲートの一時停止時 | No — メモリ上のみ; 承認は`workflow.sqlite`に永続化 | 次のターンでNoneにリセット |
| `ctx.stats.stat_turns` | 各ユーザーメッセージ追加後 | No — メモリ上 (`/stats`経由で報告) | セッション再起動時にリセット |
| `ctx.stats.stat_partial_completions` | LLMストリーム中断時 | No — メモリ上; 部分的なコンテンツは`session_diagnostics`に格納 | セッション再起動時にリセット |
| `session.title` | 最初のターン (非同期バックグラウンドタスク) | Yes — SQLite `sessions.title` | ノンブロッキング; LLM失敗時は先頭入力の切り詰めにフォールバック |

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_03_01_turn-processing-flow-overview.md`
- `05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine-part1.md`

## Keywords

partial-completion model
workflowengine integration
state changes per turn
turn-state mutation reference
