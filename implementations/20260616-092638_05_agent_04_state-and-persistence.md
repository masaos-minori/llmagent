# 04 State and Persistence — Agent Documentation Restructuring

## Goal
会話状態・ターン状態・履歴圧縮・セッション永続化の仕組みを1章にまとめる。

## Scope
- ConversationState / TurnState のライフサイクル
- HistoryManager による履歴管理と圧縮
- AgentSession によるセッション永続化

## Assumptions
- 05_ref-agent-context.md が状態クラスの正典
- 05_ref-agent-history.md が履歴管理の正典
- 05_ref-agent-session.md がセッション永続化の正典
## Implementation

### Target file
`docs/05_agent/04_state-and-persistence.md`
### Procedure
- 05_ref-agent-context.md §3 (ConversationState) からフィールドとライフサイクルを抽出
- 05_ref-agent-context.md §4 (TurnState) からターンスコープのフィールドを抽出
- 05_ref-agent-history.md 全体から HistoryManager API と CompressResult を抽出
- 05_ref-agent-session.md 全体から AgentSession の永続化API と notes を抽出
### Method
- H2: 状態クラス概要 / ConversationState / TurnState / 履歴管理 / セッション永続化
- 状態クラスのフィールドは「フィールド名: 型 — 説明」の箇条書き
- 履歴圧縮のトリガー条件と CompressResult の構造を明示

### Details
- ConversationState: messages リスト, tool_results キャッシュ, metadata
- TurnState: 現在ターンのツール呼び出しリスト, 入出力トークン数
- HistoryManager: add_message(), compress(), get_messages() の3主要メソッド
- CompressResult: compressed_messages, removed_count, compression_ratio
- AgentSession: save(), load(), list_sessions() — SQLiteベースの永続化
- セッション復元フロー: セッションID指定 → load() → ConversationState再構築

## Validation plan
- ConversationState / TurnState の全フィールドが05_ref-agent-context.mdと一致していること
- CompressResultの全フィールドが05_ref-agent-history.mdと一致していること
- AgentSessionのsave/loadフローが05_ref-agent-session.mdのnotesと矛盾しないこと
